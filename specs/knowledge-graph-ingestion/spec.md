# Feature Specification: IT Knowledge Graph Ingestion Pipeline

**Epic**: Epic 1 — Platform Foundation: Working App with CMDB Data

**Feature Directory**: `specs/knowledge-graph-ingestion`

**Created**: 2026-06-12

**Status**: Draft

---

## Problem Statement

Baptist Health South Florida manages a portfolio of 1,250 active production applications tracked in a CMDB (ServiceNow). The CMDB is authoritative and current, but its data is only accessible via manual export to XLSX — it cannot be queried by relationship, searched semantically, or browsed by non-technical stakeholders without T&D analyst involvement.

This epic establishes the foundational data layer for the IT Application Knowledge Graph platform: a pipeline that ingests the CMDB XLSX export, normalizes it into a structured relational schema with explicit graph relationships, and exposes the data through a working web interface. Without this foundation, no other capability (analytics, semantic search, AI agent Q&A) can function.

The specific gap this epic closes: knowledge about Baptist Health's 1,250 applications exists only in a flat spreadsheet. It cannot be queried by relationship (e.g., "which apps share a business process?"), browsed by any stakeholder interactively, or kept consistent across refreshes using stable identifiers.

---

## Goals

1. **Load all 1,250 CMDB records** into a normalized, queryable SQLite database without data loss.
2. **Establish a stable graph schema** with node tables (applications, types, processes, companies) and edge tables that model application relationships explicitly.
3. **Generate stable UUID identifiers** per application that survive re-ingestion and enable reliable cross-system references.
4. **Enable authorized operators** to refresh platform data by uploading a new CMDB XLSX export via the web interface — with real-time feedback and atomic failure handling.
5. **Provide a browsable applications table** and full-detail application panel in the web interface, making all 20 CMDB fields accessible to any user.
6. **Create the data foundation** that Epics 2, 3, and 4 (analytics, semantic search, AI agent) depend on — the schema and ETL pipeline must be designed to serve all downstream features.

---

## User Scenarios & Testing

### User Story 1 — Operator Loads CMDB Data into the Platform (Priority: P1)

An authorized operator (e.g., Chakri or another T&D team member) has received a new CMDB XLSX export from ServiceNow. They run the ETL pipeline — either from the command line or via the web interface — and the system loads all 1,250 application records into a normalized SQLite database with a graph-ready schema.

**Why this priority**: This is the irreducible prerequisite for the entire platform. No analytics, search, or AI capability can work without data. This story delivers standalone value: a populated, queryable database.

**Independent Test**: Run `python -m backend.etl.ingest --file data/cmdb_export.xlsx` against the reference CMDB XLSX. Verify that `data/cmdb.db` contains exactly 1,250 records in the `applications` table, all edge tables are populated, `application_type` values are normalized, and `etl_runs` records a successful run.

**Acceptance Scenarios**:

1. **Given** a fresh environment with no existing `data/cmdb.db`, **When** the ETL pipeline runs with the reference 1,250-record CMDB XLSX, **Then** `data/cmdb.db` is created with all node and edge tables populated, `etl_runs` shows status `success` with records_loaded = 1,250, and no records are silently dropped.
2. **Given** the ETL pipeline has completed, **When** a user queries for any application by name, **Then** all 20 CMDB fields are present and correct in the `applications` table.
3. **Given** a field with a non-canonical `application_type` value (e.g., "Software"), **When** the ETL normalizes it, **Then** the value is stored as `NULL` and a warning log entry is written with the record identifier and original value.
4. **Given** the same CMDB XLSX is re-ingested, **When** the pipeline runs a second time, **Then** every `application_id` UUID is identical to the first run (matched by Application Name + Company), and a new `etl_runs` record is added.
5. **Given** a malformed XLSX file missing required columns, **When** the pipeline attempts ingestion, **Then** the file is rejected with a descriptive error, the existing `data/cmdb.db` is fully intact (no partial writes), and the rejection is logged.

---

