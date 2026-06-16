---
stepsCompleted: [1, 2, 3, 4]
status: final
inputDocuments:
  - docs/planning-artifacts/prds/prd-BMAD-WorkSpace-2026-06-12/prd.md
  - docs/planning-artifacts/architecture.md
  - docs/planning-artifacts/ux-designs/ux-BMAD-WorkSpace-2026-06-12/DESIGN.md
  - docs/planning-artifacts/ux-designs/ux-BMAD-WorkSpace-2026-06-12/EXPERIENCE.md
---

# IT Application Knowledge Graph — Agentic Intelligence Platform - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the IT Application Knowledge Graph — Agentic Intelligence Platform, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

---

## Requirements Inventory

### Functional Requirements

FR-1: The ETL Pipeline ingests a CMDB XLSX file conforming to the 20-column Baptist Health schema (Application Name, Company, Publisher, Description, Updated, Last Updated By, Business Owner, T&D Application Owner, Primary Engineer, Application Support Group, Active, Install Status, Application URL, Application Portfolio Manager, Application Type, Architecture Type, Baptist Managed, Business Criticality, Business Process, Environment). All 1,250 records are loaded without data loss. Missing optional fields stored as NULL without error.

FR-2: Field normalization — Application Type values normalized to COTS, Homegrown, or NULL; all string fields trimmed of whitespace; Baptist Managed converted to boolean. Non-matching Application Type values stored as NULL with a warning log entry.

FR-3: UUID Generation — stable UUID v4 application_id generated for each record on first ingest; preserved on re-ingest matched by Application Name + Company. Application Name change treated as new record with new UUID; warning logged.

FR-4: Manual Data Refresh — operator triggers refresh via web interface or CLI by uploading new CMDB XLSX. System re-runs ETL, preserves UUIDs for unchanged records, adds new records, flags absent records as inactive (not deleted). New records appear within 60 seconds. Malformed XLSX rejected with error; prior data state preserved (no partial writes). ETL errors logged with record identifier.

FR-5: Relational Graph Schema — SQLite schema with node tables (applications, application_types, architecture_types, business_processes, companies) and edge tables (app_uses_type, app_has_architecture, app_supports_process). All 20 CMDB columns queryable. Foreign key integrity enforced. Schema migrations run without data loss.

FR-6: Redundancy Cluster Detection — system identifies sets of 2+ applications sharing the same Business Process, exposed as a queryable result set ranked by cluster size (largest first). Each cluster includes: Business Process name, application names, Application Types, Baptist Managed flags. Returns at least 5 clusters from the reference dataset.

FR-7: Vendor Concentration Analysis — system identifies sets of 3+ applications sharing the same Publisher. Results sorted by application count descending, include publisher name, count, and application name list.

FR-8: Graph Traversal — networkx-based graph traversal for multi-hop relationship queries (e.g., "which business processes are supported by vendor-managed apps?"). Results in < 5 seconds for the 1,250-node graph. Results include traversal path as citation.

FR-9: Distribution Analytics — 5 pre-built analytics queries: (1) app count by Application Type, (2) app count by Architecture Type, (3) app count by Business Process (top 20), (4) app count by Company, (5) COTS vs Homegrown breakdown by Business Process. Each query executes in < 2 seconds. Results match reference dataset within ±1%.

FR-10: Redundancy Report Export — CSV export of redundancy cluster analysis containing: Business Process, Application Name, Application Type, Architecture Type, Baptist Managed, Business Owner, T&D Application Owner. Export completes within 10 seconds for 1,250 records. Opens correctly in Excel/Google Sheets.

FR-11: Embedding Generation — ETL generates sentence-transformer embeddings (all-MiniLM-L6-v2, CPU) for concatenated application name + description. Stored in ChromaDB with application_id as document ID. All 1,250 apps embedded after ETL, < 5 minutes total. Only changed records re-embedded on refresh.

FR-12: Semantic Search Query — user submits NL description, receives ranked list of up to 10 applications by semantic similarity. "dosimetry QA radiation" returns "3D Scanner" in top 3. "computer assisted coding billing" returns "3M-CAC" in top 3. Response time < 3 seconds.

FR-13: Search Result Metadata — each semantic search result includes: Application Name, Business Process, Application Type, Baptist Managed flag, Business Owner, similarity score (normalized [0,1], 2 decimal places).

FR-14: NL Query Routing — Agent classifies each NL query into: SQL analytics (counting/distribution), graph traversal (relationship/multi-hop), or semantic search (capability-match/"do we have X?"). Multiple tools invoked in sequence for compound queries.

FR-15: Coverage of 10 Epic 5 Sample Questions — Agent correctly answers all 10 sample questions: (1) app count + distribution by type, (2) COTS vs homegrown vs other, (3) apps supporting specific business function, (4) "do we already have X?", (5) overlapping/redundant apps, (6) business processes with multiple apps, (7) architecture types distribution, (8) Baptist-managed vs vendor-managed, (9) apps by business process, (10) find apps similar to description.

