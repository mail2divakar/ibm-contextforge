# Tasks: IT Knowledge Graph Ingestion Pipeline

**Input**: Design documents from `specs/knowledge-graph-ingestion/`

**Prerequisites**: plan.md, spec.md, data-model.md, contracts/api.md, contracts/ui.md, research.md, quickstart.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Exact file paths are included in every task description

## User Story Map

| Story | Title | Priority |
|-------|-------|---------|
| US4 | Developer Sets Up the Local Development Environment | P1 |
| US1 | Operator Loads CMDB Data into the Platform | P1 |
| US2 | User Browses and Views Application Details | P2 |
| US3 | Operator Refreshes Data via Web Interface | P2 |

> US4 is listed first because it is the physical prerequisite for all browser-based validation of US2 and US3.

---

## Phase 1: Setup (Project Skeleton)

**Purpose**: Create the project directory structure, config files, and package manifests. No user story label — this is pre-story scaffolding.

- [X] T001 Create full project directory tree: `backend/`, `backend/db/`, `backend/etl/`, `backend/graph/`, `backend/agent/`, `backend/api/`, `data/` (gitkeep), and Python `__init__.py` files in each `backend/` subdirectory
- [X] T002 Create `.gitignore` listing `.env`, `data/`, `__pycache__/`, `*.pyc`, `node_modules/`, `*.db`, `chroma/`, `.DS_Store`, `dist/`
- [X] T003 [P] Create `.env.example` with `OPENAI_API_KEY=your_key_here` placeholder comment; create `.env` locally (not committed) with placeholder value
- [X] T004 [P] Create `requirements.txt` pinning: `fastapi>=0.110`, `uvicorn[standard]>=0.29`, `pandas>=2.0`, `openpyxl>=3.1`, `networkx>=3.0`, `python-multipart>=0.0.9`, `chromadb>=0.4` (stub), `sentence-transformers>=2.0` (stub), `openai>=1.0` (stub)
- [X] T005 [P] Initialize frontend: run `npm create vite@latest frontend -- --template react-ts` from project root; then `cd frontend && npm install react-router-dom`; verify `frontend/src/` structure matches plan.md

**Checkpoint**: Project tree exists, config files in place, frontend scaffold created.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that every user story depends on. No story label.

**⚠️ CRITICAL**: All user story phases depend on this phase completing first.

- [X] T006 Write full SQLite DDL in `backend/db/schema.sql` — all 9 tables (applications, application_types, architecture_types, business_processes, companies, app_uses_type, app_has_architecture, app_supports_process, etl_runs), WAL pragma, `PRAGMA foreign_keys = ON`, and all 7 partial indexes from data-model.md
- [X] T007 Create `backend/db/connection.py` — `get_connection(db_path) → sqlite3.Connection` with WAL mode and foreign_keys ON set on every connection; `init_db(db_path)` that reads and executes `schema.sql`; all SQL in this module uses `?` placeholders only
- [X] T008 Create `backend/db/init_schema.py` — `if __name__ == "__main__"` block that calls `init_db("data/cmdb.db")` and prints `"Schema initialized at data/cmdb.db"`; this enables `python -m backend.db.init_schema`
- [X] T009 [P] Create `backend/main.py` — FastAPI app instance; CORS middleware with `allow_origins=["http://localhost:5173"]`; `@asynccontextmanager` lifespan that loads networkx graph on startup (placeholder until graph/model.py exists in US1); include router from `backend/api/routes.py`; top-level `GET /api/health` route returning `{"status": "ok", "graph_loaded": false, "db_path": "data/cmdb.db"}`
- [X] T010 [P] Create `backend/api/routes.py` — empty APIRouter with placeholder comments for all 6 Epic 1 routes per contracts/api.md; register router in main.py; create `frontend/vite.config.ts` with `/api` proxy → `http://localhost:8000` and `/ws` proxy → `ws://localhost:8000` (ws: true)

