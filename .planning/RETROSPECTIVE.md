# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-25
**Phases:** 4 | **Plans:** 16 | **Requirements:** 31/31

### What Was Built
- Full diagram builder: component library (29 systems), configurator UI, live SVG preview, PNG/SVG export
- Pure SVG rendering engine with hub-and-spoke layout, m3ter branding, color-coded connections
- Auto-save with debounce, version-based staleness protection, thumbnail generation
- DOM-based export pipeline with Inter variable font injection, 2x HiDPI, SSRF-protected logo proxy
- 91+ tests across all phases with Nyquist validation coverage

### What Worked
- **Phase sequencing was right**: DB first, renderer second, UI third, export last. Each phase built on a stable foundation. Export pitfalls (canvas taint, font inlining) were mitigated in Phase 2, not retrofitted.
- **TDD for stores and layout math**: Caught regressions early, especially for SVG coordinate calculations and DiagramStore state management.
- **Pure SVG with inline styles**: Avoided the foreignObject/dynamic Tailwind trap entirely. Export "just worked" because rendering was clean from the start.
- **Logo proxy in Phase 1**: Establishing the CORS/canvas taint solution early prevented a class of silent export failures.
- **Plan-per-day velocity**: Most plans completed in 2-5 minutes. The entire milestone shipped in 2 days.

### What Was Inefficient
- **Phase 03 P04 (auto-save) took 146min**: Staleness/race condition handling required multiple iterations. Should have researched debounce + versioning patterns before planning.
- **SUMMARY frontmatter gaps**: Several phase summaries were missing `requirements_completed` fields. Milestone audit caught this but it should have been enforced during plan completion.
- **PERS-06 scope confusion**: Requirements listed it as v1, PROJECT.md listed it as out of scope. Caught during roadmap creation but wasted a decision cycle.

### Patterns Established
- Monogram format `monogram:<INITIALS>:<COLOR>` for systems without logos
- Three-layer SVG rendering order: background rect → nodes → connection pills
- NodePositionMap keyed by system ID for O(1) connection anchor lookup
- jsdom normalizes hex to rgb() in tests — assert both formats
- DOM-based SVG manipulation (DOMParser) over regex string surgery for export

### Key Lessons
- **Establish CORS/security solutions in early phases** — they can't be retrofitted without breaking export
- **Variable fonts simplify export** — one file covers all weights vs. multiple static font files
- **Configurator > WYSIWYG for consistent output** — SEs get polished diagrams every time without design skill
- **Auto-save needs explicit architecture** — debounce + versioning + flush-on-navigate is a pattern worth planning for upfront

### Cost Observations
- Model mix: primarily Opus (planning/execution), Sonnet (agents/validation)
- 16 plans across 4 phases completed in ~2 calendar days
- Phase 03 P04 was the outlier — auto-save complexity warranted its own research phase

---

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 4 |
| Plans | 16 |
| Requirements | 31 |
| Days | 2 |
| Avg plan time | ~5 min (excl. P03-04 outlier) |
| Test count | 91+ |
| Audit result | Passed (0 gaps) |