### User Story 2 — User Browses and Views Application Details (Priority: P2)

Any user — an enterprise architect, clinical director, or T&D owner — opens the web application and browses the full portfolio of 1,250 applications. They can filter by application type, business process, or company, and click any application name to open a detail panel showing all 20 CMDB fields.

**Why this priority**: This delivers the first tangible stakeholder value — replacing the need to open the ServiceNow XLSX directly. Once data is loaded (Story 1), this story is the minimum viable UI.

**Independent Test**: With data loaded, open `/applications` in a browser. Confirm the table shows 1,250 records, filtering by "COTS" updates the table immediately, and clicking an application name opens a 480px slide-in panel displaying all 20 fields with NULL values shown as "Not specified."

**Acceptance Scenarios**:

1. **Given** 1,250 records loaded in the database, **When** the Applications surface (`/applications`) loads, **Then** a table renders with columns Application Name, Company, Application Type, Business Process, Baptist Managed, Business Owner — paginated at 50 rows per page.
2. **Given** the filter bar, **When** a user selects "COTS" in the Application Type filter, **Then** the table immediately shows only COTS applications with no page reload, and an active filter badge appears.
3. **Given** any application name in the table or a query result, **When** the user clicks it, **Then** a 480px panel slides in from the right showing all 20 CMDB fields with human-readable labels; NULL fields display as "Not specified" in muted color.
4. **Given** the detail panel is open, **When** the user presses Escape, clicks the ✕ button, or clicks the dimmed backdrop, **Then** the panel closes and keyboard focus returns to the element that opened it.
5. **Given** the detail panel, **When** accessed by a screen reader, **Then** it has `role="dialog"`, `aria-label="Application detail: [app name]"`, and keyboard focus is trapped within the panel while open.

---

### User Story 3 — Operator Refreshes Data via Web Interface (Priority: P2)

When a new CMDB XLSX is available, an authorized operator uploads it through the web interface without leaving the browser. The system re-runs the ETL pipeline, shows real-time progress via WebSocket, and automatically reloads the analytics dashboard on completion. If the upload fails, the prior data state is preserved.

**Why this priority**: Data currency is a fundamental usability requirement — the platform is only as useful as its data. This story enables non-developer operators to keep the platform current without CLI access.

**Independent Test**: With data loaded, click "Refresh Data" in the topbar, upload a new XLSX, observe the spinner and WebSocket progress updates, confirm the topbar shows the updated timestamp and record count on success, and verify that uploading a malformed XLSX leaves the database unchanged.

**Acceptance Scenarios**:

1. **Given** the "Refresh Data" button visible in the topbar on all surfaces, **When** an operator clicks it, **Then** an inline panel opens (not a modal) with a file upload input; attempting to upload a non-`.xlsx` file shows the inline error "Only .xlsx files are accepted."
2. **Given** a valid `.xlsx` file is selected and submitted, **When** the upload fires, **Then** the backend receives the file at `POST /api/refresh`, triggers the ETL pipeline, and the topbar shows an animated spinner with "Refreshing…".
3. **Given** the ETL pipeline is running, **When** the WebSocket at `/ws/refresh` is open, **Then** real-time progress events are streamed (records processed, current step); the final event indicates success or failure.
4. **Given** ETL completes successfully, **When** the completion event arrives, **Then** the topbar shows "Updated · [date] · [N] apps" for 5 seconds, Dashboard metric cards auto-reload, and `GET /api/refresh/status` returns the new timestamp.
5. **Given** ETL fails (e.g., malformed XLSX), **When** the failure event arrives, **Then** the topbar shows "Refresh failed — check the file format." in destructive color, and the prior `data/cmdb.db` is fully intact.
6. **Given** some records are skipped during ETL (e.g., malformed rows), **When** ETL completes, **Then** an amber warning chip shows "[N] records skipped — see ETL log"; clicking it opens a log drawer listing each skipped record and the failure reason.

---

### User Story 4 — Developer Sets Up the Local Development Environment (Priority: P1)