**Checkpoint**: Foundation ready — `python -m backend.db.init_schema` creates the database; `uvicorn backend.main:app --reload` starts without errors; `/api/health` returns 200.

---

## Phase 3: User Story 4 — Developer Sets Up Local Dev Environment (P1)

**Goal**: Working app shell with glassmorphism sidebar, 5 nav routes, design system tokens, and a live health endpoint — the environment every other story is validated in.

**Independent Test**: Run setup commands from `quickstart.md` (Setup + Scenario 1). `curl localhost:8000/api/health` returns `{"status":"ok"}`. Open `localhost:5173` — glassmorphism sidebar with 5 nav items visible; all 5 routes navigate without errors.

- [X] T011 [US4] Create `frontend/src/index.css` — `@import` Inter from Google Fonts (weights 300–800); `:root` block with all 8 design system tokens (`--primary: #1D3269`, `--accent: #00A8CC`, `--surface: #F8FAFC`, `--border: #E2E8F0`, `--fg: #0F172A`, `--muted: #64748B`, `--success: #10B981`, `--warning: #F59E0B`); global box-sizing reset; `-webkit-font-smoothing: antialiased`
- [X] T012 [P] [US4] Create `frontend/src/components/Sidebar.tsx` — 240px fixed, `background: rgba(29,50,105,0.88)`, `backdrop-filter: blur(16px)`, `border-right: 1px solid rgba(255,255,255,0.12)`, sticky top/height 100vh; logo area ("KSquare Group" 18px/700/white + "AppGraph" 11px/teal/uppercase); 5 `<NavLink>` items (Dashboard, Query, Analytics, Redundancy, Applications) with icon emoji + active class applying left `3px solid #00A8CC` + `rgba(0,168,204,0.20)` bg; avatar footer circle with initials gradient
- [X] T013 [P] [US4] Create `frontend/src/components/Topbar.tsx` — 56px height, white bg, `border-bottom: 1px solid #E2E8F0`, sticky; `title` prop rendered left (17px/700); right slot: metadata text prop + "Refresh Data" `<button>` (accent bg, 8px radius, shadow) that calls `onRefresh` prop; `onRefresh` is a no-op prop in Phase 3 — wired in Phase 6 (US3 T041)
- [X] T014 [US4] Create `frontend/src/App.tsx` — `<BrowserRouter>` wrapping shell layout: `<Sidebar>` (fixed left) + `<div>` (flex-1, flex-col) containing `<Topbar title={currentRouteTitle}>` + `<Routes>`; define 5 routes mapping `/`, `/query`, `/analytics`, `/redundancy`, `/applications` to their surface components; derive `currentRouteTitle` from `useLocation()`
- [X] T015 [P] [US4] Create shell surfaces `frontend/src/surfaces/Query.tsx`, `frontend/src/surfaces/Analytics.tsx`, `frontend/src/surfaces/Redundancy.tsx` — each renders only a content area placeholder div with a centered "Coming soon — Epic N" message; these are navigation-complete shells
- [X] T016 [P] [US4] Create `frontend/src/surfaces/Dashboard.tsx` shell — 4 `<MetricCard>` placeholders with label text and a skeleton loader state; `<MetricCard>` import from components (created in T028 US2 — use inline placeholder div here until T028 is available); static "Last refresh: —" metadata
- [ ] T017 [US4] Validate US4 end-to-end: run `pip install -r requirements.txt` → `python -m backend.db.init_schema` → `uvicorn backend.main:app --reload --port 8000` → `curl localhost:8000/api/health`; run `cd frontend && npm install && npm run dev`; open `localhost:5173`; confirm glassmorphism sidebar, 5 nav items, all routes render, no console errors, CSS `--primary` and `--accent` tokens present on `:root`

**Checkpoint**: US4 complete — working dev environment with shell navigation. All 4 acceptance scenarios for US4 pass.

---

## Phase 4: User Story 1 — Operator Loads CMDB Data into the Platform (P1)

