# Phase 1: Data Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-23
**Phase:** 01-data-foundation
**Areas discussed:** Component library seed, Logo proxy approach, Diagram data model

---

## Component Library Seed

### Seed Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Only m3ter native connectors (~9) | Just the systems documented at docs.m3ter.com/guides/integrations — Salesforce, Stripe, NetSuite, etc. Small, accurate, each verified as a real native integration. | |
| Expanded list (~25-30) | Native connectors plus commonly seen systems in SE diagrams (Snowflake, Segment, HubSpot, etc.) even if they're not native m3ter integrations. Richer library out of the box. | ✓ |
| You decide | Claude picks based on research and what makes sense for SE workflows. | |

**User's choice:** Expanded list (~25-30)
**Notes:** None

### Categories

| Option | Description | Selected |
|--------|-------------|----------|
| Match m3ter diagram style | Use the groupings from m3ter's own architecture diagrams: Front Office Stack, Finance Stack, Analytics Stack, Data Infrastructure, etc. | |
| Functional categories | Group by function: CRM, Billing/Payments, Analytics, Data Warehousing, Messaging, etc. More intuitive for SEs who think in terms of what the system does. | ✓ |
| You decide | Claude picks the best categorization based on how m3ter's existing diagrams group things. | |

**User's choice:** Functional categories
**Notes:** None

### Seed Source

| Option | Description | Selected |
|--------|-------------|----------|
| SQL migration seed | Insert rows in a migration file. Data lives in Supabase, queryable via the API. Adding systems later means a new migration or admin endpoint. | ✓ |
| Backend JSON fixture | JSON file in backend/data/ loaded on first API call or via a seed script. Easier to edit/review than SQL. | |
| You decide | Claude picks the approach that fits the existing codebase patterns best. | |

**User's choice:** SQL migration seed
**Notes:** None

### Connector Tag

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — is_native_connector flag | Each system has a boolean flag. Enables Phase 3 auto-suggestion (CONN-06). | ✓ |
| No — all systems equal | No special flag. Phase 3 can infer from system name or add this later if needed. | |
| You decide | Claude decides based on what Phase 3 will need downstream. | |

**User's choice:** Yes — is_native_connector flag
**Notes:** None

---

## Logo Proxy Approach

### Logo API

| Option | Description | Selected |
|--------|-------------|----------|
| Logo.dev (Recommended) | Free tier: 10K requests/month. High quality logos, simple API. Returns PNG/SVG by domain. | ✓ |
| Clearbit Logo API | Free, no key required. Returns 128px PNG by domain. Reliable but lower resolution. Now owned by HubSpot. | |
| Google Favicon + fallback | Google's favicon service for small icons, with monogram fallback. Free, no limits, but favicons are tiny. | |

**User's choice:** Logo.dev (Recommended)
**Notes:** None

### Logo Cache

| Option | Description | Selected |
|--------|-------------|----------|
| Cache in DB as base64 | Store fetched logos as base64 in the component library table. One fetch per system. Eliminates API rate limit concerns. | ✓ |
| Cache in memory/filesystem | Cache on backend filesystem or in-memory with TTL. Lighter DB schema but logos refetched after server restart. | |
| No caching — proxy every time | Always proxy through Logo.dev. Simplest but hits rate limits and adds latency. | |

**User's choice:** Cache in DB as base64
**Notes:** None

### Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Monogram (initials on colored bg) | Generate a colored circle/rounded square with first 1-2 letters. Clean, consistent. Matches m3ter's existing diagram style. | ✓ |
| Generic icon | Use a generic 'system' icon from Lucide. Simple but all unknowns look identical. | |
| You decide | Claude picks the fallback approach. | |

**User's choice:** Monogram (initials on colored bg)
**Notes:** None

### Pre-fetch

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-fetch during seed | A seed script fetches all ~25-30 logos and stores base64 in the DB. Seed data is complete from day one. | ✓ |
| Lazy fetch on first access | Logos fetched and cached the first time each system appears in a diagram. No seed script dependency. | |
| You decide | Claude picks based on what makes the best developer experience. | |

**User's choice:** Pre-fetch during seed
**Notes:** None

---

## Diagram Data Model

### Storage

| Option | Description | Selected |
|--------|-------------|----------|
| Single JSON column (Recommended) | One `content` JSONB column holding systems, connections, positions, settings. Simple, flexible, schema_version governs shape. | ✓ |
| Normalized tables | Separate tables for diagram_systems, diagram_connections, etc. More relational but heavier schema and more joins. | |
| You decide | Claude picks based on rendering needs and existing patterns. | |

**User's choice:** Single JSON column (Recommended)
**Notes:** None

### Fields

| Option | Description | Selected |
|--------|-------------|----------|
| Essentials only | id, user_id, customer_name, project_id, content, schema_version, created_at, updated_at. | |
| Include thumbnail column now | Add thumbnail_base64 and title now to avoid future migration. | ✓ |
| You decide | Claude decides based on what minimizes future migrations. | |

**User's choice:** Include thumbnail column now
**Notes:** None

### JSON Shape

| Option | Description | Selected |
|--------|-------------|----------|
| Define shape now via Pydantic | Create DiagramContent model with typed fields. Backend validates on save. Documents contract for Phase 2. | ✓ |
| Flexible JSONB, validate later | Store any valid JSON. Phase 2 defines the shape when the renderer needs it. | |
| You decide | Claude decides based on what helps Phase 2 move faster. | |

**User's choice:** Define shape now via Pydantic
**Notes:** None

### Library Table

| Option | Description | Selected |
|--------|-------------|----------|
| DB table (component_library) | Full Supabase table. Queryable, extensible, allows future admin UI. Seeded via migration. | ✓ |
| Backend constant + logo table | System definitions in Python constant. Only logos in DB. Simpler but harder to extend. | |
| You decide | Claude picks based on extensibility needs. | |

**User's choice:** DB table (component_library)
**Notes:** None

---

## Claude's Discretion

- Exact list of ~25-30 systems and their category assignments
- DiagramContent Pydantic model field names and nesting
- Monogram color assignment strategy
- Migration numbering

## Deferred Ideas

None — discussion stayed within phase scope.
