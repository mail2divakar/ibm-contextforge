# API Contract: IT Knowledge Graph Ingestion Pipeline

**Feature**: Epic 1 — Platform Foundation
**Date**: 2026-06-12
**Base URL**: `http://localhost:8000`
**Authentication**: None (MVP — internal localhost deployment)
**Content-Type**: `application/json` (unless noted)

---

## Endpoints

### GET /api/health

Dev setup validation. Returns 200 if the server is running.

**Response 200**
```json
{
  "status": "ok",
  "graph_loaded": true,
  "db_path": "data/cmdb.db"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Always `"ok"` when server is healthy |
| `graph_loaded` | boolean | True if networkx graph loaded successfully at startup |
| `db_path` | string | Path to the SQLite database file |

---

### GET /api/applications

Returns a paginated, optionally filtered list of active applications.

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No (default: 1) | Page number (1-indexed) |
| `page_size` | integer | No (default: 50, max: 200) | Results per page |
| `application_type` | string | No | Filter: `COTS` \| `Homegrown` |
| `business_process` | string | No | Filter by business process name (exact match) |
| `company` | string | No | Filter by company name (exact match) |
| `baptist_managed` | boolean | No | Filter: `true` \| `false` |
| `q` | string | No | Name substring search (case-insensitive) |

**Response 200**
```json
{
  "results": [
    {
      "application_id": "550e8400-e29b-41d4-a716-446655440000",
      "application_name": "3D Scanner",
      "company": "Baptist Hospital",
      "publisher": "Varian Medical Systems",
      "application_type": "COTS",
      "architecture_type": "Client Server",
      "baptist_managed": true,
      "business_process": "Radiation Oncology",
      "business_owner": "Alonso Gutierrez",
      "install_status": "Installed",
      "active_status": 1
    }
  ],
  "total": 1250,
  "page": 1,
  "page_size": 50,
  "pages": 25
}
```

**Result item fields** (subset — excludes PII and long fields for list view):

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `application_id` | string (UUID) | No | Stable identifier |
| `application_name` | string | No | Application name |
| `company` | string | Yes | Baptist Health entity |
| `publisher` | string | Yes | Software vendor |
| `application_type` | string | Yes | `COTS` \| `Homegrown` \| null |
| `architecture_type` | string | Yes | Deployment pattern |
| `baptist_managed` | boolean | Yes | Managed by Baptist (true/false/null) |
| `business_process` | string | Yes | Primary business process |
| `business_owner` | string | Yes | Business Owner name |
| `install_status` | string | Yes | Installation status |
| `active_status` | integer | No | Always 1 in list view (inactive excluded) |

**Response 400** — Invalid query parameter
```json
{"detail": "page_size must be between 1 and 200"}
```

---

### GET /api/applications/{application_id}

Returns the full 20-field CMDB record for a single application.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `application_id` | string (UUID) | The application's stable UUID |

**Response 200** — Full 20-field application record
```json
{
  "application_id": "550e8400-e29b-41d4-a716-446655440000",
  "application_name": "3D Scanner",
  "company": "Baptist Hospital",
  "publisher": "Varian Medical Systems",
  "description": "3D volumetric imaging for radiation therapy planning",
  "updated": "2026-05-15",
  "last_updated_by": "Jane Smith",
  "business_owner": "Alonso Gutierrez",
  "td_app_owner": "Chakri Ramaswamy",
  "primary_engineer": "John Doe",
  "support_group": "Radiation Oncology IT",
  "active": 1,
  "install_status": "Installed",
  "application_url": "https://3dscanner.baptisthealth.net",
  "portfolio_manager": "Maria Lopez",
  "application_type": "COTS",
  "architecture_type": "Client Server",
  "baptist_managed": true,
  "business_criticality": "High",
  "business_process": "Radiation Oncology",
  "environment": "Production",
  "active_status": 1
}
```

All 20 CMDB fields are returned. NULL fields are returned as JSON `null` — the UI renders these as "Not specified".

**Response 404** — Application not found
```json
{"detail": "Application not found: 550e8400-e29b-41d4-a716-446655440000"}
```

---

### POST /api/refresh

Accepts a CMDB XLSX file upload and triggers the ETL pipeline as a background task.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | CMDB XLSX file (.xlsx only) |

**Response 202** — Accepted; ETL running in background
```json
{
  "run_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "running",
  "message": "ETL pipeline started. Connect to /ws/refresh?run_id=<run_id> for progress."
}
```

**Response 400** — Invalid file type
```json
{"detail": "Only .xlsx files are accepted. Received: application/pdf"}
```

**Response 400** — XLSX schema validation failure (detected synchronously before background task)
```json
{
  "detail": "XLSX schema validation failed",
  "missing_columns": ["Business Owner", "Baptist Managed"]
}
```

**Response 409** — ETL already running
```json
{"detail": "An ETL run is already in progress. Wait for completion before uploading a new file."}
```

---

### GET /api/refresh/status

Returns the status of the most recent ETL run.

**Response 200**
```json
{
  "run_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "run_at": "2026-06-12T17:30:00Z",
  "status": "success",
  "records_loaded": 1250,
  "records_skipped": 3,
  "xlsx_hash": "a3f4b2c1..."
}
```

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `run_id` | string (UUID) | No | Identifier of the most recent run |
| `run_at` | string (ISO 8601) | No | Timestamp of run start |
| `status` | string | No | `success` \| `partial` \| `failed` \| `running` |
| `records_loaded` | integer | Yes | Count of successfully loaded records |
| `records_skipped` | integer | Yes | Count of records that failed to load |
| `xlsx_hash` | string | Yes | SHA-256 of the uploaded file |

**Response 200** — No ETL runs yet
```json
{
  "run_id": null,
  "run_at": null,
  "status": "never_run",
  "records_loaded": null,
  "records_skipped": null,
  "xlsx_hash": null
}
```

---

## WebSocket

### WS /ws/refresh

Real-time ETL progress stream. Connect immediately after receiving a 202 from `POST /api/refresh`.

**Connection URL**: `ws://localhost:8000/ws/refresh?run_id=<run_id>`