**Goal**: CLI-invokable ETL pipeline that loads 1,250 CMDB records from XLSX into normalized SQLite with stable UUIDs, atomic transactions, and an audit trail in `etl_runs`.

**Independent Test**: Run `python -m backend.etl.ingest --file path/to/cmdb_export.xlsx`. Verify via `quickstart.md` Scenarios 2–5: 1,250 records in `applications` (active_status=1), edge tables populated, `application_type` values normalized, `etl_runs` shows `status='success'`, re-ingest produces identical UUIDs, malformed file is rejected with DB unchanged.

- [X] T018 [P] [US1] Create `backend/etl/normalize.py` — `normalize_application_type(raw) → str | None` (maps to 'COTS'/'Homegrown'/None; logs warning with record identifier on non-matching value); `normalize_baptist_managed(raw) → int | None` (True/Yes/1 → 1; False/No/0 → 0; else None + warning); `strip_strings(record_dict) → dict` (strip all string values, empty string → None); `compute_content_hash(name, description) → str` (SHA-256 hex of f"{name or ''}{description or ''}"); `build_embed_payload(record) → str` (returns f"{record['application_name']} {record.get('description','')}" — no PII fields; include docstring listing excluded fields: business_owner, td_app_owner, primary_engineer, last_updated_by)
- [X] T019 [US1] Create `backend/etl/ingest.py` — `REQUIRED_COLUMNS: list[str]` (all 20 CMDB column names); `validate_schema(df) → None | raises SchemaValidationError` (check all REQUIRED_COLUMNS present in df.columns); `parse_row(row, uuid_map) → dict` (call normalize.py functions on each field; generate UUID v4 or preserve from uuid_map by (application_name, company) key; compute content_hash); `run_etl(file_path: str, progress_queue=None) → dict` (pandas read_excel → validate_schema → build uuid_map from existing DB → parse each row → call write_transaction → emit progress to queue if provided → return {status, records_loaded, records_skipped})
- [X] T020 [US1] Create `backend/db/write_transaction.py` — `write_transaction(records, run_meta, db_path)`: open connection; `BEGIN`; UPSERT `applications` (all 20 fields + active_status=1 + content_hash); UPSERT `application_types`, `architecture_types`, `business_processes`, `companies` (INSERT OR IGNORE unique name values); UPSERT `app_uses_type`, `app_has_architecture`, `app_supports_process` edge rows; `UPDATE applications SET active_status=0 WHERE application_id NOT IN (current_run_id_list) AND active_status=1`; `INSERT INTO etl_runs (run_id, run_at, xlsx_hash, records_loaded, records_skipped, status, error_detail)`; `COMMIT`; on any exception: `ROLLBACK`, insert failed etl_runs row, re-raise; all SQL uses `?` placeholders only
- [X] T021 [P] [US1] Create `backend/graph/model.py` — `APP_GRAPH: nx.DiGraph = None` module singleton; `build_graph(db_path) → nx.DiGraph` (query active applications, business_processes, application_types, architecture_types from DB; add nodes with `type` attribute; add edges from app_supports_process, app_uses_type, app_has_architecture; return DiGraph); `reload_graph(db_path)` (rebuilds APP_GRAPH in place); `get_graph() → nx.DiGraph` (returns APP_GRAPH, raises if None)
- [X] T022 [US1] Create `backend/etl/embed.py` stub — `embed_changed_records(records: list[dict], db_path: str) → None` no-op implementation with a docstring specifying: collection name "applications", document text = `build_embed_payload(record)`, metadata fields = {application_type, business_process, baptist_managed}, excluded fields (PII list); comment: "Epic 3 implements this function"
- [X] T023 [US1] Create `backend/etl/__main__.py` — `argparse` parser with `--file` (required) argument; call `init_db` if `data/cmdb.db` not found; call `run_etl(args.file)`; print result counts and status to stdout; exit code 0 on success, 1 on failure; enables `python -m backend.etl.ingest --file <path>`
- [X] T024 [US1] Update `backend/main.py` lifespan — after `init_db()` call, attempt `reload_graph("data/cmdb.db")` on startup; catch and log if DB empty (graph_loaded stays false); expose `graph_loaded` state in `/api/health` response; update routes.py placeholder to use `get_graph()` dependency
- [ ] T025 [US1] Validate US1 end-to-end: run CLI against reference CMDB XLSX; run all checks in `quickstart.md` Scenarios 2–5; confirm: COUNT=1250, DISTINCT application_type ∈ {COTS, Homegrown, None}, no whitespace in names, etl_runs row exists with status='success', UUID stability on re-ingest, malformed XLSX rejected with DB count unchanged