FR-16: Cited, Explainable Responses — every Agent response cites the data source (e.g., "Source: SQL analytics — Business Process filter"). No response omits a citation. Citations are human-readable. Responses referencing a specific application include Application Name, Business Owner, and T&D Application Owner.

FR-17: Follow-up Query Context — Agent retains conversation context for at least 5 turns within a session. Follow-up queries referencing "those" or "them" correctly scope to the prior result set. Context resets on page reload.

FR-18: NL Query Interface — web interface with prominent text input, submit button, results panel rendering structured Agent response. No page reload on submit. Handles both plain-text answers and tabular data. Session query history scrollable above active input.

FR-19: Analytics Dashboard — dedicated Analytics view displaying all 5 distributions (FR-9) as charts and tables. All distributions render on page load. Charts update within 2 seconds of Data Refresh. Each chart has accessible underlying data table.

FR-20: Application Detail View — clicking any Application Name opens a detail panel showing all 20 CMDB fields. Opens without page navigation (modal or side panel). NULL fields display as "Not specified". All 20 fields with human-readable labels.

FR-21: Redundancy Explorer — dedicated view listing Redundancy Clusters (FR-6) with drill-down per cluster and CSV export (FR-10). Accessible from main navigation. Each cluster expandable to show all member applications. CSV export triggers file download.

FR-22: Data Refresh Trigger — operator uploads new CMDB XLSX via web form. Interface accepts .xlsx only (other types rejected with error). Real-time refresh status (running/complete/failed) via polling or WebSocket. Analytics dashboard auto-reloads on completion. Last successful refresh timestamp displayed.

---

### NonFunctional Requirements

NFR-1: Performance — SQL analytics queries execute in < 2 seconds. Semantic search returns results in < 3 seconds. Agent end-to-end response (including OpenAI API round-trip) < 10 seconds for simple queries. Graph traversal < 5 seconds for 1,250-node graph.

NFR-2: Data Integrity — ETL never silently drops records. All ingestion errors logged with record identifier and failure reason. On any ETL failure, prior data state preserved (no partial writes — full transaction rollback).

NFR-3: Factual Accuracy — Agent must not generate Application names, counts, or relationships not present in the database. All Agent claims must be traceable to a specific query result.

NFR-4: Portability — system runs on any machine with Python 3.10+ and Node.js 18+ without cloud dependencies. SQLite and ChromaDB data files are portable as a directory.

NFR-5: Graceful Degradation — when OpenAI API is unreachable, SQL analytics and semantic search remain fully functional. UI displays "AI agent offline" banner; NL query input disabled; analytics and applications surfaces unaffected.

NFR-6: Security — OpenAI API key stored only in .env file; never committed to version control. PII fields (Business Owner, T&D Application Owner, Primary Engineer, Last Updated By) stored in SQLite and displayed in UI but excluded from all OpenAI API payloads and ChromaDB embeddings.

NFR-7: Accessibility — WCAG 2.1 AA compliance across all surfaces. All color pairs pass contrast ratios. All interactive elements keyboard-operable. Focus rings visible at all times on keyboard navigation.

NFR-8: No Authentication (MVP) — no login or RBAC in v1. Network boundary is the only access control. Must be revisited before any shared/networked deployment.

---

### Additional Requirements (Architecture)

- **Project setup**: Directory structure with `backend/`, `frontend/`, `data/` (gitignored), `.env` (gitignored), `.gitignore` covering `.env`, `data/`, `__pycache__/`, `node_modules/`
- **SQLite WAL mode**: `PRAGMA journal_mode=WAL` enabled at connection time to allow concurrent reads during ETL write operations
- **networkx graph lifecycle**: Graph loaded from SQLite at FastAPI startup; reloaded after every successful ETL refresh
- **ETL transaction**: All SQLite writes wrapped in a single transaction; full rollback on any error
- **Incremental re-embedding**: ETL compares current record name+description hash against stored values; only changed records re-embedded in ChromaDB
- **FastAPI server**: Runs on `localhost:8000`; serves both REST routes and WebSocket `/ws/refresh`
- **React Vite**: Runs on `localhost:5173` in development; proxies API calls to `:8000`
- **OpenAI function-calling**: Three tool definitions: `sql_analytics`, `graph_traversal`, `semantic_search`. System prompt includes PII fence and routing rules.
- **Conversation context**: Held in-memory per `conversation_id` in FastAPI; not persisted to DB; resets on server restart
- **ETL state table**: `etl_runs` table tracks run timestamp, file hash, records loaded/skipped, status — displayed in UI topbar
- **API contract**: 9 REST endpoints + 1 WebSocket (per architecture Section 5) — all unauthenticated for MVP

---

### UX Design Requirements

UX-DR1: **Glassmorphism sidebar** — Left nav sidebar with `background: rgba(29,50,105,0.88)`, `backdrop-filter: blur(16px)`, `border-right: 1px solid rgba(255,255,255,0.12)`, `box-shadow: 4px 0 24px rgba(29,50,105,0.18)`. Width 240px expanded, 64px icon-only at 1024–1279px, slide-in drawer at 768–1023px.