**Query Parameters**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | string (UUID) | Yes | The run_id returned by POST /api/refresh |

**Message Types** (all messages are JSON text frames)

#### Progress event
Emitted periodically during ETL execution.
```json
{
  "type": "progress",
  "step": "normalizing",
  "records_processed": 450,
  "records_total": 1250,
  "message": "Normalizing fields — 450/1,250 records"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"progress"` |
| `step` | string | `"reading"` \| `"normalizing"` \| `"writing"` \| `"indexing"` |
| `records_processed` | integer | Records processed so far in this step |
| `records_total` | integer | Total records in the XLSX |
| `message` | string | Human-readable progress description |

#### Warning event
Emitted when a record is skipped during normalization or write.
```json
{
  "type": "warning",
  "application_name": "Unnamed App",
  "company": "Baptist Hospital",
  "reason": "application_type value 'Unknown Software' stored as NULL"
}
```

#### Completion event (success)
Emitted when ETL completes successfully. Connection closes after this message.
```json
{
  "type": "complete",
  "status": "success",
  "records_loaded": 1250,
  "records_skipped": 3,
  "timestamp": "2026-06-12T17:35:22Z",
  "message": "Updated · Jun 12, 2026 · 1,250 apps"
}
```

#### Completion event (failure)
Emitted when ETL fails. Connection closes after this message.
```json
{
  "type": "complete",
  "status": "failed",
  "records_loaded": 0,
  "records_skipped": 0,
  "timestamp": "2026-06-12T17:35:05Z",
  "error": "Transaction rolled back — prior data preserved",
  "message": "Refresh failed — check the file format."
}
```

**Client fallback**: If the WebSocket connection drops, poll `GET /api/refresh/status` at 5-second intervals until `status` is no longer `"running"`.

---

## Error Response Format

All error responses use this shape:

```json
{
  "detail": "Human-readable error description"
}
```

For validation errors with multiple issues:
```json
{
  "detail": "Validation failed",
  "errors": [
    {"field": "file", "message": "Only .xlsx files are accepted."},
    {"field": "page", "message": "Must be a positive integer."}
  ]
}
```

---

## HTTP Status Codes

| Code | When Used |
|------|-----------|
| 200 | Successful GET |
| 202 | ETL background task accepted |
| 400 | Invalid request (bad parameters, wrong file type, schema validation failure) |
| 404 | Resource not found |
| 409 | Conflict (ETL already running) |
| 500 | Unexpected server error |

---

## CORS Configuration (Development)

In development mode, FastAPI allows requests from `http://localhost:5173` (Vite dev server).

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

In production build mode, React is served as static files from FastAPI — no CORS needed.

---

## Vite Proxy Configuration (Development)

`frontend/vite.config.ts` proxies all `/api/*` and `/ws/*` requests to the FastAPI backend:

```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true,
    },
  },
}
```

---

## Future Endpoints (Not in Epic 1)

These endpoints are planned for later epics and should be considered when designing the route structure:

| Method | Path | Epic | Purpose |
|--------|------|------|---------|
| `GET` | `/api/analytics/distributions` | 2 | 5 pre-built distribution queries |
| `GET` | `/api/analytics/redundancy` | 2 | Redundancy cluster list |
| `GET` | `/api/analytics/redundancy/export` | 2 | CSV export of redundancy clusters |
| `GET` | `/api/analytics/vendor-concentration` | 2 | Vendor concentration analysis |
| `GET` | `/api/search` | 3 | Semantic search (ChromaDB) |
| `POST` | `/api/query` | 4 | Submit NL query to agent |