**Checkpoint**: US1 complete — all 5 US1 acceptance scenarios pass. ETL is the single source of truth for `data/cmdb.db`.

---

## Phase 5: User Story 2 — User Browses and Views Application Details (P2)

**Goal**: Paginated, filterable Applications table in the browser with a 480px slide-in detail panel showing all 20 CMDB fields. Dashboard shows real portfolio metrics.

**Independent Test**: With data loaded, open `/applications` — table shows 1,250 rows across pages; COTS filter updates table immediately; click any name → panel opens with all 20 fields; NULL shows "Not specified"; Escape closes panel and returns focus. Dashboard shows correct counts and last-refresh timestamp.

- [X] T026 [P] [US2] Implement `GET /api/applications` in `backend/api/routes.py` — query params: `page` (default 1), `page_size` (default 50, max 200, 400 if out of range), `application_type`, `business_process`, `company`, `baptist_managed`, `q` (name LIKE `%q%`); build parameterized WHERE clause with `active_status=1`; return `{results:[], total:int, page:int, page_size:int, pages:int}`; list view omits description, all PII fields (business_owner, td_app_owner, primary_engineer, last_updated_by) from results for performance
- [X] T027 [P] [US2] Implement `GET /api/applications/{application_id}` in `backend/api/routes.py` — SELECT all 20 fields + application_id WHERE application_id=? AND active_status=1 with parameterized query; return full record as JSON (null values as JSON null); 404 with `{"detail": "Application not found: {id}"}` if not found
- [X] T028 [P] [US2] Create `frontend/src/components/MetricCard.tsx` — props: `label`, `value`, `subText`, `loading` (boolean); renders card with 3px gradient top bar (`linear-gradient(90deg, #1D3269, #00A8CC)` opacity 0.7), label (12px uppercase muted), value (42px weight 800 primary), subText (12.5px muted); `loading=true` shows skeleton div with `aria-hidden="true"` and pulse animation; 16px radius, 24px padding, border
- [X] T029 [P] [US2] Create `frontend/src/components/FilterBar.tsx` — props: `filters` (controlled state object), `onChange` (callback); renders: search input (320px, left 🔍 icon, right Cmd+K hint, `focus-visible` ring `0 0 0 3px rgba(0,168,204,0.12)`), 4 controlled `<select>` dropdowns (Business Process, Application Type, Baptist Managed, Company — each calls `onChange` immediately on change), active-filter badge (accent dot when any filter set), "✕ Clear filters" link (shows only when filter active), results count chip right-aligned; all `<select>` elements use native browser accessibility
- [X] T030 [P] [US2] Create `frontend/src/components/PaginationBar.tsx` — props: `page`, `pages`, `total`, `pageSize`, `onPageChange`, `onPageSizeChange`; renders "Showing {start}–{end} of {total} applications" left; page-size `<select>` (10/25/50 per page); right: Prev button (disabled on page 1), numbered page buttons (active: `#1D3269` bg/white; hover: surface bg + accent border), Next button; each button 32×32px, 7px radius
- [X] T031 [US2] Implement `frontend/src/surfaces/Applications.tsx` — fetch `/api/applications` with current filter params using `api/client.ts`; render `<FilterBar>` + scrollable table (`role="table"`) with 7 columns per contracts/ui.md (Application Name as `<button>` styled as teal link with `aria-label="View {name} details"`, Company with truncation, Type badge, Business Process with truncation, Baptist Managed badge, Business Owner with "Not specified" fallback, chevron); row hover bg; selected row bg; `<PaginationBar>` below; skeleton rows while loading; no results state
- [X] T032 [P] [US2] Create `frontend/src/components/DetailPanel.tsx` — 480px fixed panel right edge, full height; backdrop `rgba(15,23,42,0.40)` covering viewport; `slideIn` animation: `transform: translateX(100%) → translateX(0)` over 0.3s `cubic-bezier(0.16,1,0.3,1)`; `role="dialog"`, `aria-label="Application detail: {name}"`; focus trap (Tab/Shift+Tab cycles within panel, initial focus on close button); header: name (20px/700) + publisher subtitle + status pills (In Production, app type, business process); scrollable body: Overview section (Description styled box + Architecture Type + Application URL), Ownership section (2×3 grid with inner borders: Business Owner, T&D App Owner, Primary Engineer, Support Group, Company, Baptist Managed — "No" shows amber dot + `#B45309`; Last Updated full-width), Graph Relationships section (business process chip + type chip + relationship hint box); all null fields display "Not specified" (muted italic, never blank); footer: "🔍 Find similar apps" (accent full-width, disabled in Epic 1) + "📄 Open in CMDB" (secondary); close on: ✕ button click, Escape key, backdrop click — each calls `onClose` prop
- [X] T033 [US2] Wire DetailPanel into Applications.tsx — track `selectedAppId` in state; Application Name click → set `selectedAppId` + fetch `GET /api/applications/{id}` → pass record to `<DetailPanel>`; `onClose` → clear `selectedAppId` + return focus to the `<button>` that triggered open (use `useRef` to store trigger ref); backdrop renders only when panel is open
- [X] T034 [US2] Implement `frontend/src/surfaces/Dashboard.tsx` (full implementation replacing Phase 3 shell) — fetch `/api/applications?page_size=1` for total count; fetch `/api/applications?application_type=COTS&page_size=1` for COTS count; fetch `/api/applications?application_type=Homegrown&page_size=1` for Homegrown count; fetch `/api/refresh/status` for last-refresh timestamp; render 4 `<MetricCard>` components (Total Applications, COTS count, Homegrown count, Last Data Refresh); `loading=true` skeleton state during fetch; "Never" for timestamp if status is "never_run"
- [ ] T035 [US2] Validate US2 end-to-end: open `/applications` → confirm 1,250 total, COTS filter narrows immediately, Application Name links have aria-label; click 3D Scanner → panel opens with all 20 fields, NULL Architecture Type shows "Not specified" (not blank), press Escape → panel closes → focus on trigger; open `/` (Dashboard) → 4 metric cards with correct counts; run `quickstart.md` Scenarios 6 and 7

