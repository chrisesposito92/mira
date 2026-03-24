# Integration Architecture Diagrammer

## What It Is

A web app that lets an SE quickly build polished integration architecture diagrams (CUSTOMER FACING SO MAKE IT CLEAN!) showing how m3ter fits into a prospect's existing tech stack. Instead of hand-drawing diagrams on every call, you select components from a library, define data flows, and get a clean, shareable diagram in seconds.

## Why It Matters

Every prospect has a different stack — Salesforce for quoting, NetSuite for invoicing, Stripe for payments, Snowflake for analytics, plus various homegrown systems. Today, explaining "where m3ter fits" means whiteboarding or cobbling together slides. This tool makes that repeatable and professional, and the output can go straight into a proposal or follow-up email.

## Core Concepts

- **Component Library**: Pre-built nodes representing common systems in the usage-based billing ecosystem (CRMs, ERPs, payment processors, data warehouses, homegrown systems, and of course m3ter itself). EVERY SYSTEM THAT m3ter HAS AN OUT OF THE BOX CONNECTOR FOR SHOULD BE INCLUDED (https://docs.m3ter.com/guides/integrations). Every system in our library should come with that company's/tool's logo.
- **Customer's Solutions**: Allow user to enter the customer's name and product names. We should have a button to attempt to pull a logo for it to use in the diagram.
- **Integration Status**: Each connection between m3ter and another system is tagged as "Native Connector" or "Custom Build" (requires implementation work)
- **Data Flow Arrows**: Labeled, directional arrows (one-way or bidirectional) showing what data moves between systems (usage events, rated bills, account sync, invoice data, payment confirmations, etc.)
- **Templates**: Pre-built starting configurations for common verticals (AI/ML platform, IoT provider, API-first SaaS, fintech) that can be customized
- **Style**: Should follow m3ter's "style"

---

## Milestone 1: Full-Featured Integration Architecture Diagrammer

**Goal**: A complete, intelligent diagram builder that produces clean, exportable architecture visuals with smart integration awareness and collaboration features.

### 1. Drag-and-Drop Canvas

Users drag system nodes from a sidebar onto a canvas. Each node has an icon, label, and category (CRM, ERP, Payments, Data Warehouse, Observability, Homegrown, m3ter). m3ter is always present and centered by default.

### 2. Component Library

Pre-populated with the systems m3ter SEs encounter most often:

- **Native Connectors**: All systems m3ter has a native connector for (https://docs.m3ter.com/guides/integrations)
- **Custom**: A generic "Homegrown System" node the user can rename (e.g., "Internal Billing Engine", "Usage Pipeline")
- Users can also add custom nodes with a name and optional icon

### 3. Connection Drawing

Click two nodes to draw a connection between them. Each connection has:

- A direction (unidirectional or bidirectional)
- A label describing the data flow (e.g., "Usage Events via REST API", "Rated Bills via Webhook", "Account Sync")
- An integration status badge: Native (green), Webhook/API (blue), Custom (orange)

### 4. Integration Status Auto-Detection

When you draw a connection from m3ter to a known system (e.g., Salesforce, Stripe, NetSuite), the tool automatically tags it as "Native Connector" and adds a tooltip describing what the connector supports. For unknown systems, it defaults to "Custom Build" and the user can override.

### 5. Data Flow Suggestions

When connecting two nodes, the tool suggests common data flows based on system types:

- m3ter → NetSuite: suggests "Rated Bills", "Invoice Line Items", "Credit Memos"
- Homegrown → m3ter: suggests "Usage Events (REST API)", "Usage Events (File Upload)", "Account Data"

### 6. Vertical Templates

One-click starting points:

- **AI/ML Platform**: Usage pipeline → m3ter → Stripe + Salesforce
- **IoT Provider**: Device telemetry → m3ter → NetSuite + custom dashboard
- **API-First SaaS**: API gateway → m3ter → Stripe + Salesforce CPQ
- **Fintech/Payments**: Transaction processor → m3ter → NetSuite + compliance system
- Each template includes pre-labeled data flows that the user can customize

### 7. Complexity Scoring

Based on the diagram, calculate a rough integration complexity score: how many custom integrations, how many systems total, any known pain points (e.g., "NetSuite + Salesforce sync can be tricky"). Display this as a sidebar summary.

### 8. Auto-Layout

A "clean up" button that auto-arranges nodes into a readable layout so diagrams don't look messy after a bunch of dragging around.

### 9. Export Options

Export the diagram as:

- PNG/SVG image (for slides and docs)
- Interactive HTML (for embedding in emails or proposals)
- JSON (for saving and reloading later)

### 10. Save, Load, and Versioning

- Persist diagrams locally. Tag them by prospect name, vertical, and deal stage.
- Save multiple versions as a prospect's architecture evolves during the sales cycle. View a changelog of what changed between versions.

### 11. Annotations and Notes

Add callout boxes to the diagram with notes like "Requires SOC2 review", "Prospect already has this built", "Phase 2 implementation". Useful for internal context and handoff to implementation teams.

### 12. Shareable Link

Generate a read-only link to the interactive HTML version so a prospect or implementation team can view the diagram without needing the tool.