A developer clones the repository, installs dependencies, and runs both the React frontend and FastAPI backend locally. The KSquare design system is in place, navigation works across all 5 surfaces, and the project is structured to support all subsequent epics.

**Why this priority**: All stories in this epic (and every subsequent epic) require a working local dev environment. This is the technical prerequisite for all other work.

**Independent Test**: On a fresh machine with Python 3.10+ and Node 18+, run `pip install -r requirements.txt` then `npm install && npm run dev`. Confirm React loads at `localhost:5173` with the glassmorphism sidebar and 5 nav items; `localhost:8000/api/health` returns `{"status": "ok"}`.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** `pip install -r requirements.txt` and `npm install && npm run dev` are run, **Then** React loads at `localhost:5173` and FastAPI responds at `localhost:8000/api/health` with `{"status": "ok"}`.
2. **Given** the project directory, **When** `.gitignore` is inspected, **Then** `.env`, `data/`, `__pycache__/`, `node_modules/`, and `*.pyc` are all listed; `.env` is never committed.
3. **Given** the sidebar, **When** it renders, **Then** it shows 5 nav items (Dashboard, Query, Analytics, Redundancy Explorer, Applications) using `background: rgba(29,50,105,0.88)` and `backdrop-filter: blur(16px)`.
4. **Given** all 18 color tokens and 10 typography roles defined in the design system, **When** any surface loads, **Then** they are available as CSS custom properties on `:root`.

---

### Edge Cases

- **Malformed XLSX — missing required columns**: File must be rejected with a clear error message listing the missing columns. No partial write to `data/cmdb.db`. Prior data state fully preserved.
- **Duplicate application names within the same company**: System generates a warning log entry per duplicate and loads both records with distinct UUIDs. Neither record is silently dropped.
- **Application with NULL Business Process, Architecture Type, or Business Criticality**: Record loads successfully with `NULL` for the missing field. No error raised. NULL fields display as "Not specified" in the UI.
- **Application name changes between XLSX versions**: The old record is treated as a new record on re-ingest (new UUID, new row). The previous record with the old name is marked `inactive_status = 0`. A warning is logged.
- **Re-ingest with no changes**: UUID values are identical to the previous run. `etl_runs` records a new entry. No data is duplicated.
- **Records absent from new XLSX**: Absent records are marked `active_status = 0` (soft delete). Their UUIDs and data are preserved. They are excluded from default query results but retained for historical reference.
- **XLSX with more than 1,250 records**: Pipeline ingests all records. No hardcoded record count limit. `etl_runs` reflects the actual records_loaded count.
- **ETL interrupted mid-run** (e.g., process killed): SQLite transaction rollback ensures no partial data is committed. Prior `data/cmdb.db` state is fully restored.
- **Detail panel opened for application with all NULL optional fields**: Panel renders all 20 fields; all NULL fields show "Not specified" in muted color — never blank, never the string "null".
- **Non-.xlsx file uploaded to Data Refresh**: Rejected client-side with the inline error "Only .xlsx files are accepted." — file never reaches the backend.
- **WebSocket connection lost during ETL refresh**: UI falls back to polling `GET /api/refresh/status` at a 5-second interval. User is still notified of completion or failure.
- **`application_type` value is blank string**: Normalized to `NULL` with a warning log entry (same handling as unrecognized values).

---

## Functional Requirements

### FR-001: CMDB XLSX Ingestion
The ETL pipeline MUST ingest a CMDB XLSX file conforming to the 20-column Baptist Health schema. All 1,250 records MUST be loaded without data loss. Records with missing optional fields (Architecture Type, Business Criticality, Environment) MUST be loaded with `NULL` values and MUST NOT raise an error. Duplicate application names within the same company MUST each be loaded with distinct UUIDs; a warning log entry MUST be written for each duplicate.