**Checkpoint**: US2 complete — all 5 US2 acceptance scenarios pass. Stakeholders can browse the full 1,250-app portfolio.

---

## Phase 6: User Story 3 — Operator Refreshes Data via Web Interface (P2)

**Goal**: Web-triggered ETL with real-time WebSocket progress, atomic failure handling, topbar status feedback, and a warning log for skipped records.

**Independent Test**: Click "Refresh Data" topbar button → inline panel opens; upload `.csv` → client rejects with "Only .xlsx files are accepted."; upload valid XLSX → spinner → WebSocket progress events → topbar shows "Updated · date · N apps" for 5s; upload malformed XLSX → failure message, DB unchanged. `quickstart.md` Scenario 8 passes.

- [X] T036 [P] [US3] Implement `POST /api/refresh` in `backend/api/routes.py` — accept `multipart/form-data` file; server-side extension check (.xlsx only → 400 otherwise); eager schema validation via `validate_schema()` (400 with {detail, missing_columns} if invalid); 409 if `ETL_RUNNING` module-level flag is True; set flag True; generate `run_id` UUID; return 202 `{run_id, status: "running", message: "…"}`; trigger `BackgroundTask(run_etl_background, tmp_file_path, run_id)`
- [X] T037 [P] [US3] Implement `GET /api/refresh/status` in `backend/api/routes.py` — SELECT latest row from etl_runs ORDER BY run_at DESC LIMIT 1; return fields: run_id, run_at, status, records_loaded, records_skipped, xlsx_hash; if table empty return all nulls + `status: "never_run"`
- [X] T038 [P] [US3] Implement WebSocket `WS /ws/refresh` in `backend/api/routes.py` — accept connection; read `run_id` from query params; look up or create `asyncio.Queue` keyed on run_id in a module-level dict; loop: `msg = await queue.get()` → send JSON text frame; break on `msg["type"] == "complete"`; close WebSocket; handle client disconnect gracefully
- [X] T039 [US3] Create `backend/api/background.py` — `ETL_RUNNING: bool = False`; `PROGRESS_QUEUES: dict[str, asyncio.Queue] = {}`; `run_etl_background(file_path, run_id)`: create Queue, register in PROGRESS_QUEUES, call `run_etl(file_path, progress_queue=queue)` (run_etl already emits progress/warning/complete events to queue), clear ETL_RUNNING flag on completion, delete queue from PROGRESS_QUEUES, delete tmp file; import and use this module in routes.py for T036/T038
- [X] T040 [US3] Create `frontend/src/components/RefreshForm.tsx` — triggered by Topbar "Refresh Data" button; renders inline panel (not modal, no `role="dialog"`); file `<input accept=".xlsx">`; client-side validation: `file.name.endsWith('.xlsx')` or show inline error "Only .xlsx files are accepted." and stop (no network request); on valid file: POST multipart to `/api/refresh` → get run_id → connect `WebSocket ws://localhost:8000/ws/refresh?run_id={run_id}`; while open: topbar shows spinner + "Refreshing…"; on progress event: optionally show step/count; on `complete` event (status='success'): call `onSuccess(completionData)`, show "Updated · {date} · {records_loaded} apps" for 5s then revert; on `complete` (status='failed'): show error message in `#EF4444` destructive color; WebSocket fallback: `onerror`/`onclose` → poll `GET /api/refresh/status` every 5s until status ≠ "running"; on skipped records: show amber chip "{records_skipped} records skipped — see ETL log"
- [X] T041 [US3] Wire RefreshForm into Topbar.tsx — add `showRefreshForm` boolean state and `onSuccess` callback prop to Topbar; "Refresh Data" button toggles `showRefreshForm`; render `<RefreshForm>` conditionally; `onSuccess` prop triggers parent's metric card reload (pass down from App.tsx as a callback that re-fetches Dashboard data)
- [ ] T042 [US3] Validate US3 end-to-end: run `quickstart.md` Scenario 8 (full upload flow, WebSocket events, 5-second success display, ETL failure leaves DB intact); verify: CSV upload rejected client-side, malformed XLSX returns 400 from server, valid XLSX triggers progress events, Dashboard "Last Data Refresh" updates after success, concurrent upload attempt returns 409

