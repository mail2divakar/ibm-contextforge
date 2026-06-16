# Quickstart Validation Guide: IT Knowledge Graph Ingestion Pipeline

**Feature**: Epic 1 — Platform Foundation
**Date**: 2026-06-12

This guide provides step-by-step instructions to validate that Epic 1 is working end-to-end. Each validation scenario maps directly to the acceptance criteria in `spec.md`.

---

## Prerequisites

| Requirement | Version | Check |
|-------------|---------|-------|
| Python | 3.10+ | `python --version` |
| Node.js | 18.x LTS | `node --version` |
| CMDB XLSX export | 20-column Baptist Health schema | File available locally |
| `.env` configured | `OPENAI_API_KEY` set (placeholder OK for Epic 1) | `cat .env` shows key |

---

## Setup (First Run)

```bash
# From project root: it-knowledge-graph/

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Node dependencies
cd frontend && npm install && cd ..

# 3. Initialize SQLite schema
python -m backend.db.init_schema
# Expected output: "Schema initialized at data/cmdb.db"

# 4. Run initial ETL
python -m backend.etl.ingest --file path/to/cmdb_export.xlsx
# Expected output:
#   Validating schema...
#   Normalizing 1,250 records...
#   Writing to SQLite (transaction)...
#   Reloading networkx graph...
#   SUCCESS: 1,250 records loaded. 0 skipped.

# 5. Start the backend (Terminal A)
uvicorn backend.main:app --reload --port 8000
# Expected: "Application startup complete."

# 6. Start the frontend (Terminal B)
cd frontend && npm run dev
# Expected: "Local: http://localhost:5173/"
```

---

## Validation Scenario 1: Dev Setup (AC-019, AC-020)

**What**: Confirm the local environment is running correctly with the design system in place.

```bash
# Check backend health
curl http://localhost:8000/api/health
```

**Expected response**:
```json
{"status": "ok", "graph_loaded": true, "db_path": "data/cmdb.db"}
```

**Browser check** — Open `http://localhost:5173`:
- [ ] Page loads without errors
- [ ] Left sidebar visible with glassmorphism background (`rgba(29,50,105,0.88)`, `blur(16px)`)
- [ ] 5 nav items visible: Dashboard, Query, Analytics, Redundancy Explorer, Applications
- [ ] Active nav item has left-border strip indicator
- [ ] Dashboard shows 4 metric cards with counts

**CSS token check** (browser DevTools → Computed → `:root`):
- [ ] `--color-primary: #1D3269` is defined
- [ ] `--color-accent: #00A8CC` is defined

---

## Validation Scenario 2: ETL Pipeline — Full Load (AC-001 through AC-004)

**What**: Confirm all 1,250 records are loaded and normalized correctly.

```bash
# Verify record count
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
count = conn.execute('SELECT COUNT(*) FROM applications WHERE active_status=1').fetchone()[0]
print(f'Active records: {count}')
assert count == 1250, f'Expected 1250, got {count}'
"
# Expected: "Active records: 1250"

# Verify application_type normalization
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
types = conn.execute('SELECT DISTINCT application_type FROM applications').fetchall()
print('application_type values:', [t[0] for t in types])
# Should only be: COTS, Homegrown, None
"

# Verify no whitespace in name field
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
bad = conn.execute(\"SELECT COUNT(*) FROM applications WHERE application_name != TRIM(application_name)\").fetchone()[0]
print(f'Records with whitespace in name: {bad}')
assert bad == 0
"

# Verify etl_runs recorded
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
run = conn.execute('SELECT status, records_loaded FROM etl_runs ORDER BY run_at DESC LIMIT 1').fetchone()
print(f'Latest ETL run: status={run[0]}, records={run[1]}')
"
```

---

## Validation Scenario 3: UUID Stability on Re-Ingest (AC-005)

**What**: Re-ingesting the same XLSX preserves all `application_id` values.

```bash
# Capture UUIDs before re-ingest
python -c "
import sqlite3, json
conn = sqlite3.connect('data/cmdb.db')
ids_before = {row[0]: row[1] for row in conn.execute('SELECT application_name, application_id FROM applications WHERE active_status=1')}
with open('/tmp/ids_before.json', 'w') as f:
    json.dump(ids_before, f)
print(f'Captured {len(ids_before)} UUIDs')
"

# Re-ingest the same XLSX
python -m backend.etl.ingest --file path/to/cmdb_export.xlsx

# Compare UUIDs after re-ingest
python -c "
import sqlite3, json
conn = sqlite3.connect('data/cmdb.db')
ids_after = {row[0]: row[1] for row in conn.execute('SELECT application_name, application_id FROM applications WHERE active_status=1')}
with open('/tmp/ids_before.json') as f:
    ids_before = json.load(f)
mismatches = [(k, ids_before[k], ids_after.get(k)) for k in ids_before if ids_before[k] != ids_after.get(k)]
print(f'UUID mismatches: {len(mismatches)}')
assert len(mismatches) == 0, f'Mismatches: {mismatches}'
print('All UUIDs preserved correctly.')
"
```