UX-DR2: **5-surface information architecture** — Dashboard `/`, Query `/query`, Analytics `/analytics`, Redundancy Explorer `/redundancy`, Applications `/applications`. Fixed left sidebar. Sticky topbar. White content area. Active nav item non-clickable with `aria-current="page"`.

UX-DR3: **Detail panel overlay** — 480px slide-in from right edge, `transform: translateX(0)` from `translateX(100%)`, `240ms ease-out`. Backdrop dims main content to 40% opacity. Closes on ✕, Escape, or backdrop click. Focus trapped within panel while open. Focus returns to triggering element on close. `role="dialog"`, `aria-label="Application detail: [name]"`. "Find similar apps" button navigates to Query surface with semantic search pre-filled.

UX-DR4: **NL Query interface behavior** — Enter fires query, Shift+Enter inserts newline. Input disabled with animated teal dot indicator during Agent processing (`aria-busy="true"`). Citation chip above every result block. Application Name column is teal link opening detail panel. "Show all N results" link to `/applications` with filter pre-applied. Follow-up pills appear below result and auto-dismiss on new manual query.

UX-DR5: **Metric cards** — 4-column grid at ≥1280px, 2-column at 768–1023px. Click-through to relevant surface. Hover lifts to Level 2 shadow (`box-shadow` transition 120ms). Skeleton loaders on cold load (`aria-hidden="true"`).

UX-DR6: **Cluster card (Redundancy Explorer)** — Click header expands/collapses. Expanded state shows member application table with teal Application Name links. "Export cluster" button triggers CSV download for that cluster only.

UX-DR7: **Filter bar** — Dropdown filters: Business Process, Application Type, Company, Baptist Managed. Immediate apply on change (no "Apply" button). Active filter count badge on filter icon. "Clear filters" link appears when any filter is active. Keyboard-operable with `aria-expanded` and `aria-activedescendant`.

UX-DR8: **Data Refresh form** — "Refresh Data" in topbar (always visible at all breakpoints). Click opens inline panel (not modal). Accepts `.xlsx` only — other types: inline error "Only .xlsx files are accepted." Upload status updates via WebSocket: spinner during processing, "Updated · Jun 12, 2026 · 1,250 apps" on success, destructive color on failure. Analytics dashboard auto-reloads on success.

UX-DR9: **State patterns** — Cold load: skeleton loaders. Agent processing: animated teal dot + "Querying 1,250 applications…". Agent error: inline error with retry link. Empty query: "No applications match '[query]'. Closest business process: [name] — [N] apps." OpenAI offline: dismissible banner, NL input disabled. ETL warning: amber chip "[N] records skipped — see ETL log". NULL fields in detail panel: "Not specified" in muted color.

UX-DR10: **Accessibility floor** — Sidebar: `role="navigation"`, `aria-label="Main navigation"`. Detail panel: `role="dialog"`, focus trap. Agent result tables: `role="table"`, `scope="col"`, descriptive `aria-label` on Application Name links. Query input: `aria-label="Ask the Knowledge Graph"`. All interactive elements minimum 44×44px touch target. Focus rings: `outline: 2px solid #00A8CC`, `outline-offset: 2px`. Color never the sole state indicator.

UX-DR11: **Keyboard shortcuts** — `Tab`/`Shift+Tab` cycle focus. `Enter` activates. `Escape` closes detail panel, dismisses dropdowns. `Shift+Enter` newline in query. `/` focuses query input from any surface.

UX-DR12: **Conversation history** — Scrollable session history above active query input. Click replays query (pre-fills and fires). Timestamp: relative (e.g., "2m ago") until >24h, then absolute date.

UX-DR13: **Color token system** — Primary `#1D3269`, accent `#00A8CC`, background `#FFFFFF`, surface `#F8FAFC`, foreground `#0F172A`, muted `#475569`, muted-foreground `#94A3B8`, success `#10B981`, warning `#F59E0B`, destructive `#EF4444`. All implemented as CSS custom properties.

UX-DR14: **Typography** — Inter font throughout. 10 typography roles from `display` (36px/700) to `code` (13px/400 monospace). Applied via CSS utility classes per DESIGN.md token system.

UX-DR15: **Responsive layout** — ≥1280px: sidebar 240px expanded, 4-column metric grid, two-column chart layout, 480px detail panel. 1024–1279px: sidebar 64px icon-only, 400px detail panel. 768–1023px: sidebar slide-in drawer, 2-column metric grid, single-column charts, full-width detail panel. <768px: out of scope.

