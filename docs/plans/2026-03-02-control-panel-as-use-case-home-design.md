# Control Panel as Use Case Home

**Date:** 2026-03-02
**Status:** Approved

## Problem

After completing WF1 (Products, Meters & Aggregations), the UI returns to the "Start Workflow" screen with no way to review results. The Control Panel link is broken (missing useCaseId in URL). The workflow page is the primary use case view, but it should be the Control Panel — workflows are a tool to produce objects, not the home base.

## Design

### Route Structure

- **Remove** `/use-cases/[useCaseId]/workflow/` route entirely
- **Control Panel** at `/use-cases/[useCaseId]/control-panel/` becomes the sole use case page
- `UseCaseCard` links to `/projects/{projectId}/use-cases/{useCaseId}/control-panel`
- "Back" button navigates to the project page

### Toolbar: "Run Workflow" Button

The control panel toolbar gets a "Run Workflow" button (right side). Clicking opens a compact popover with:
- Workflow type selector (4 types, gated by prerequisites)
- Model picker dropdown
- "Start" button

### Workflow Side Panel (Drawer)

A sliding drawer from the right (~400-450px wide) containing:
- `WorkflowHeader` (step indicator, connection state, model name)
- `ChatContainer` (messages, entity cards, clarification cards)
- Close button (X)

Behavior:
- Opens when a workflow starts or when restoring an interrupted workflow
- Auto-closes ~3 seconds after workflow completion (manual close always available)
- Can be closed at any time; workflow continues in background via WebSocket

### Live Object Updates

When workflow sends approval results (entities saved to DB), the control panel refetches its objects list. Triggered on per-step approval completions and workflow "complete" message.

### Data Loading

The control panel `+page.ts` load function adds:
- Workflows list (for prerequisite gating in launcher)
- Models list (for launcher dropdown)
- Interrupted workflow + messages (for restore on page load)

## Files Affected

### Delete
- `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/workflow/+page.svelte`
- `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/workflow/+page.ts`

### Modify
- `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/+page.svelte` — add workflow side panel, toolbar button, live updates
- `frontend/src/routes/(app)/projects/[projectId]/use-cases/[useCaseId]/control-panel/+page.ts` — add workflow/model data loading
- `frontend/src/lib/components/project/UseCaseCard.svelte` — change link target from `/workflow` to `/control-panel`

### Create
- `frontend/src/lib/components/control-panel/WorkflowDrawer.svelte` — side panel component wrapping WorkflowHeader + ChatContainer
- `frontend/src/lib/components/control-panel/WorkflowLauncherPopover.svelte` — compact popover with workflow type + model picker