---

## Validation Scenario 4: Malformed XLSX Rejection (AC-006, AC-017)

**What**: A malformed XLSX is rejected without modifying the database.

```bash
# Record current count
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
count = conn.execute('SELECT COUNT(*) FROM applications WHERE active_status=1').fetchone()[0]
print(f'Before: {count} records')
"

# Create a malformed XLSX (missing required columns) using Python
python -c "
import pandas as pd
df = pd.DataFrame({'WrongColumn1': ['a'], 'WrongColumn2': ['b']})
df.to_excel('/tmp/bad_cmdb.xlsx', index=False)
print('Created malformed XLSX')
"

# Attempt to ingest the malformed file
python -m backend.etl.ingest --file /tmp/bad_cmdb.xlsx
# Expected: error output listing missing columns, exit code != 0

# Verify database unchanged
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
count = conn.execute('SELECT COUNT(*) FROM applications WHERE active_status=1').fetchone()[0]
print(f'After: {count} records (should be unchanged)')
"
```

---

## Validation Scenario 5: Soft Delete on Re-Ingest (AC-007)

**What**: Records absent from a new XLSX are marked inactive (not deleted).

```bash
# This test requires a modified XLSX with some records removed
# Use a copy with 5 fewer records for testing
python -c "
import pandas as pd
df = pd.read_excel('path/to/cmdb_export.xlsx')
df_minus_5 = df.iloc[5:]  # Remove first 5 records
df_minus_5.to_excel('/tmp/cmdb_minus5.xlsx', index=False)
print('Created test XLSX with 5 fewer records')
"

# Capture the first 5 application names
python -c "
import pandas as pd
df = pd.read_excel('path/to/cmdb_export.xlsx')
removed = df.iloc[:5]['Application Name'].tolist()
print('Removed names:', removed)
"

# Re-ingest the smaller XLSX
python -m backend.etl.ingest --file /tmp/cmdb_minus5.xlsx

# Verify soft-delete (active_status=0) for removed records
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
inactive = conn.execute(\"SELECT COUNT(*) FROM applications WHERE active_status=0\").fetchone()[0]
print(f'Inactive (soft-deleted) records: {inactive}')
assert inactive >= 5
"
```

---

## Validation Scenario 6: Applications Table UI (AC-009, AC-010)

**What**: The Applications surface renders correctly with filtering.

Open `http://localhost:5173/applications` in a browser.

**Manual checks**:
- [ ] Page shows "1,250 applications" (or current count) above the table
- [ ] Table has columns: Application Name, Company, Application Type, Business Process, Baptist Managed, Business Owner
- [ ] Application Name links are teal color
- [ ] Pagination controls visible; "1 of 25" (or similar)
- [ ] Filter bar visible with Application Type, Business Process, Company, Baptist Managed dropdowns

**Filter test**:
1. Select "COTS" in Application Type filter
2. Table updates immediately (no button click needed)
3. Active filter badge appears (e.g., "1 filter")
4. "Clear filters" link appears
5. All visible rows show "COTS" in Application Type column

**Search test**:
1. Type "scan" in the name search input
2. Table filters to show only applications containing "scan" (case-insensitive)

**API verification**:
```bash
curl "http://localhost:8000/api/applications?page=1&page_size=10&application_type=COTS"
# Expected: JSON with results array (all COTS), total count, page info
```

---

## Validation Scenario 7: Application Detail Panel (AC-011, AC-012, AC-013)

**What**: Clicking an application name opens a detail panel with all 20 fields.

1. On `/applications`, click any application name (teal link)
2. **Expected**: 480px panel slides in from the right edge, main content dims

**Manual checks**:
- [ ] Panel opens without page navigation
- [ ] All 20 field labels are visible (scroll if needed):
  - Application Name, Company, Publisher, Description, Updated, Last Updated By, Business Owner, T&D Application Owner, Primary Engineer, Application Support Group, Active, Install Status, Application URL, Application Portfolio Manager, Application Type, Architecture Type, Baptist Managed, Business Criticality, Business Process, Environment
- [ ] NULL fields show "Not specified" in muted gray color (not blank, not "null")
- [ ] "Find similar apps" button visible at bottom of panel
- [ ] Panel has correct ARIA attributes (open DevTools → Elements → inspect panel element):
  - `role="dialog"`
  - `aria-label="Application detail: [app name]"`

**Close behavior test**:
- Press Escape → panel closes, focus returns to the application name link that was clicked