---

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR-1 | Epic 1 | CMDB XLSX ingestion |
| FR-2 | Epic 1 | Field normalization |
| FR-3 | Epic 1 | UUID generation + preservation |
| FR-4 | Epic 1 | Manual data refresh (web trigger) |
| FR-5 | Epic 1 | Relational graph schema (SQLite DDL) |
| FR-6 | Epic 2 | Redundancy cluster detection |
| FR-7 | Epic 2 | Vendor concentration analysis |
| FR-8 | Epic 4 | Graph traversal for agent multi-hop queries |
| FR-9 | Epic 2 | 5 pre-built distribution analytics |
| FR-10 | Epic 2 | Redundancy cluster CSV export |
| FR-11 | Epic 3 | Sentence-transformer embedding generation |
| FR-12 | Epic 3 | Semantic search query (top-10 ranked) |
| FR-13 | Epic 3 | Search result metadata (6 fields + score) |
| FR-14 | Epic 4 | NL query routing (SQL / graph / semantic) |
| FR-15 | Epic 4 | Coverage of 10 Epic 5 sample questions |
| FR-16 | Epic 4 | Cited, explainable agent responses |
| FR-17 | Epic 4 | Follow-up query context (5-turn) |
| FR-18 | Epic 4 | NL query web interface (full) |
| FR-19 | Epic 2 | Analytics dashboard view |
| FR-20 | Epic 1 | Application detail view (all 20 fields) |
| FR-21 | Epic 2 | Redundancy Explorer view |
| FR-22 | Epic 1 | Data Refresh trigger UI |

---

## Epic List

### Epic 1: Platform Foundation — Working App with CMDB Data
Users can run the platform locally, load the CMDB XLSX, browse all 1,250 applications in a working React interface, view full application detail, and trigger data refresh.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-20, FR-22

### Epic 2: Portfolio Analytics & Redundancy Explorer
T&D owners can visualize the application portfolio through 5 distribution analytics views, explore redundancy clusters by business process, and export rationalization reports as CSV.
**FRs covered:** FR-6, FR-7, FR-9, FR-10, FR-19, FR-21

### Epic 3: Semantic Search & Application Discovery
Any user can find applications by describing what they're looking for — returning ranked results by semantic similarity even without knowing exact application names.
**FRs covered:** FR-11, FR-12, FR-13

### Epic 4: Agentic NL Q&A Interface
Any user can ask plain-English portfolio questions and receive cited, explainable answers from the AI agent — with multi-turn context for follow-up queries and graceful fallback when OpenAI is offline.
**FRs covered:** FR-8, FR-14, FR-15, FR-16, FR-17, FR-18

---

## Epic 1: Platform Foundation — Working App with CMDB Data

The platform runs locally; operators can load the CMDB XLSX; users can browse all 1,250 applications and view full detail; data refresh works end-to-end.

### Story 1.1: Project Scaffold, Design System, and Local Development Environment

As a developer,
I want the project scaffolded with a running React frontend, FastAPI backend, and KSquare design system,
So that all subsequent features can be built on a consistent, working foundation.

**Acceptance Criteria:**

**Given** a fresh clone of the project repository
**When** `pip install -r requirements.txt` and `npm install && npm run dev` are run
**Then** React app loads at `localhost:5173` with a white content area and KSquare glassmorphism sidebar
**And** FastAPI responds at `localhost:8000/api/health` with `{"status": "ok"}`

**Given** the app is open in a browser
**When** the sidebar renders
**Then** it displays 5 nav items: Dashboard, Query, Analytics, Redundancy Explorer, Applications
**And** the sidebar uses `background: rgba(29,50,105,0.88)`, `backdrop-filter: blur(16px)`, `border-right: 1px solid rgba(255,255,255,0.12)`
**And** the active nav item has `aria-current="page"` and a left-border strip active indicator

**Given** the project directory
**When** `.env` and `.gitignore` are inspected
**Then** `.env` contains `OPENAI_API_KEY=sk-placeholder` and is listed in `.gitignore`
**And** `data/`, `__pycache__/`, `node_modules/`, `*.pyc` are also in `.gitignore`

**Given** any surface in the app
**When** the page CSS is inspected
**Then** all 18 color tokens (primary `#1D3269`, accent `#00A8CC`, etc.) are defined as CSS custom properties
**And** all 10 typography roles using Inter font are available as CSS utility classes

**Given** a viewport ≥1280px
**When** the sidebar renders
**Then** it is 240px wide (expanded); at 1024–1279px it collapses to 64px icon-only

---

### Story 1.2: SQLite Schema and CMDB ETL Pipeline

As an operator,
I want to run the ETL pipeline against the CMDB XLSX,
So that all 1,250 applications are loaded into a queryable SQLite database.

**Acceptance Criteria:**

**Given** `data/cmdb.db` does not exist
**When** the ETL pipeline is run with the reference CMDB XLSX
**Then** `data/cmdb.db` is created with WAL mode (`PRAGMA journal_mode=WAL`)
**And** all node tables (applications, application_types, architecture_types, business_processes, companies) and edge tables (app_uses_type, app_has_architecture, app_supports_process) exist with the correct schema
**And** the `etl_runs` table records the run with status `success`, timestamp, and records_loaded count

