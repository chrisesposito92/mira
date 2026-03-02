"""Research node — searches the web for company info and analyzes results."""

import asyncio
import json
import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm_factory import get_llm
from app.agents.prompts.use_case_gen import RESEARCH_PROMPT
from app.agents.state import UseCaseGenState
from app.config import settings

logger = logging.getLogger(__name__)


def _ensure_tavily_key() -> None:
    """Set TAVILY_API_KEY env var from settings if not already set."""
    if not os.environ.get("TAVILY_API_KEY"):
        key = settings.tavily_api_key
        if key:
            os.environ["TAVILY_API_KEY"] = key


async def _search_single(tool: object, query: str) -> list[str]:
    """Run a single Tavily search and return formatted results."""
    results_list: list[str] = []
    try:
        results = await tool.ainvoke({"query": query})
        if isinstance(results, str):
            results_list.append(results)
        elif isinstance(results, list):
            for r in results:
                if isinstance(r, dict):
                    content = r.get("content", "")
                    url = r.get("url", "")
                    if content:
                        results_list.append(f"[{url}] {content}")
                elif isinstance(r, str):
                    results_list.append(r)
    except Exception:
        logger.exception("Tavily search failed for query: %s", query)
    return results_list


async def _run_tavily_searches(customer_name: str) -> str:
    """Run multiple Tavily searches in parallel and compile results."""
    from langchain_tavily import TavilySearch

    _ensure_tavily_key()

    tool = TavilySearch(max_results=5)
    queries = [
        f"{customer_name} company products services",
        f"{customer_name} pricing billing model",
        f"{customer_name} API usage",
    ]

    results = await asyncio.gather(*[_search_single(tool, q) for q in queries])
    all_results = [item for sublist in results for item in sublist]
    return "\n\n---\n\n".join(all_results) if all_results else ""


async def research_customer(state: UseCaseGenState) -> dict:
    """Research a company via web search and analyze results with an LLM.

    Uses Tavily to search for company information, then passes the results
    through an LLM to produce a structured research summary.
    """
    customer_name = state["customer_name"]
    model_id = state["model_id"]
    notes = state.get("notes", "")
    attachment_text = state.get("attachment_text", "")

    # Run web searches
    try:
        raw_results = await _run_tavily_searches(customer_name)
    except Exception:
        logger.exception("All Tavily searches failed for: %s", customer_name)
        raw_results = ""

    if not raw_results:
        fallback = (
            f"Web search returned no results for '{customer_name}'. "
            "Proceeding with user-provided notes and attachment text only."
        )
        return {
            "research_results": fallback,
            "needs_clarification": False,
            "current_step": "research_complete",
        }

    # Analyze with LLM
    prompt = RESEARCH_PROMPT.format(
        customer_name=customer_name,
        search_results=raw_results,
        notes=notes or "None provided",
        attachment_text=attachment_text or "None provided",
    )

    llm = get_llm(model_id, temperature=0.2)
    response = await llm.ainvoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(
                content=f"Analyze the search results for {customer_name} "
                "and produce a research summary."
            ),
        ]
    )

    content = response.content if isinstance(response.content, str) else str(response.content)

    # Parse structured response
    try:
        parsed = json.loads(content)
        research_summary = parsed.get("research_summary", content)
        needs_clarification = parsed.get("needs_clarification", False)
    except (json.JSONDecodeError, TypeError):
        research_summary = content
        needs_clarification = False

    return {
        "research_results": research_summary,
        "needs_clarification": needs_clarification,
        "current_step": "research_complete",
    }
