# Phase 2: Rendering Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 02-rendering-engine
**Areas discussed:** Layout algorithm, Connection line rendering, Category group cards, Custom node creation
**Mode:** --analyze (trade-off tables provided for each decision)

---

## Layout Algorithm

### Q1: How should the auto-layout position nodes?

| Option | Description | Selected |
|--------|-------------|----------|
| Zone-based | Fixed zones: prospect top-center, categories in left/right/bottom arcs, individual systems fill remaining positions | ✓ |
| Radial | Pure circle arrangement, prospect at 12 o'clock, everything else evenly spaced | |
| Hybrid | Prospect fixed at top, categories in zones, ungrouped systems radial-fill the gaps | |

**User's choice:** Zone-based
**Notes:** Matches m3ter reference diagrams. Deterministic positioning.

### Q2: How should the layout handle varying system counts?

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed canvas, reflow | Single canvas size, nodes adjust position/size as count grows | ✓ |
| Tiered breakpoints | 2-3 preset sizes based on node count | |
| Elastic canvas | Grows dynamically, needs zoom/pan | |

**User's choice:** Fixed canvas, reflow
**Notes:** Simplest for v1, predictable export dimensions.

### Q3: How should categories be assigned to zones?

| Option | Description | Selected |
|--------|-------------|----------|
| Automatic by category order | display_order from component library drives clockwise zone fill | ✓ |
| Smart placement by size | Largest categories get the most space | |
| User-assignable zones | Explicit zone selection per category | |

**User's choice:** Automatic by category order
**Notes:** Deterministic, no extra UI needed.

---

## Connection Line Rendering

### Q4: How should connection lines render between nodes?

| Option | Description | Selected |
|--------|-------------|----------|
| Straight dashed lines | Direct point-to-point, matching m3ter reference style | ✓ |
| Curved Bezier | Arced paths that avoid the center hub | |
| Orthogonal | Right-angle routed paths | |

**User's choice:** Straight dashed lines
**Notes:** Matches m3ter brand reference.

### Q5: How should data flow pill labels position along connection lines?

| Option | Description | Selected |
|--------|-------------|----------|
| Midpoint | Centered on the line, simple and predictable | ✓ |
| Offset midpoint | Centered but nudged away from nearby lines | |
| Source-biased | Closer to the source node to indicate flow direction | |

**User's choice:** Midpoint
**Notes:** Overlap rare with zone-based layout.

### Q6: How should connection endpoints convey direction?

| Option | Description | Selected |
|--------|-------------|----------|
| Dot at source, arrowhead at target | Bidirectional gets arrowheads both ends | ✓ |
| Dots both ends, arrow on pill | Direction shown in the label area only | |
| Arrowhead only | No dots, just arrows at target | |

**User's choice:** Dot at source, arrowhead at target
**Notes:** Clear directionality, matches reference "dashed lines with dot endpoints."

---

## Category Group Cards

### Q7: How should systems inside a category group card be arranged?

| Option | Description | Selected |
|--------|-------------|----------|
| Logo grid | Small logo squares in rows, names below each | ✓ |
| Vertical list | Stacked rows with logo + full name | |
| Compact pills | Minimal pills with tiny logo + short name | |

**User's choice:** Logo grid
**Notes:** Compact, visually rich, matches reference.

### Q8: How should category group cards be visually labeled?

| Option | Description | Selected |
|--------|-------------|----------|
| Text-only header | Category name in bold/muted text at top of the white card | ✓ |
| Colored top bar | Thin accent-colored bar per category | |
| Icon + text header | Category-specific icon alongside the name | |

**User's choice:** Text-only header
**Notes:** Avoids competing color systems with connection type colors.

### Q9: How should ungrouped or single-system nodes render?

| Option | Description | Selected |
|--------|-------------|----------|
| Individual cards | Standalone white card with logo + name, no category wrapper | ✓ |
| Hybrid | Auto-collapse single-system categories to individual cards | |
| Force into groups | Everything gets a category container | |

**User's choice:** Individual cards
**Notes:** Custom nodes and lone systems look natural as standalone cards.

---

## Custom Node Creation

### Q10: Where does custom node creation live in Phase 2?

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal dialog | Simple modal with name + domain fields, accessible from "+" button | ✓ |
| Render-only | Phase 2 just renders; defer creation UI to Phase 3 | |
| Sidebar form panel | More featured creation panel | |

**User's choice:** Minimal dialog
**Notes:** Meets COMP-02 success criteria without building the full configurator.

### Q11: How should logo resolution work from the user's perspective?

| Option | Description | Selected |
|--------|-------------|----------|
| Live preview on blur | Show logo preview when domain field loses focus, before adding | ✓ |
| Fetch on submit | Logo appears only after the node is added | |
| Fetch on submit + edit after | Add first, allow re-editing the node | |

**User's choice:** Live preview on blur
**Notes:** Prevents trial-and-error adding/deleting.

---

## Claude's Discretion

- Exact canvas dimensions and SVG coordinate system
- Font choice (Inter as default)
- Spacing constants, card dimensions, border radius, shadow styling
- Dashed line stroke-dasharray pattern
- Logo grid column count per card width
- Monogram SVG rendering
- DiagramStore reactive state extension
- SVG marker definitions
- Pill label sizing and padding

## Deferred Ideas

None — discussion stayed within phase scope.