**Given** the reference CMDB XLSX (1,250 records)
**When** the ETL pipeline completes
**Then** exactly 1,250 records are in the `applications` table
**And** `application_type` is `COTS`, `Homegrown`, or `NULL` (non-matching values stored as `NULL` with a warning log entry)
**And** all string fields have no leading/trailing whitespace
**And** `baptist_managed` values (`True`/`False`/`Yes`/`No`/`1`/`0`) resolve to SQLite booleans

**Given** a re-ingest of the same XLSX
**When** the ETL pipeline runs a second time
**Then** each record retains its original `application_id` UUID (matched by Application Name + Company)
**And** a new entry is added to `etl_runs`

**Given** a malformed XLSX (missing required columns)
**When** the ETL pipeline is invoked
**Then** the pipeline rejects the file with a logged error
**And** `data/cmdb.db` is unchanged — no partial writes (full transaction rollback)

**Given** a record present in the prior XLSX is absent from the new XLSX
**When** ETL completes
**Then** that record has `active_status = 0` (inactive) and its UUID is preserved

---

### Story 1.3: Applications Surface — Browse and Filter All Applications

As a user,
I want to browse all 1,250 applications in a filterable, searchable table,
So that I can find any application in the portfolio by name, type, or business process.

**Acceptance Criteria:**

**Given** the Applications surface (`/applications`) loads
**When** the page renders
**Then** skeleton loaders appear, then resolve to a table with columns: Application Name (teal link), Company, Application Type, Business Process, Baptist Managed, Business Owner
**And** total count "1,250 applications" appears above the table

**Given** 1,250 records are in the database
**When** the table renders
**Then** rows are paginated at 50 per page with page controls

**Given** the filter bar
**When** a user selects "COTS" in the Application Type filter
**Then** the table immediately updates to COTS-only results (no "Apply" button)
**And** an active filter count badge appears and a "Clear filters" link is visible

**Given** a name search input
**When** a user types "scan"
**Then** the table filters to applications whose names contain "scan" (case-insensitive)

**Given** `GET /api/applications`
**When** called with `?page=1&page_size=50&application_type=COTS`
**Then** the response contains `{results[], total, page, pages}` JSON

---

### Story 1.4: Application Detail Panel

As a user,
I want to click any application name to open a full-detail panel,
So that I can see all 20 CMDB fields without navigating away from my current view.

**Acceptance Criteria:**

**Given** any application name link is clicked
**When** the click fires
**Then** a 480px panel slides in from the right edge (`translateX(100%)` → `translateX(0)`, `240ms ease-out`)
**And** main content dims to 40% opacity

**Given** the detail panel is open
**When** content renders
**Then** all 20 CMDB fields display with human-readable labels
**And** NULL fields show "Not specified" in muted color `#94A3B8` — never blank or "null"
**And** a "Find similar apps" button is present at the bottom

**Given** the detail panel is open
**When** the user presses `Escape`, clicks ✕, or clicks the dimmed backdrop
**Then** the panel closes and focus returns to the element that triggered it

**Given** the detail panel
**When** a screen reader user enters it
**Then** the panel has `role="dialog"` and `aria-label="Application detail: [app name]"`
**And** keyboard focus is trapped within the panel while it is open

**Given** `GET /api/applications/{id}`
**When** called with a valid `application_id`
**Then** all 20 CMDB fields are returned as JSON

---

### Story 1.5: Dashboard Homepage with Portfolio Metrics

As a user,
I want to see key portfolio metrics on the dashboard,
So that I can immediately understand the scale of the application portfolio and when data was last refreshed.

**Acceptance Criteria:**

**Given** the Dashboard (`/`) loads
**When** the page renders
**Then** skeleton loaders appear, then resolve to 4 metric cards: Total Applications, COTS count, Homegrown count, Last Data Refresh (timestamp or "Never")

**Given** a metric card
**When** the user hovers it
**Then** the card's box-shadow elevates to Level 2, transitioning in 120ms

**Given** `GET /api/refresh/status`
**When** called
**Then** the response contains `{last_run_at, records_loaded, status}` JSON
**And** the Dashboard "Last Data Refresh" card displays the most recent successful run's timestamp

---

### Story 1.6: Data Refresh — Upload New CMDB Export and Monitor Progress

As an operator,
I want to upload a new CMDB XLSX from the dashboard topbar and see real-time progress,
So that I can refresh platform data when a new ServiceNow export is available.

**Acceptance Criteria:**

**Given** the "Refresh Data" button visible in the topbar (all surfaces, all breakpoints)
**When** the operator clicks it
**Then** an inline panel opens (not a modal) with a file input
**And** uploading a non-.xlsx file shows inline error "Only .xlsx files are accepted."

**Given** a valid .xlsx file is uploaded
**When** submitted
**Then** `POST /api/refresh` receives the file and triggers the ETL pipeline
**And** the topbar shows a spinner: "Refreshing…"
**And** WebSocket `/ws/refresh` streams progress events