### FR-002: Field Normalization
The ETL pipeline MUST normalize `Application Type` values to `COTS`, `Homegrown`, or `NULL`. Any non-matching value MUST be stored as `NULL` with a warning log entry. All string fields MUST have leading and trailing whitespace removed. `Baptist Managed` values (`True`/`False`/`1`/`0`/`Yes`/`No`, case-insensitive) MUST resolve to SQLite boolean integers (1 or 0).

### FR-003: UUID Generation and Preservation
The ETL pipeline MUST generate a stable UUID v4 `application_id` for each application record on first ingest, using Application Name + Company as the natural deduplication key. On re-ingest, existing `application_id` values MUST be preserved for records matching by Application Name + Company. A record whose Application Name changes across XLSX versions MUST be treated as a new application with a new UUID; a warning MUST be logged.

### FR-004: Manual Data Refresh (ETL Trigger)
The system MUST allow an authorized operator to trigger a data refresh by uploading a new CMDB XLSX via the web interface. The ETL pipeline MUST re-run on upload, preserve existing UUIDs for unchanged records, add new records, and mark absent records as `active_status = 0` (soft delete) rather than deleting them. New application records MUST appear in query results within 60 seconds of a successful refresh. If the uploaded file is malformed or missing required columns, the system MUST reject it with a descriptive error message and MUST NOT modify the existing data (full transaction rollback).

### FR-005: Relational Graph Schema (SQLite DDL)
The system MUST maintain a SQLite database with the following node tables: `applications` (all 20 CMDB fields plus `application_id`, `active_status`), `application_types`, `architecture_types`, `business_processes`, `companies`. Edge tables MUST include: `app_uses_type`, `app_has_architecture`, `app_supports_process`. An `etl_runs` table MUST track each pipeline run with timestamp, file hash, records loaded, records skipped, and status. Foreign key relationships MUST enforce referential integrity. SQLite WAL mode (`PRAGMA journal_mode=WAL`) MUST be enabled to allow concurrent reads during ETL writes.

### FR-006: ETL Error Logging
Every ETL error MUST be logged with the record identifier (Application Name + Company) and the specific failure reason. The `etl_runs` table MUST record `records_loaded`, `records_skipped`, and overall `status` (`success`, `partial`, `failed`) for each run. The web interface MUST expose a log view of skipped records for any run that produced warnings.

### FR-007: Application Browse and Filter UI
The web interface MUST provide an Applications surface (`/applications`) displaying all applications in a paginated table (50 rows per page) with columns: Application Name (teal link), Company, Application Type, Business Process, Baptist Managed, Business Owner. Filter controls for Business Process, Application Type, Company, and Baptist Managed MUST apply immediately on change with no "Apply" button. A name search input MUST filter by case-insensitive substring match. Active filter count badge and "Clear filters" link MUST be shown when any filter is active.

### FR-008: Application Detail Panel
The web interface MUST allow any user to click an Application Name in any table or query result to open a 480px slide-in detail panel displaying all 20 CMDB fields with human-readable labels. NULL fields MUST display as "Not specified" in muted color — never blank or "null". The panel MUST close on Escape key, ✕ button click, or backdrop click, returning focus to the triggering element. The panel MUST have `role="dialog"`, `aria-label="Application detail: [app name]"`, and keyboard focus trap.

### FR-009: Dashboard Portfolio Metrics
The web interface Dashboard MUST display at minimum: total application count, COTS count, Homegrown count, and the timestamp of the last successful data refresh. Metric cards MUST use skeleton loaders during the initial data fetch. The dashboard MUST show "Never" if no successful ETL run has been recorded.

### FR-010: Data Refresh Web Trigger
The web interface MUST provide a permanently visible "Refresh Data" button in the topbar, accessible from all surfaces at all supported breakpoints. Clicking it MUST open an inline panel (not a modal) with a file upload input. The system MUST reject non-`.xlsx` file types with the inline error "Only .xlsx files are accepted." ETL progress MUST be streamed in real time via WebSocket. On success, the topbar MUST show the updated timestamp and record count. On failure, the topbar MUST show a descriptive failure message in destructive color.

