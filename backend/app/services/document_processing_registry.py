"""In-memory registry bridging REST document uploads to WebSocket observers.

Module-level state is safe because asyncio is single-threaded — no locks needed.
"""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# WebSocket listeners keyed by project_id
_listeners: dict[str, list[WebSocket]] = {}


def register_listener(project_id: str, ws: WebSocket) -> None:
    """Add a WebSocket as a listener for document events in a project."""
    _listeners.setdefault(project_id, []).append(ws)
    logger.debug("Registered document listener for project %s", project_id)


def unregister_listener(project_id: str, ws: WebSocket) -> None:
    """Remove a WebSocket listener for a project."""
    if project_id in _listeners:
        try:
            _listeners[project_id].remove(ws)
        except ValueError:
            pass
        if not _listeners[project_id]:
            del _listeners[project_id]
    logger.debug("Unregistered document listener for project %s", project_id)


async def notify_listeners(project_id: str, message: dict) -> None:
    """Send a JSON message to all WebSocket listeners for a project."""
    listeners = _listeners.get(project_id, [])
    stale: list[WebSocket] = []
    for ws in listeners:
        try:
            await ws.send_json(message)
        except Exception:
            logger.debug("Removing stale listener for project %s", project_id)
            stale.append(ws)
    for ws in stale:
        unregister_listener(project_id, ws)