**Checkpoint**: US3 complete — all 6 US3 acceptance scenarios pass. Non-developer operators can refresh data via the browser.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, accessibility hardening, performance checks, security audit, and stub files for future epics.

- [ ] T043 Run all 20 acceptance criteria from `quickstart.md` (Scenarios 1–9) against reference CMDB XLSX; mark each AC in the traceability table; any failure blocks release
- [ ] T044 [P] Accessibility audit — keyboard-only walkthrough: tab through sidebar nav (visible focus rings `outline: 2px solid #00A8CC; outline-offset: 2px` on all nav items), Applications table (tab to filter dropdowns, search, table rows), DetailPanel focus trap (Tab cycles within panel, Shift+Tab reverses), RefreshForm file input and buttons; verify all interactive elements meet 44×44px touch target; verify `role="table"`, `scope="col"` on column headers, `aria-label` on Application Name links, `role="dialog"` on DetailPanel, `aria-hidden="true"` on skeleton loaders
- [ ] T045 [P] Performance spot-checks — time `python -m backend.etl.ingest --file ...` against reference XLSX (must complete < 5 min); `curl -w "%{time_total}" http://localhost:8000/api/applications` (must be < 3s); browser DevTools Network tab on `/applications` initial load (must render within 3s); WebSocket progress events must emit at least once during ETL (verify in Scenario 8)
- [ ] T046 [P] Security review — grep `backend/` for f-string SQL (`f"SELECT`, `.format(`); verify `.env` is in `.gitignore` and `git status` shows it untracked; verify `build_embed_payload()` in `backend/etl/embed.py` returns only `{application_name} {description}` with no PII fields; verify no hardcoded API keys anywhere in `backend/` or `frontend/`
- [X] T047 [P] Create stub files for future epics: `backend/graph/queries.py` (stub functions for Epic 2 redundancy and vendor analysis with TODO comments), `backend/agent/orchestrator.py` (Epic 4 stub — OpenAI agent class skeleton), `backend/agent/tools.py` (Epic 4 stub — `sql_analytics`, `graph_traversal`, `semantic_search` function signatures); ensures project structure is complete from day one

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup         — No deps, start immediately
Phase 2: Foundational  — Depends on Phase 1
Phase 3: US4           — Depends on Phase 2 (CRITICAL: needs FastAPI + frontend init)
Phase 4: US1           — Depends on Phase 2 (can run in parallel with Phase 3)
Phase 5: US2           — Depends on Phase 3 (shell) + Phase 4 (data)
Phase 6: US3           — Depends on Phase 4 (ETL) + Phase 5 (Topbar/Detail Panel exist)
Phase 7: Polish        — Depends on all story phases
```

### User Story Dependencies

| Story | Depends On | Rationale |
|-------|-----------|-----------|
| US4 (shell) | Phase 2 | FastAPI health + Vite frontend must exist |
| US1 (ETL) | Phase 2 | SQLite schema + connection must exist |
| US2 (browse) | US4 + US1 | Needs the app shell (nav, topbar) and loaded data |
| US3 (refresh) | US1 + US2 | ETL pipeline must exist; Topbar (from US2's wiring) must exist |

### Within Each User Story

Within each story phase, tasks run top-to-bottom with exceptions noted by [P]:

| Story | Parallel Start | Then Sequential |
|-------|---------------|----------------|
| US4 | T012 [P], T013 [P], T015 [P], T016 [P] in parallel | T014 (App.tsx router) → T017 (validate) |
| US1 | T018 [P] (normalize), T021 [P] (graph model) in parallel | T019 → T020 → T022 → T023 → T024 → T025 |
| US2 | T026 [P], T027 [P] (API routes), T028 [P], T029 [P], T030 [P], T032 [P] (components) in parallel | T031 (Applications surface) → T033 (wire panel) → T034 (Dashboard) → T035 (validate) |
| US3 | T036 [P], T037 [P], T038 [P] (API routes) in parallel | T039 → T040 → T041 → T042 (validate) |

---

## Parallel Execution Examples

### Parallel: Foundational Phase (Phase 2)

```text
Run simultaneously:
  Task T009: Create backend/main.py (FastAPI app + health route)
  Task T010: Create backend/api/routes.py stub + frontend/vite.config.ts