**Given** ETL completes successfully
**When** the completion event arrives via WebSocket
**Then** topbar shows "Updated · [date] · [N] apps" for 5 seconds then reverts to "Refresh Data"
**And** Dashboard metric cards reload automatically

**Given** ETL fails
**When** the failure event arrives
**Then** topbar shows "Refresh failed — check the file format." in `#EF4444`
**And** prior data in `data/cmdb.db` is intact (no partial write)

**Given** [N] records are skipped during ETL
**When** ETL completes
**Then** an amber warning chip shows "[N] records skipped — see ETL log" in the topbar
**And** clicking it opens a log drawer listing skipped records and reasons

---

## Epic 2: Portfolio Analytics & Redundancy Explorer

T&D owners can visualize the application portfolio through 5 distribution analytics views, explore redundancy clusters by business process, and export rationalization reports as CSV.

### Story 2.1: networkx Graph Engine and Distribution Analytics API

As a T&D owner,
I want to query portfolio distribution analytics,
So that I can understand how applications are distributed by type, architecture, business process, and vendor.

**Acceptance Criteria:**

**Given** FastAPI server starts
**When** the application initializes
**Then** a networkx DiGraph is loaded from SQLite edge tables (app_supports_process, app_uses_type, app_has_architecture)
**And** the graph contains all 1,250 application nodes and their relationship edges

**Given** `GET /api/analytics/distributions`
**When** called
**Then** it returns all 5 distributions as JSON: app count by Application Type, by Architecture Type, by Business Process (top 20), by Company, and COTS vs Homegrown breakdown by Business Process
**And** each query completes in < 2 seconds

**Given** `GET /api/analytics/vendor-concentration`
**When** called
**Then** it returns publishers with 3 or more applications, sorted by application count descending
**And** each entry includes publisher name, application count, and list of application names

**Given** a successful ETL refresh completes
**When** the ETL pipeline triggers a graph reload
**Then** the networkx DiGraph in memory is rebuilt from the updated SQLite data within 30 seconds

---

### Story 2.2: Analytics Dashboard Surface with Charts and Filter Drill-Down

As a T&D owner,
I want to view distribution analytics as interactive charts with filter controls,
So that I can explore the portfolio composition and drill into specific segments.

**Acceptance Criteria:**

**Given** the Analytics surface (`/analytics`) loads
**When** the page renders
**Then** all 5 distribution charts render without additional user action
**And** skeleton loaders appear during the initial fetch, replaced by charts on data arrival

**Given** the Analytics surface
**When** charts are displayed
**Then** each chart is accompanied by its underlying data table (togglable for accessibility)
**And** the Business Process chart shows the top 20 processes ranked by application count

**Given** the filter bar (Business Process, Application Type, Company, Baptist Managed filters)
**When** a filter is changed
**Then** all charts update immediately (no "Apply" button)
**And** an active filter count badge appears; "Clear filters" link is visible when any filter is active

**Given** a Data Refresh completes
**When** the WebSocket completion event is received
**Then** all 5 Analytics charts reload with updated data within 2 seconds

**Given** the vendor concentration section
**When** the page renders
**Then** publishers with 3+ applications are listed, sorted by count descending, with application names expandable

---

### Story 2.3: Redundancy Cluster Detection

As a T&D owner,
I want the system to automatically identify applications that share the same business process,
So that I can find rationalization candidates without manual analysis across 1,250 records.

**Acceptance Criteria:**

**Given** the networkx graph is loaded from SQLite
**When** `GET /api/analytics/redundancy` is called
**Then** it returns a list of redundancy clusters — sets of 2 or more applications sharing the same Business Process
**And** clusters are ranked by cluster size (largest first)
**And** each cluster includes: Business Process name, list of Application Names, Application Types, Baptist Managed flags

**Given** the reference CMDB dataset
**When** redundancy detection runs
**Then** at least 5 clusters are returned (e.g., Imaging: 67, Radiation Oncology: 88, Technology & Digital: 161)

**Given** applications with NULL Business Process
**When** redundancy detection runs
**Then** those applications are excluded from all clusters

**Given** `GET /api/analytics/redundancy?business_process=Imaging`
**When** called with a filter
**Then** only the cluster(s) matching the filtered business process are returned

---

### Story 2.4: Redundancy Explorer Surface and CSV Export

As a T&D owner (Chakri),
I want to explore redundancy clusters visually and export them as CSV,
So that I can prepare the quarterly rationalization review with an evidence-backed shortlist.

**Acceptance Criteria:**

**Given** the Redundancy Explorer surface (`/redundancy`) loads
**When** the page renders
**Then** cluster cards are listed, ranked by cluster size (largest first)
**And** each card header shows: Business Process name, application count, and an expand/collapse toggle

**Given** a cluster card header is clicked
**When** the cluster expands
**Then** a table shows all member applications with columns: Application Name (teal link), Application Type, Architecture Type, Baptist Managed
**And** clicking an Application Name opens the detail panel for that application