**API verification**:
```bash
# Get an application_id from the list endpoint
APP_ID=$(curl -s "http://localhost:8000/api/applications?page_size=1" | python -c "import sys,json; print(json.load(sys.stdin)['results'][0]['application_id'])")
curl "http://localhost:8000/api/applications/$APP_ID"
# Expected: JSON with all 20 fields (null values as JSON null)
```

---

## Validation Scenario 8: Data Refresh via Web UI (AC-014, AC-015, AC-016)

**What**: The Refresh Data flow works end-to-end with a valid XLSX.

1. Click "Refresh Data" in the topbar (visible on all surfaces)
2. **Expected**: Inline panel opens (not a full modal)
3. Attempt to upload a `.csv` file:
   - **Expected**: "Only .xlsx files are accepted." error message appears
   - No spinner, no network request triggered
4. Upload the reference CMDB `.xlsx` file:
   - **Expected**: Spinner appears with "Refreshing…" in the topbar
5. Wait for ETL to complete:
   - **Expected**: Topbar shows "Updated · [date] · 1,250 apps" for ~5 seconds
   - Then reverts to "Refresh Data"
6. Navigate to Dashboard:
   - **Expected**: "Last Data Refresh" metric card shows the timestamp of the refresh just completed

**ETL failure test**:
```bash
# Simulate ETL failure by uploading bad file via API
curl -X POST http://localhost:8000/api/refresh \
  -F "file=@/tmp/bad_cmdb.xlsx"
# Expected: 400 with {"detail": "XLSX schema validation failed", "missing_columns": [...]}
```

**WebSocket test**:
```python
# Run this in a Python terminal while uploading a valid XLSX
import asyncio, websockets, json

async def watch_progress():
    # First trigger a refresh to get a run_id
    import httpx
    with open('path/to/cmdb_export.xlsx', 'rb') as f:
        r = httpx.post('http://localhost:8000/api/refresh', files={'file': f})
    run_id = r.json()['run_id']
    
    async with websockets.connect(f'ws://localhost:8000/ws/refresh?run_id={run_id}') as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"[{data['type']}] {data.get('message', data)}")
            if data['type'] == 'complete':
                break

asyncio.run(watch_progress())
```

---

## Validation Scenario 9: Database Schema Integrity (AC-008, AC-018)

**What**: All tables exist with correct schema and foreign key integrity.

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/cmdb.db')
conn.execute('PRAGMA foreign_keys = ON')

# Check all tables exist
tables = {row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()}
required = {'applications', 'application_types', 'architecture_types', 'business_processes',
            'companies', 'app_uses_type', 'app_has_architecture', 'app_supports_process', 'etl_runs'}
missing = required - tables
assert not missing, f'Missing tables: {missing}'
print('All required tables present:', required)

# Check foreign key integrity
violations = conn.execute('PRAGMA foreign_key_check').fetchall()
assert not violations, f'FK violations: {violations}'
print('Foreign key integrity: OK')

# Check WAL mode is enabled
mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
assert mode == 'wal', f'Expected WAL, got {mode}'
print(f'Journal mode: {mode}')

# Check etl_runs has at least one entry
run_count = conn.execute('SELECT COUNT(*) FROM etl_runs').fetchone()[0]
print(f'ETL runs recorded: {run_count}')
assert run_count >= 1
"
```

---

## Acceptance Criteria Traceability

| AC ID | Validation Scenario | Status |
|-------|---------------------|--------|
| AC-001 | Scenario 2 — count = 1,250 | ☐ |
| AC-002 | Scenario 2 — application_type values | ☐ |
| AC-003 | Scenario 2 — whitespace check | ☐ |
| AC-004 | Scenario 2 — baptist_managed normalization | ☐ |
| AC-005 | Scenario 3 — UUID stability | ☐ |
| AC-006 | Scenario 4 — malformed XLSX rejection | ☐ |
| AC-007 | Scenario 5 — soft delete | ☐ |
| AC-008 | Scenario 9 — schema + FK integrity | ☐ |
| AC-009 | Scenario 6 — Applications table count | ☐ |
| AC-010 | Scenario 6 — filter updates table | ☐ |
| AC-011 | Scenario 7 — all 20 fields in panel | ☐ |
| AC-012 | Scenario 7 — NULL → "Not specified" | ☐ |
| AC-013 | Scenario 7 — Escape closes panel, focus returns | ☐ |
| AC-014 | Scenario 8 — non-.xlsx rejected | ☐ |
| AC-015 | Scenario 8 — WebSocket progress visible | ☐ |
| AC-016 | Scenario 8 — Dashboard timestamp updates | ☐ |
| AC-017 | Scenario 4 — DB unchanged after ETL failure | ☐ |
| AC-018 | Scenario 9 — etl_runs recorded | ☐ |
| AC-019 | Scenario 1 — localhost:5173 + :8000/health respond | ☐ |
| AC-020 | Scenario 1 — sidebar glassmorphism styling | ☐ |