### Key Entities

- **Application**: A discrete software system tracked in the CMDB. Identified by a stable UUID `application_id`. Has 20 CMDB fields including name, company, publisher, description, ownership, type classification, architecture classification, business process association, and operational status.
- **Application Type**: Classification of an application's commercial origin — `COTS`, `Homegrown`, or unclassified (`NULL`).
- **Architecture Type**: Deployment pattern of an application — `Client Server`, `Platform Host`, `Web Based`, `N-Tier`, `Other`, or unclassified.
- **Business Process**: The organizational function an application serves (e.g., "Imaging", "Radiation Oncology", "Pharmacy"). A single application may support multiple business processes.
- **Company**: The Baptist Health entity that owns or uses the application (e.g., Baptist Hospital, BHMG).
- **ETL Run**: A single execution of the ingestion pipeline against a CMDB XLSX file. Tracks file hash, record counts, status, and timestamp.

---

## Non-Functional Requirements

### NFR-001: Performance
- ETL pipeline MUST complete ingestion of 1,250 records in under 5 minutes on a standard laptop CPU.
- All SQL analytics queries over the `applications` table MUST execute in under 2 seconds.
- The web interface Applications table MUST render initial results within 3 seconds of page load.
- WebSocket progress events MUST be emitted at least every 5 seconds during active ETL execution.

### NFR-002: Data Integrity
- The ETL pipeline MUST NEVER silently drop records. Every skipped or failed record MUST be logged with its identifier and failure reason.
- All SQLite writes MUST be wrapped in a single transaction. Any failure during the transaction MUST trigger a full rollback — the database MUST NOT be left in a partial state.
- The `application_id` UUID for any given application MUST remain stable across re-ingestions as long as the Application Name + Company combination is unchanged.

### NFR-003: Portability
- The system MUST run on any machine with Python 3.10+ and Node.js 18+ without cloud infrastructure dependencies.
- The SQLite database (`data/cmdb.db`) MUST be a portable single file. Moving the file to another machine MUST preserve all data.
- No external database server, message broker, or cloud service MUST be required for ETL or the Applications/Detail surfaces.