**Given** an expanded cluster card
**When** the user clicks "Export cluster"
**Then** a CSV file downloads containing: Business Process, Application Name, Application Type, Architecture Type, Baptist Managed, Business Owner, T&D Application Owner
**And** the export completes within 10 seconds for up to 1,250 records
**And** the exported CSV opens correctly in Excel/Google Sheets

**Given** `GET /api/analytics/redundancy/export`
**When** called with optional `?business_process=` filter
**Then** it returns a `text/csv` response with the correct columns

**Given** no redundancy clusters match the current filter
**When** the Explorer renders
**Then** it displays "No redundancy clusters found for the current filters." with a "Clear filters" CTA

---

## Epic 3: Semantic Search & Application Discovery

Any user can find applications by describing what they're looking for — returning ranked results by semantic similarity even without knowing exact application names.

### Story 3.1: Sentence-Transformer Embedding Pipeline and ChromaDB Integration

As an operator,
I want the ETL pipeline to generate semantic embeddings for all applications and store them in ChromaDB,
So that users can later search by describing an application's purpose rather than its exact name.

**Acceptance Criteria:**

**Given** the ETL pipeline runs with the reference CMDB XLSX
**When** embedding generation completes
**Then** all 1,250 applications have a corresponding vector in the ChromaDB collection at `data/chroma/`
**And** each ChromaDB document uses `application_id` as its document ID
**And** the embedding input is `application_name + " " + description` only — owner names, engineer names, and URLs are excluded

**Given** the embedding model
**When** generating embeddings for 1,250 records
**Then** the process completes in under 5 minutes on a standard laptop CPU using `all-MiniLM-L6-v2`
**And** no GPU is required

**Given** a re-ingest where some records have unchanged name and description
**When** the ETL pipeline runs
**Then** only records whose name or description changed are re-embedded (incremental update)
**And** unchanged records retain their existing ChromaDB vectors

**Given** ChromaDB metadata stored per document
**When** a document is upserted
**Then** metadata fields stored are: `application_type`, `business_process`, `baptist_managed` only
**And** no PII fields (owner names, engineer names) appear in ChromaDB metadata

**Given** `data/chroma/` directory
**When** the server restarts
**Then** ChromaDB loads the persisted collection from disk without requiring a re-embed

---

### Story 3.2: Semantic Search API and Query Surface

As a user,
I want to search for applications by describing what I'm looking for,
So that I can discover relevant applications even without knowing their exact names.

**Acceptance Criteria:**

**Given** `GET /api/search?q=dosimetry+QA+radiation`
**When** called
**Then** "3D Scanner" appears in the top 3 results
**And** the response returns up to 10 results with: `application_id`, `application_name`, `business_process`, `application_type`, `baptist_managed`, `business_owner`, `similarity_score`
**And** similarity scores are normalized to [0, 1] and expressed to 2 decimal places
**And** the response arrives in under 3 seconds

**Given** `GET /api/search?q=computer+assisted+coding+billing`
**When** called
**Then** "3M-CAC" appears in the top 3 results

**Given** `GET /api/search?q=dosimetry&business_process=Radiation+Oncology`
**When** called with a filter
**Then** only results matching both the semantic query and the business process filter are returned

**Given** the Query surface (`/query`) is loaded
**When** the page renders
**Then** a prominent text input is displayed with placeholder "Ask the Knowledge Graph"
**And** quick-query pills appear below the input (e.g., "Radiation Oncology apps", "COTS applications", "Baptist-managed apps")
**And** clicking a quick-query pill pre-fills the input and fires the search immediately (no second Enter needed)

**Given** a user types a search term and presses Enter
**When** the search fires
**Then** a results table renders with columns: Application Name (teal link), Business Process, Application Type, Baptist Managed, Business Owner, Similarity Score
**And** clicking an Application Name opens the detail panel for that application

**Given** a search that returns zero results
**When** the response arrives
**Then** the UI displays: "No applications match '[query]'. Closest business process: [name] — [N] apps." with a teal suggestion pill

---

## Epic 4: Agentic NL Q&A Interface

Any user can ask plain-English portfolio questions and receive cited, explainable answers from the AI agent — with multi-turn context for follow-up queries and graceful fallback when OpenAI is offline.

### Story 4.1: OpenAI Agent Orchestrator with Function-Calling Tools

As a user,
I want the platform to intelligently route my plain-English questions to the right data source and return a cited, factual answer,
So that I can get evidence-backed portfolio insights without knowing SQL or graph query syntax.

**Acceptance Criteria:**

**Given** `POST /api/query` with `{"text": "How many COTS vs homegrown applications do we have?", "conversation_id": "...", "history": []}`
**When** the agent processes the request
**Then** it invokes the `sql_analytics` tool and returns an answer with exact counts matching the SQLite distribution query
**And** the response includes a citation: `"Source: SQL analytics — Application Type distribution"`