After T006, T007, T008 complete:
  Task T009 and T010 can both build on the existing DB infrastructure
```

### Parallel: US4 Components (Phase 3)

```text
Run simultaneously:
  Task T012: frontend/src/components/Sidebar.tsx
  Task T013: frontend/src/components/Topbar.tsx
  Task T015: frontend/src/surfaces/Query.tsx, Analytics.tsx, Redundancy.tsx shells
  Task T016: frontend/src/surfaces/Dashboard.tsx shell

After all [P] tasks complete:
  Task T014: frontend/src/App.tsx (imports all the above)
```

### Parallel: US1 ETL (Phase 4)

```text
Run simultaneously:
  Task T018: backend/etl/normalize.py
  Task T021: backend/graph/model.py

After T018 completes:
  Task T019: backend/etl/ingest.py (imports normalize.py)

After T019 completes:
  Task T020: backend/db/write_transaction.py
```

### Parallel: US2 Components (Phase 5)

```text
Run simultaneously:
  Task T026: GET /api/applications endpoint
  Task T027: GET /api/applications/{id} endpoint
  Task T028: frontend/src/components/MetricCard.tsx
  Task T029: frontend/src/components/FilterBar.tsx
  Task T030: frontend/src/components/PaginationBar.tsx
  Task T032: frontend/src/components/DetailPanel.tsx