### NFR-004: Security
- The OpenAI API key (used in later epics) MUST be stored only in a `.env` file at the project root. The `.env` file MUST be listed in `.gitignore` and MUST NOT be committed to version control.
- PII-adjacent fields (Business Owner, T&D Application Owner, Primary Engineer, Last Updated By) MUST be stored in SQLite and displayed in the UI detail panel, but MUST NOT be included in ChromaDB embeddings or OpenAI API payloads (relevant to Epics 3 and 4, but the ETL pipeline here must exclude these fields from the embedding input even in Epic 1's pipeline setup).
- No authentication or RBAC is implemented in v1. Network boundary (local machine deployment) is the sole access control. This decision MUST be revisited before any deployment on a shared or internet-accessible server.

### NFR-005: Graceful Degradation
- If the ETL pipeline fails, the system MUST preserve the prior database state entirely. Users MUST be able to continue using the platform against the previously loaded data.
- If the WebSocket connection drops during a refresh, the UI MUST fall back to polling `GET /api/refresh/status` to detect completion.

### NFR-006: Accessibility
- All web interface surfaces MUST meet WCAG 2.1 AA compliance.
- All interactive elements MUST be keyboard-operable with visible focus rings (`outline: 2px solid #00A8CC`, `outline-offset: 2px`).
- All interactive elements MUST have a minimum touch target size of 44×44px.
- Color MUST NOT be the sole state indicator for any UI element.
- The Applications table MUST use `role="table"` with `scope="col"` on column headers. Application Name links MUST have descriptive `aria-label` values.

### NFR-007: Observability
- All ETL runs MUST be recorded in the `etl_runs` table with sufficient detail for an operator to understand what happened without reading log files.
- The web interface MUST display the timestamp and record count of the last successful ETL run on the Dashboard at all times.
- Skipped records MUST be accessible via the UI (log drawer) — operators MUST NOT need to read server logs to understand what was skipped.

---

## Acceptance Criteria

The following criteria define the completion threshold for Epic 1. All must pass against the reference CMDB XLSX (1,250 records) before the epic is considered done.

| ID | Criterion | Verification Method |
|----|-----------|---------------------|
| AC-001 | All 1,250 CMDB records are loaded into `applications` table after a single ETL run | `SELECT COUNT(*) FROM applications WHERE active_status = 1` returns 1,250 |
| AC-002 | `application_type` contains only `COTS`, `Homegrown`, or `NULL` after normalization | `SELECT DISTINCT application_type FROM applications` returns only these three values |
| AC-003 | No leading/trailing whitespace exists in any string field after ETL | Spot-check 20 random records; none have leading/trailing spaces in name, company, or publisher |
| AC-004 | `baptist_managed` resolves correctly from mixed input formats | Test records with `True`, `False`, `Yes`, `No`, `1`, `0` — all resolve to 1 or 0 in SQLite |
| AC-005 | Re-ingesting the same XLSX produces identical `application_id` values | Two ETL runs against identical XLSX; UUIDs match 100% |
| AC-006 | A malformed XLSX is rejected without modifying the database | Upload file missing required columns → error returned; `cmdb.db` record count unchanged |
| AC-007 | Absent records on re-ingest are marked inactive, not deleted | Remove 5 records from XLSX, re-ingest; those 5 records have `active_status = 0` with data preserved |
| AC-008 | All node and edge tables exist with correct schema and foreign key integrity | Run `PRAGMA foreign_key_check` after ETL — zero violations |
| AC-009 | Applications table renders 1,250 records across paginated pages in the UI | Open `/applications`, page through all results; total count displays "1,250 applications" |
| AC-010 | Application Type filter updates table results immediately | Select "COTS" in filter; table updates within 1 second; only COTS records shown |
| AC-011 | Application detail panel shows all 20 CMDB fields | Click any application; verify all 20 field labels are present in the panel |
| AC-012 | NULL fields in detail panel display "Not specified" | Open detail for an application with NULL Architecture Type; field shows "Not specified" in muted color |
| AC-013 | Detail panel closes on Escape and focus returns to trigger | Open panel, press Escape; panel closes, focus on the link that opened it |
| AC-014 | Data Refresh upload of non-.xlsx file is rejected | Upload a `.csv` file; see "Only .xlsx files are accepted." error; no ETL triggered |
| AC-015 | ETL progress is visible in real time during refresh | Upload valid XLSX; observe spinner and at least one progress update before completion event |
| AC-016 | Dashboard shows last successful refresh timestamp after ETL | Perform refresh; navigate to Dashboard; "Last Data Refresh" shows the correct timestamp |
| AC-017 | ETL failure preserves prior database state | Upload deliberately malformed XLSX during a valid loaded state; record count unchanged |
| AC-018 | `etl_runs` table records each run with status, timestamp, and counts | After 2 ETL runs; `SELECT * FROM etl_runs` shows 2 rows with correct data |
| AC-019 | `localhost:5173` and `localhost:8000/api/health` both respond after dev setup | Run setup commands; both URLs respond within 10 seconds |
| AC-020 | Sidebar renders with correct glassmorphism styling and 5 nav items | Visual inspection; sidebar matches `rgba(29,50,105,0.88)` background and `blur(16px)` |

---

## Dependencies

### Upstream Dependencies (Inputs this Epic Requires)

| Dependency | Type | Notes |
|------------|------|-------|
| CMDB XLSX export | Data input | Baptist Health ServiceNow 20-column schema. Manual upload only in v1. Schema must match: Application Name, Company, Publisher, Description, Updated, Last Updated By, Business Owner, T&D Application Owner, Primary Engineer, Application Support Group, Active, Install Status, Application URL, Application Portfolio Manager, Application Type, Architecture Type, Baptist Managed, Business Criticality, Business Process, Environment |
| Python 3.10+ | Runtime | Required for ETL pipeline and FastAPI backend. Python 3.11 recommended for performance. |
| Node.js 18.x LTS | Build toolchain | Required for React frontend build only. Not a runtime dependency. |
| pandas 2.x + openpyxl 3.x | Python libraries | XLSX parsing. Must be installed via `requirements.txt`. |
| SQLite 3.35+ | Database | Built into Python stdlib. No external server. WAL mode requires SQLite 3.22+. |
| networkx 3.x | Python library | In-memory graph engine. Loaded at FastAPI startup. Graph reload triggered after each successful ETL run. |
| FastAPI 0.110+ + uvicorn 0.29+ | Web framework | REST API and WebSocket server. Runs at `localhost:8000`. |
| React JS 18.x + Vite 5.x | Frontend framework | SPA served at `localhost:5173` in development. |

### Downstream Dependencies (What Depends on This Epic)

| Consumer | Dependency on Epic 1 |
|----------|---------------------|
| Epic 2: Portfolio Analytics & Redundancy Explorer | Requires populated SQLite schema (node + edge tables) and the networkx graph loaded from those tables. FR-6, FR-7, FR-9 are blocked until FR-005 is complete and 1,250 records are loaded. |
| Epic 3: Semantic Search | Requires the ETL pipeline infrastructure (ingest + normalize + UUID steps) as the base for the embedding generation step (FR-011). ChromaDB integration extends the Epic 1 ETL pipeline. |
| Epic 4: Agentic NL Q&A | Requires all of Epic 1 (data loaded, API server running) plus Epics 2 and 3. The agent tools (`sql_analytics`, `graph_traversal`, `semantic_search`) query the infrastructure established here. |

### Deferred / Out of Scope

- **ServiceNow API integration**: Data enters the system only via XLSX upload in v1. Automated sync from ServiceNow is a v2 item (OQ-1, pending Chakri input).
- **User authentication / RBAC**: Out of scope for MVP. Must be added before any deployment outside the local machine.
- **Business Process taxonomy normalization**: Raw values are loaded as-is. Cleanup of `'-Not Listed-'` and other non-standard values is deferred post-launch.
- **ChromaDB embedding pipeline**: The ETL pipeline architecture is established in this epic, but the embedding generation step (`embed.py`) is built in Epic 3.
- **Write-back to ServiceNow CMDB**: This platform is read-only in all versions scoped to date.

---

## Assumptions

- **A-1 (Data source)**: CMDB data enters the system only via XLSX upload. The 20-column schema from the Baptist Health ServiceNow export is the authoritative input format. Any schema changes in ServiceNow require a corresponding ETL update.
- **A-2 (Natural key for deduplication)**: Application Name + Company uniquely identifies an application across XLSX versions. This is the deduplication key for UUID preservation on re-ingest.
- **A-3 (No Business Process taxonomy)**: Business Process values are loaded as-is from the XLSX. No canonical taxonomy exists in v1. Data quality cleanup (e.g., normalizing `'-Not Listed-'`) is post-launch.
- **A-4 (No authentication)**: The platform is deployed on a local machine for the MVP demo. The network boundary (localhost) is the only access control. This is confirmed safe for the MVP demo scope and must be revisited before any shared or networked deployment.
- **A-5 (Authorized operator)**: Any user with access to the local deployment can trigger a data refresh. No RBAC is implemented.
- **A-6 (ETL performance target)**: 1,250 records is the current dataset size. The ETL pipeline is designed for this scale. Performance targets are scoped accordingly. If the dataset grows significantly, targets should be re-evaluated.
- **A-7 (PII field handling)**: Owner names, engineer names, and Last Updated By are stored in SQLite and displayed in the detail panel, but are excluded from all future ChromaDB embeddings and OpenAI API payloads. The ETL pipeline must not include these fields in the embedding input even in later epics.
- **A-8 (OpenAI API key)**: Provisioned via `.env` file. No organizational secrets management is required for MVP. The key is never committed to version control.