**Given** `POST /api/query` with `{"text": "Which applications overlap in Imaging?"}`
**When** the agent processes the request
**Then** it invokes the `graph_traversal` tool (networkx redundancy cluster for Imaging)
**And** the response includes the traversal path citation: `"Source: Graph traversal — app_supports_process → Imaging"`

**Given** `POST /api/query` with `{"text": "Do we have a dosimetry QA application for Radiation Oncology?"}`
**When** the agent processes the request
**Then** it invokes the `semantic_search` tool and returns matching applications including "3D Scanner"
**And** the response includes citation: `"Source: Semantic Search · top match score [score]"`

**Given** a compound query: `"Which Baptist-managed apps support Radiation Oncology?"`
**When** the agent processes the request
**Then** it invokes semantic or graph traversal combined with a `baptist_managed=true` SQL filter
**And** the response lists only Baptist-managed apps in Radiation Oncology

**Given** the agent system prompt
**When** inspected
**Then** it contains an explicit PII fence: owner names, engineer names, and URLs must not be included in tool call arguments or search query text
**And** PII fields are only appended to the response after retrieval from SQLite (display only)

**Given** the agent is asked all 10 Epic 5 sample questions in sequence
**When** each question is answered
**Then** all 10 return factually correct responses verifiable against the reference CMDB dataset
**And** questions 1, 2, 7, 8 (counting questions) include exact counts matching SQL analytics output
**And** questions 3, 4, 9, 10 (application-specific) include application names and owners

**Given** any agent response that references a specific application
**When** the response is rendered
**Then** it includes Application Name, Business Owner, and T&D Application Owner
**And** no Application Name, count, or relationship is fabricated — all claims traceable to a query result

**Given** end-to-end agent response time
**When** a simple query is submitted
**Then** the full response (including OpenAI round-trip) is received within 10 seconds

---

### Story 4.2: Multi-Turn Conversation Context and Follow-Up Queries

As a user,
I want the agent to remember what I asked in my last few queries,
So that I can ask follow-up questions like "Which of those are Baptist-managed?" without repeating the full context.

**Acceptance Criteria:**

**Given** a session with `conversation_id = "abc123"` and prior query "Which apps support Radiation Oncology?" returning 88 results
**When** the follow-up query "Which of those are Baptist-managed?" is submitted with the same `conversation_id` and prior exchange in `history`
**Then** the agent correctly scopes the follow-up to the 88 Radiation Oncology apps and returns only the Baptist-managed subset

**Given** a conversation with 5 prior turns
**When** a 6th query references "those" or "them"
**Then** the agent correctly resolves the reference to the most recent result set

**Given** `history` contains at least 5 prior turns
**When** the agent constructs its OpenAI prompt
**Then** all 5 prior turns are included in the conversation context sent to gpt-4o

**Given** a page reload or new browser tab
**When** a query is submitted without a prior `conversation_id`
**Then** the agent has no memory of prior queries (context resets — in-memory only, not persisted to DB)

**Given** conversation context held in FastAPI memory
**When** the FastAPI server restarts
**Then** all conversation history is lost (expected behavior; not a bug)

---

### Story 4.3: Full NL Query Interface — Citation Chips, History, and Offline State

As a user,
I want a polished NL query interface with conversation history, follow-up suggestions, and graceful handling when the AI agent is unavailable,
So that I can work efficiently regardless of OpenAI API availability.

**Acceptance Criteria:**

**Given** the Query surface (`/query`) is loaded and a query is submitted
**When** the agent is processing
**Then** the query input is disabled with `aria-busy="true"` and an animated teal dot indicator: "Querying 1,250 applications…"
**And** on response, the input re-enables and focuses automatically

**Given** an agent response is received
**When** it renders
**Then** a citation chip appears above the result block in code typography (e.g., `Semantic Search · 3 results · 0.8s`)
**And** the result table shows Application Name as a teal link opening the detail panel
**And** "Show all N results" link navigates to `/applications` with the filter pre-applied

**Given** a result is returned
**When** the result renders
**Then** 1–3 follow-up suggestion pills appear below the result
**And** clicking a pill appends the text to the query input and fires immediately
**And** the pills dismiss automatically when a new manual query is submitted

**Given** prior queries in the same session
**When** the Query surface is open
**Then** conversation history is scrollable above the active input
**And** each history item shows the query text and a relative timestamp (e.g., "2m ago")
**And** clicking a history item pre-fills and fires that query again

**Given** the OpenAI API is unreachable
**When** a query is submitted
**Then** a dismissible banner appears: "AI agent is offline. SQL analytics and semantic search are available — use the Analytics and Applications surfaces."
**And** the NL query input is disabled
**And** quick-query pills route to `/analytics` instead

**Given** the keyboard shortcut `/`
**When** pressed from any surface (while not already in a text input)
**Then** focus moves to the query input on the Query surface

**Given** the keyboard shortcut `Shift+Enter`
**When** pressed in the query input
**Then** a newline is inserted rather than firing the query