After T026 + T029 + T030 complete:
  Task T031: frontend/src/surfaces/Applications.tsx

After T031 + T032 complete:
  Task T033: Wire DetailPanel into Applications.tsx
```

### Parallel: US3 API Routes (Phase 6)

```text
Run simultaneously:
  Task T036: POST /api/refresh
  Task T037: GET /api/refresh/status
  Task T038: WS /ws/refresh

After T036 + T038 complete:
  Task T039: backend/api/background.py (ETL queue wiring)
```

---

## Implementation Strategy

### MVP First (US4 + US1 Only — Story 1.1 + 1.6 in Epic)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks everything)
3. Complete Phase 3: US4 → health endpoint responds, navigation works
4. Complete Phase 4: US1 → 1,250 records loaded, CLI ETL works
5. **STOP and VALIDATE**: `quickstart.md` Scenarios 1–5 pass
6. This delivers standalone value: a queryable, populated database with a working app shell

### Incremental Delivery

1. Setup + Foundational → skeleton
2. US4 → working nav shell with design system ✓
3. US1 → data loaded, CLI ETL works ✓
4. US2 → browse table + detail panel, stakeholders can explore apps ✓ (demo ready)
5. US3 → web refresh, operators can keep data current ✓ (production ready for demo)

### Solo Developer Sequence

Single developer should follow task IDs in order, working within one phase before the next. Exceptions: within any phase, implement [P]-marked tasks before sequential dependencies.

---

## Summary

| Phase | Story | Tasks | Key Deliverable |
|-------|-------|-------|----------------|
| Phase 1 | — | T001–T005 | Project skeleton |
| Phase 2 | — | T006–T010 | DB schema, FastAPI skeleton, frontend init |
| Phase 3 | US4 | T011–T017 | Working app shell with glassmorphism nav |
| Phase 4 | US1 | T018–T025 | CLI ETL loading 1,250 records |
| Phase 5 | US2 | T026–T035 | Paginated browse table + detail panel + dashboard |
| Phase 6 | US3 | T036–T042 | Web-triggered refresh with WebSocket progress |
| Phase 7 | — | T043–T047 | Validation, accessibility, security, stubs |

**Total tasks**: 47
**Parallel opportunities identified**: 24 tasks marked [P]
**MVP scope**: Phases 1–4 (T001–T025) → working data pipeline with app shell

---

## Notes

- [P] tasks are in different files with no outstanding dependencies — a solo dev or parallel agents can implement them simultaneously
- [US1]/[US2]/[US3]/[US4] labels map each task to its user story for traceability to spec.md acceptance criteria
- Each user story phase is independently completable and testable — a team can build stories in parallel after Phase 2
- All SQL must use `?` placeholders — enforced in T007, T020, T026, T027 task descriptions
- `.env` must never be committed — enforced in T002 and audited in T046
- PII exclusion from embeddings is established in T018 (`build_embed_payload`) and audited in T046
- `quickstart.md` Scenarios map directly to acceptance criteria: each phase's validation task references the relevant scenario numbers
