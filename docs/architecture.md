---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - docs/planning-artifacts/briefs/brief-BMAD-WorkSpace-2026-06-12/brief.md
  - docs/planning-artifacts/prds/prd-BMAD-WorkSpace-2026-06-12/prd.md
  - docs/planning-artifacts/ux-designs/ux-BMAD-WorkSpace-2026-06-12/DESIGN.md
  - docs/planning-artifacts/ux-designs/ux-BMAD-WorkSpace-2026-06-12/EXPERIENCE.md
workflowType: 'architecture'
project_name: 'IT Application Knowledge Graph — Agentic Intelligence Platform'
user_name: 'uday kumar'
date: '2026-06-12'
status: final
notes: 'draw.io diagrams included as XML in dedicated section'
---

# Architecture: IT Application Knowledge Graph — Agentic Intelligence Platform

**Project:** Baptist Health South Florida — KSquare Group  
**Date:** 2026-06-12  
**Owner:** Uday Kumar  
**Acceptance:** Chakri (T&D)

---

## 1. Architecture Summary

The platform is a four-layer, single-host Python + React web application. It has no cloud infrastructure dependencies at runtime. All persistence (relational data, vector embeddings) lives in SQLite files on the deployment machine. The OpenAI API is the only external network dependency.

**Four layers:**

| Layer | Technology | Purpose |
|---|---|---|
| ETL & Data Store | Python (pandas, openpyxl, sqlite3), SQLite | Ingest CMDB XLSX, normalize, persist |
| Graph & Analytics | Python networkx + SQLite | Relationship traversal, redundancy clusters, distribution analytics |
| Semantic Search | sentence-transformers + ChromaDB (SQLite) | Vector similarity search over app names and descriptions |
| Agentic Q&A + UI | OpenAI gpt-4o, FastAPI, React JS 18 | NL query routing, response assembly, browser interface |

**Key constraints driving every decision:**
- Local machine deployment only (MVP demo)
- 1,250 records — no distributed scale required
- No authentication in v1 (confirmed safe: internal network only)
- `.env` for OpenAI API key — never committed to version control
- PII fields (owner names) excluded from all OpenAI and ChromaDB payloads

---

## 2. Component Inventory

### 2.1 Backend Components

| Component | Technology | Role | Port / Path |
|---|---|---|---|
| ETL Pipeline | Python 3.10+, pandas 2.x, openpyxl | Reads XLSX → normalizes → writes SQLite + ChromaDB | CLI / triggered by API |
| SQLite Database | SQLite 3 (stdlib) | Primary relational store: apps, types, processes, edges | `data/cmdb.db` |
| ChromaDB | chromadb 0.4.x+ (SQLite-backed) | Vector store for app embeddings | `data/chroma/` |
| Embedding Model | sentence-transformers, all-MiniLM-L6-v2 | CPU embedding generation at ETL time | In-process |
| Graph Engine | Python networkx 3.x | In-memory graph loaded from SQLite; traversal queries | In-process |
| Agent Orchestrator | OpenAI Python SDK, gpt-4o | Tool-calling NL router: SQL / graph / semantic | In-process |
| API Server | FastAPI + uvicorn | REST + WebSocket backend for React frontend | `localhost:8000` |

### 2.2 Frontend Components

| Component | Technology | Role |
|---|---|---|
| React App | React JS 18.x, Vite | SPA: 5 surfaces, sidebar nav, detail panel overlay |
| Dashboard | React | Metric cards + distribution charts |
| Query Surface | React | NL input, agent result table, conversation history |
| Analytics Surface | React | 5 pre-built distribution views with drill-down |
| Redundancy Explorer | React | Cluster cards, CSV export |
| Applications Table | React | Searchable, filterable full app index |
| Detail Panel | React | 480px slide-in overlay, all 20 CMDB fields |

### 2.3 External Dependencies

| Dependency | Type | Notes |
|---|---|---|
| OpenAI API (gpt-4o) | External HTTPS | Only external runtime dependency. Requires `OPENAI_API_KEY` in `.env`. Platform degrades gracefully if unreachable — SQL and semantic search remain available. |
| CMDB XLSX export | Data input | Baptist Health ServiceNow 20-column schema. Manual upload only (v1). |

---

## 3. SQLite Schema

### 3.1 Node Tables

```sql
CREATE TABLE applications (
    application_id   TEXT PRIMARY KEY,        -- UUID v4, stable across re-ingests
    application_name TEXT NOT NULL,
    company          TEXT,
    publisher        TEXT,
    description      TEXT,
    updated          TEXT,
    last_updated_by  TEXT,
    business_owner   TEXT,
    td_app_owner     TEXT,
    primary_engineer TEXT,
    support_group    TEXT,
    active           INTEGER DEFAULT 1,
    install_status   TEXT,
    application_url  TEXT,
    portfolio_manager TEXT,
    application_type TEXT,                    -- 'COTS' | 'Homegrown' | NULL
    architecture_type TEXT,
    baptist_managed  INTEGER,                 -- 0 | 1 | NULL
    business_criticality TEXT,
    business_process TEXT,
    environment      TEXT,
    active_status    INTEGER DEFAULT 1        -- 0 = marked inactive on refresh
);

CREATE TABLE application_types (
    type_id   TEXT PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE            -- 'COTS' | 'Homegrown'
);

CREATE TABLE architecture_types (
    arch_id   TEXT PRIMARY KEY,
    arch_name TEXT NOT NULL UNIQUE            -- 'Client Server' | 'Platform Host' | 'Web Based' | 'N-Tier' | 'Other'
);

CREATE TABLE business_processes (
    process_id   TEXT PRIMARY KEY,
    process_name TEXT NOT NULL UNIQUE
);

CREATE TABLE companies (
    company_id   TEXT PRIMARY KEY,
    company_name TEXT NOT NULL UNIQUE
);
```

### 3.2 Edge Tables (Graph Layer)

```sql
CREATE TABLE app_uses_type (
    application_id TEXT REFERENCES applications(application_id),
    type_id        TEXT REFERENCES application_types(type_id),
    PRIMARY KEY (application_id, type_id)
);

CREATE TABLE app_has_architecture (
    application_id TEXT REFERENCES applications(application_id),
    arch_id        TEXT REFERENCES architecture_types(arch_id),
    PRIMARY KEY (application_id, arch_id)
);

CREATE TABLE app_supports_process (
    application_id TEXT REFERENCES applications(application_id),
    process_id     TEXT REFERENCES business_processes(process_id),
    PRIMARY KEY (application_id, process_id)
);
```

### 3.3 ETL State Table

```sql
CREATE TABLE etl_runs (
    run_id     TEXT PRIMARY KEY,
    run_at     TEXT NOT NULL,               -- ISO 8601
    xlsx_hash  TEXT,                        -- SHA-256 of uploaded file
    records_loaded INTEGER,
    records_skipped INTEGER,
    status     TEXT                         -- 'success' | 'partial' | 'failed'
);
```

---

## 4. Data Flow

### 4.1 ETL Flow (Ingest Path)

```
Operator uploads CMDB XLSX via web UI or CLI
    │
    ▼
FastAPI /api/refresh endpoint receives file
    │
    ▼
ETL Pipeline (Python)
    ├── Read XLSX (pandas + openpyxl)
    ├── Validate schema: 20 required columns present
    ├── Normalize fields:
    │       application_type → 'COTS' | 'Homegrown' | NULL
    │       baptist_managed  → 0 | 1 | NULL
    │       strings          → strip whitespace
    ├── Generate/preserve UUIDs (key: application_name + company)
    ├── Write to SQLite (transaction — no partial writes)
    │       applications, node tables, edge tables
    │       Mark absent records inactive (not deleted)
    │       Log skipped records to etl_runs
    ├── Generate embeddings (sentence-transformers, CPU)
    │       Input: application_name + " " + description only
    │       PII fields (owner names, URLs) EXCLUDED
    │       Regenerate only for changed records
    └── Upsert to ChromaDB collection
            document_id = application_id
            metadata = {application_type, business_process, baptist_managed}
```

### 4.2 Query Flow (Read Path)

```
User types NL query in React Query surface
    │
    ▼
POST /api/query  {text: "...", conversation_id: "..."}
    │
    ▼
Agent Orchestrator (OpenAI gpt-4o, function-calling)
    │
    ├── Tool: sql_analytics(query_type, filters)
    │       → SQLite GROUP BY / COUNT queries
    │       → Returns structured JSON result set
    │
    ├── Tool: graph_traversal(start_node, relationship, filters)
    │       → networkx graph (loaded once from SQLite, cached in memory)
    │       → Returns node list + traversal path citation
    │
    └── Tool: semantic_search(query_text, top_k, filters)
            → sentence-transformers embed query (CPU, <100ms)
            → ChromaDB .query() top-k results
            → Returns ranked app list + similarity scores
    │
    ▼
Agent assembles response:
    direct answer + evidence table + source citation
    PII fields included in response (displayed in UI, not in OpenAI prompt)
    │
    ▼
FastAPI streams response → React renders result table
    Application Name links → detail panel (GET /api/applications/{id})
```

### 4.3 Graph Traversal Detail

```
SQLite edge tables loaded into networkx DiGraph at server startup
(and reloaded after each ETL refresh)

Nodes:  applications, business_processes, application_types, companies
Edges:  app_supports_process, app_uses_type, app_has_architecture

Redundancy cluster query:
    GROUP nodes by shared business_process node
    Return subgraphs where cluster_size >= 2
    Rank by cluster_size DESC

Vendor concentration query:
    GROUP applications by publisher attribute
    Return publishers where count >= 3
    Rank by count DESC

Multi-hop example ("Baptist-managed apps in Imaging"):
    Filter: applications WHERE baptist_managed = 1
    Traverse: app_supports_process → business_process WHERE name = 'Imaging'
    Return: intersection
```

---

## 5. API Contract (FastAPI)

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/query` | Submit NL query to agent | None (MVP) |
| `GET` | `/api/applications` | List all apps (paginated, filtered) | None |
| `GET` | `/api/applications/{id}` | Full CMDB record for one application | None |
| `GET` | `/api/analytics/distributions` | All 5 pre-built distribution queries | None |
| `GET` | `/api/analytics/redundancy` | Redundancy cluster list | None |
| `GET` | `/api/analytics/redundancy/export` | CSV export of all clusters | None |
| `POST` | `/api/refresh` | Trigger ETL pipeline (XLSX upload) | None |
| `GET` | `/api/refresh/status` | Last ETL run status + timestamp | None |
| `WebSocket` | `/ws/refresh` | Real-time ETL progress stream | None |

**Query payload:**
```json
{
  "text": "Which applications support Radiation Oncology?",
  "conversation_id": "uuid-session",
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**Query response:**
```json
{
  "answer": "88 applications support Radiation Oncology.",
  "results": [
    {
      "application_id": "uuid",
      "application_name": "3D Scanner",
      "business_process": "Radiation Oncology",
      "application_type": "COTS",
      "baptist_managed": true,
      "business_owner": "Alonso Gutierrez",
      "similarity_score": 0.91
    }
  ],
  "citation": "Semantic Search + SQL filter · 88 results · 1.4s",
  "tool_used": "semantic_search",
  "processing_ms": 1400
}
```

---

## 6. Deployment Topology

**Target: Single developer laptop / workstation**

```
┌─────────────────────────────────────────────────────────┐
│                  Local Machine (Windows/macOS)           │
│                                                         │
│   ┌─────────────────┐     ┌──────────────────────────┐  │
│   │  React SPA       │     │  FastAPI + uvicorn        │  │
│   │  (Vite dev /     │────▶│  localhost:8000           │  │
│   │   static build)  │     │                          │  │
│   │  localhost:5173  │     │  ┌────────────────────┐  │  │
│   └─────────────────┘     │  │ Agent Orchestrator  │  │  │
│                            │  │ networkx Graph      │  │  │
│                            │  │ ETL Pipeline        │  │  │
│                            │  └────────────────────┘  │  │
│                            │           │               │  │
│                            │  ┌────────┴─────────┐    │  │
│                            │  │  data/cmdb.db     │    │  │
│                            │  │  data/chroma/     │    │  │
│                            │  └──────────────────┘    │  │
│                            └──────────────────────────┘  │
│                                        │                  │
│                                        ▼ HTTPS            │
│                              ┌─────────────────┐         │
│                              │  OpenAI API      │         │
│                              │  api.openai.com  │         │
│                              └─────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

**Project directory layout:**

```
it-knowledge-graph/
├── .env                    ← OPENAI_API_KEY (NEVER commit)
├── .gitignore              ← .env, data/, __pycache__/, node_modules/
├── backend/
│   ├── main.py             ← FastAPI app entry point
│   ├── etl/
│   │   ├── ingest.py       ← XLSX → SQLite
│   │   ├── normalize.py    ← Field normalization
│   │   └── embed.py        ← sentence-transformers → ChromaDB
│   ├── graph/
│   │   ├── model.py        ← networkx graph builder from SQLite
│   │   └── queries.py      ← Redundancy, vendor concentration, traversal
│   ├── agent/
│   │   ├── orchestrator.py ← OpenAI function-calling agent
│   │   └── tools.py        ← sql_analytics, graph_traversal, semantic_search
│   ├── api/
│   │   └── routes.py       ← FastAPI route handlers
│   └── db/
│       ├── schema.sql      ← SQLite DDL
│       └── connection.py   ← SQLite connection pool
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── surfaces/       ← Dashboard, Query, Analytics, Redundancy, Applications
│   │   ├── components/     ← Sidebar, DetailPanel, MetricCard, AgentResult, etc.
│   │   └── api/            ← Typed API client
│   └── vite.config.ts
├── data/                   ← Runtime data (gitignored)
│   ├── cmdb.db
│   └── chroma/
└── requirements.txt
```

---

## 7. Agent Tool Definitions (OpenAI Function Calling)

```python
tools = [
    {
        "name": "sql_analytics",
        "description": "Run structured analytics queries against the SQLite CMDB database. Use for counting, grouping, distribution, and filter questions.",
        "parameters": {
            "query_type": "string",  # "distribution" | "filter" | "redundancy" | "vendor_concentration"
            "filters": "object"      # {business_process, application_type, baptist_managed, company}
        }
    },
    {
        "name": "graph_traversal",
        "description": "Traverse the application relationship graph using networkx. Use for multi-hop questions: which apps share a vendor, which processes have the most overlap, etc.",
        "parameters": {
            "traversal_type": "string",  # "redundancy_clusters" | "vendor_concentration" | "process_apps" | "multi_hop"
            "filters": "object"
        }
    },
    {
        "name": "semantic_search",
        "description": "Search for applications by semantic similarity to a description. Use for 'do we have X?' or 'find something like Y' questions.",
        "parameters": {
            "query_text": "string",
            "top_k": "integer",     # default 10
            "filters": "object"     # {business_process, application_type, baptist_managed}
        }
    }
]
```

**Routing rules (baked into system prompt):**
- Counting / distribution → `sql_analytics`
- Relationship / multi-hop → `graph_traversal`
- Capability match / "do we have" → `semantic_search`
- Compound queries → multiple tool calls in sequence

**PII fence (system prompt constraint):**
> "You have access to application metadata. When building tool call arguments, NEVER include owner names, engineer names, or URLs in the query text or filter values. These fields are only displayed to the user after retrieval — they must not be sent in search queries."

---

## 8. Non-Functional Architecture Decisions

| Concern | Decision | Rationale |
|---|---|---|
| **No auth (MVP)** | No login, no session tokens | Local machine only; network boundary is the security layer. Must be added before any shared/networked deployment. |
| **No partial writes** | ETL wrapped in SQLite transaction; rollback on any error | Preserves prior data state on malformed XLSX upload (FR-4) |
| **Graph in-memory** | networkx graph loaded at startup, refreshed after ETL | 1,250 nodes — full graph fits in <10MB RAM. No query latency from DB joins. |
| **Graceful OpenAI degradation** | SQL analytics and semantic search remain available when OpenAI unreachable | Agent offline banner in UI; NL input disabled; analytics/search surfaces unaffected |
| **Embeddings CPU-only** | all-MiniLM-L6-v2 on CPU | 1,250 records embeds in <5 min on any laptop CPU. No GPU dependency. |
| **Incremental re-embed** | Re-embed only records whose name or description changed | Avoids full re-embed on every refresh (only delta changes) |
| **Conversation context in-memory** | Session history held in FastAPI memory per `conversation_id` | No DB writes for chat history; resets on server restart (A-6) |
| **SQLite WAL mode** | `PRAGMA journal_mode=WAL` | Allows concurrent reads during ETL write |

---

## 9. Security & Data Governance Decisions

| Decision | Implementation |
|---|---|
| OpenAI API key | `.env` file only. `OPENAI_API_KEY=sk-...`. `.env` in `.gitignore`. Never in code. |
| PII exclusion from OpenAI | ETL embed input: `name + description` only. Agent system prompt: explicit PII fence. Owner/engineer fields retrieved after query, not sent as query parameters. |
| PII exclusion from ChromaDB | Metadata fields stored: `application_type`, `business_process`, `baptist_managed` only. No names. |
| Data residency | All data on local machine. Only transient OpenAI API calls leave the host. |
| No write-back | Platform is read-only. No ServiceNow API calls. No CMDB mutations. |

---

## 10. Technology Versions

| Technology | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.11 recommended for performance |
| FastAPI | 0.110+ | |
| uvicorn | 0.29+ | |
| pandas | 2.x | XLSX read |
| openpyxl | 3.x | XLSX engine for pandas |
| networkx | 3.x | Graph traversal |
| sentence-transformers | 2.x | all-MiniLM-L6-v2 |
| chromadb | 0.4.x+ | SQLite-backed persistence |
| openai (Python SDK) | 1.x | gpt-4o, function calling |
| SQLite | 3.35+ (stdlib) | WAL mode, JSON functions |
| React JS | 18.x | |
| Vite | 5.x | Frontend build |
| Node.js | 18.x LTS | Build toolchain only |

---

## 11. Draw.io Architecture Diagrams

The following XML blocks can be imported directly into draw.io (app.diagrams.net):  
**File → Import From → Device** and paste the XML content.

---

### Diagram 1 — System Overview (4-Layer Architecture)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="IT Application Knowledge Graph — System Architecture" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;fontColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="184" y="20" width="800" height="40" as="geometry" />
    </mxCell>

    <!-- Layer 4: UI -->
    <mxCell id="layer4_bg" value="Layer 4 — React JS Frontend" style="swimlane;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontStyle=1;fontSize=12;startSize=30;" vertex="1" parent="1">
      <mxGeometry x="40" y="80" width="1080" height="120" as="geometry" />
    </mxCell>
    <mxCell id="react_dashboard" value="Dashboard" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="layer4_bg">
      <mxGeometry x="20" y="50" width="120" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_query" value="Query Surface" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00A8CC;strokeColor=#007A99;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="layer4_bg">
      <mxGeometry x="160" y="50" width="120" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_analytics" value="Analytics" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="layer4_bg">
      <mxGeometry x="300" y="50" width="120" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_redundancy" value="Redundancy Explorer" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="layer4_bg">
      <mxGeometry x="440" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_apps" value="Applications Table" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="layer4_bg">
      <mxGeometry x="600" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_detail" value="Detail Panel (overlay)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;dashed=1;" vertex="1" parent="layer4_bg">
      <mxGeometry x="760" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="react_note" value="React JS 18 · Vite · localhost:5173" style="text;html=1;strokeColor=none;fillColor=none;align=right;fontSize=10;fontColor=#475569;" vertex="1" parent="layer4_bg">
      <mxGeometry x="800" y="5" width="260" height="20" as="geometry" />
    </mxCell>

    <!-- Layer 3: FastAPI / Agent -->
    <mxCell id="layer3_bg" value="Layer 3 — FastAPI Backend + Agent Orchestrator" style="swimlane;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontStyle=1;fontSize=12;startSize=30;" vertex="1" parent="1">
      <mxGeometry x="40" y="240" width="1080" height="140" as="geometry" />
    </mxCell>
    <mxCell id="fastapi" value="FastAPI + uvicorn&#xa;localhost:8000" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=11;" vertex="1" parent="layer3_bg">
      <mxGeometry x="20" y="50" width="150" height="60" as="geometry" />
    </mxCell>
    <mxCell id="agent" value="Agent Orchestrator&#xa;(OpenAI gpt-4o&#xa;Function Calling)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00A8CC;strokeColor=#007A99;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="layer3_bg">
      <mxGeometry x="200" y="40" width="160" height="70" as="geometry" />
    </mxCell>
    <mxCell id="tool_sql" value="Tool: sql_analytics" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer3_bg">
      <mxGeometry x="400" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="tool_graph" value="Tool: graph_traversal&#xa;(networkx)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer3_bg">
      <mxGeometry x="560" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="tool_semantic" value="Tool: semantic_search&#xa;(ChromaDB)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer3_bg">
      <mxGeometry x="720" y="50" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="etl_trigger" value="ETL Pipeline&#xa;(trigger endpoint)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#F59E0B;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer3_bg">
      <mxGeometry x="880" y="50" width="140" height="50" as="geometry" />
    </mxCell>

    <!-- Layer 2: Data -->
    <mxCell id="layer2_bg" value="Layer 2 — Data Layer (SQLite + ChromaDB)" style="swimlane;fillColor=#F8FAFC;strokeColor=#475569;fontColor=#1D3269;fontStyle=1;fontSize=12;startSize=30;" vertex="1" parent="1">
      <mxGeometry x="40" y="420" width="1080" height="130" as="geometry" />
    </mxCell>
    <mxCell id="sqlite" value="SQLite Database&#xa;data/cmdb.db&#xa;&#xa;applications · types&#xa;processes · edges" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer2_bg">
      <mxGeometry x="160" y="20" width="160" height="90" as="geometry" />
    </mxCell>
    <mxCell id="chromadb" value="ChromaDB&#xa;data/chroma/&#xa;&#xa;1,250 embeddings&#xa;all-MiniLM-L6-v2" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer2_bg">
      <mxGeometry x="460" y="20" width="160" height="90" as="geometry" />
    </mxCell>
    <mxCell id="networkx" value="networkx DiGraph&#xa;(in-memory)&#xa;&#xa;1,250 nodes&#xa;loaded at startup" style="shape=mxgraph.flowchart.start_2;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer2_bg">
      <mxGeometry x="760" y="20" width="160" height="90" as="geometry" />
    </mxCell>

    <!-- Layer 1: ETL -->
    <mxCell id="layer1_bg" value="Layer 1 — ETL Pipeline (Python)" style="swimlane;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontStyle=1;fontSize=12;startSize=30;" vertex="1" parent="1">
      <mxGeometry x="40" y="590" width="1080" height="120" as="geometry" />
    </mxCell>
    <mxCell id="xlsx_input" value="CMDB XLSX&#xa;1,250 records&#xa;20 columns" style="shape=document;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer1_bg">
      <mxGeometry x="40" y="30" width="120" height="70" as="geometry" />
    </mxCell>
    <mxCell id="etl_ingest" value="ingest.py&#xa;(pandas + openpyxl)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer1_bg">
      <mxGeometry x="200" y="40" width="130" height="50" as="geometry" />
    </mxCell>
    <mxCell id="etl_normalize" value="normalize.py&#xa;(types · booleans · UUIDs)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer1_bg">
      <mxGeometry x="360" y="40" width="140" height="50" as="geometry" />
    </mxCell>
    <mxCell id="etl_embed" value="embed.py&#xa;(sentence-transformers&#xa;→ ChromaDB)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer1_bg">
      <mxGeometry x="530" y="35" width="140" height="60" as="geometry" />
    </mxCell>
    <mxCell id="etl_write" value="SQLite write&#xa;(transaction)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="layer1_bg">
      <mxGeometry x="700" y="40" width="120" height="50" as="geometry" />
    </mxCell>

    <!-- External: OpenAI -->
    <mxCell id="openai" value="OpenAI API&#xa;gpt-4o&#xa;api.openai.com" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1D3269;strokeColor=#0F1C3D;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="940" y="730" width="160" height="70" as="geometry" />
    </mxCell>

    <!-- Arrows: Layer 4 → Layer 3 -->
    <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;" edge="1" parent="1" source="react_query" target="fastapi">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Arrows: Agent → Tools -->
    <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;dashed=1;" edge="1" parent="layer3_bg" source="agent" target="tool_sql">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;dashed=1;" edge="1" parent="layer3_bg" source="agent" target="tool_graph">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e4" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;dashed=1;" edge="1" parent="layer3_bg" source="agent" target="tool_semantic">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Arrows: Tools → Data Layer -->
    <mxCell id="e5" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#475569;" edge="1" parent="1" source="tool_sql" target="sqlite">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e6" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#475569;" edge="1" parent="1" source="tool_semantic" target="chromadb">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e7" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#475569;" edge="1" parent="1" source="tool_graph" target="networkx">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Arrows: ETL → Data Layer -->
    <mxCell id="e8" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="etl_write" target="sqlite">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e9" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="etl_embed" target="chromadb">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Arrow: Agent → OpenAI (external) -->
    <mxCell id="e10" value="HTTPS (function calling)" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;dashed=1;fontColor=#1D3269;fontSize=10;" edge="1" parent="1" source="agent" target="openai">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ETL input arrow -->
    <mxCell id="e11" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="layer1_bg" source="xlsx_input" target="etl_ingest">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e12" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="layer1_bg" source="etl_ingest" target="etl_normalize">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e13" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="layer1_bg" source="etl_normalize" target="etl_embed">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="e14" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="layer1_bg" source="etl_normalize" target="etl_write">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

### Diagram 2 — Data Flow: NL Query Path

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="Data Flow — NL Query Path (Read)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1;fontColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="184" y="20" width="800" height="40" as="geometry" />
    </mxCell>

    <!-- Swim lanes -->
    <mxCell id="swim" value="" style="shape=pool;html=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=none;horizontalStack=1;resizeParent=1;resizeParentMax=0;collapsible=0;marginBottom=0;" vertex="1" parent="1">
      <mxGeometry x="40" y="80" width="1100" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: User -->
    <mxCell id="lane_user" value="User (Browser)" style="swimlane;startSize=30;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="0" y="0" width="180" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: React -->
    <mxCell id="lane_react" value="React SPA" style="swimlane;startSize=30;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="180" y="0" width="180" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: FastAPI -->
    <mxCell id="lane_api" value="FastAPI Backend" style="swimlane;startSize=30;fillColor=#F8FAFC;strokeColor=#475569;fontColor=#1D3269;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="360" y="0" width="180" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: Agent -->
    <mxCell id="lane_agent" value="Agent Orchestrator" style="swimlane;startSize=30;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="540" y="0" width="180" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: OpenAI -->
    <mxCell id="lane_openai" value="OpenAI API" style="swimlane;startSize=30;fillColor=#1D3269;strokeColor=#0F1C3D;fontColor=#FFFFFF;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="720" y="0" width="180" height="700" as="geometry" />
    </mxCell>

    <!-- Lane: Data -->
    <mxCell id="lane_data" value="Data Layer" style="swimlane;startSize=30;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontStyle=1;" vertex="1" parent="swim">
      <mxGeometry x="900" y="0" width="200" height="700" as="geometry" />
    </mxCell>

    <!-- Steps in User lane -->
    <mxCell id="s1" value="1. Type NL query&#xa;'Which apps support&#xa;Radiation Oncology?'" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_user">
      <mxGeometry x="10" y="50" width="160" height="60" as="geometry" />
    </mxCell>
    <mxCell id="s8" value="8. View result table&#xa;+ citation chip" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#00A8CC;strokeColor=#007A99;fontColor=#FFFFFF;fontSize=10;" vertex="1" parent="lane_user">
      <mxGeometry x="10" y="580" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Steps in React lane -->
    <mxCell id="s2" value="2. POST /api/query&#xa;{text, conversation_id,&#xa;history}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_react">
      <mxGeometry x="10" y="150" width="160" height="60" as="geometry" />
    </mxCell>
    <mxCell id="s7" value="7. Render result&#xa;table + citation" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_react">
      <mxGeometry x="10" y="510" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Steps in FastAPI lane -->
    <mxCell id="s3" value="3. Validate request&#xa;Pass to Agent" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#475569;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_api">
      <mxGeometry x="10" y="240" width="160" height="50" as="geometry" />
    </mxCell>
    <mxCell id="s6b" value="6b. Assemble response&#xa;JSON + return" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#475569;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_api">
      <mxGeometry x="10" y="430" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Steps in Agent lane -->
    <mxCell id="s4" value="4. Classify intent&#xa;→ tool selection" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_agent">
      <mxGeometry x="10" y="310" width="160" height="50" as="geometry" />
    </mxCell>
    <mxCell id="s6" value="6a. Merge tool results&#xa;→ cited response" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_agent">
      <mxGeometry x="10" y="430" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Steps in OpenAI lane -->
    <mxCell id="s4b" value="gpt-4o routes to&#xa;semantic_search +&#xa;sql filter tools" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#FFFFFF;fontColor=#FFFFFF;fontSize=10;" vertex="1" parent="lane_openai">
      <mxGeometry x="10" y="310" width="160" height="60" as="geometry" />
    </mxCell>

    <!-- Steps in Data lane -->
    <mxCell id="s5a" value="5a. ChromaDB&#xa;semantic_search(&#xa;'Radiation Oncology')" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_data">
      <mxGeometry x="10" y="360" width="175" height="60" as="geometry" />
    </mxCell>
    <mxCell id="s5b" value="5b. SQLite sql_analytics&#xa;(filter + count)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="lane_data">
      <mxGeometry x="10" y="440" width="175" height="50" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

### Diagram 3 — ETL Pipeline Flow

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="ETL Pipeline — CMDB XLSX to SQLite + ChromaDB" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="80" y="20" width="660" height="40" as="geometry" />
    </mxCell>

    <!-- Start -->
    <mxCell id="start" value="Operator uploads XLSX&#xa;(web UI or CLI)" style="ellipse;whiteSpace=wrap;html=1;fillColor=#1D3269;strokeColor=#0F1C3D;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="280" y="80" width="200" height="60" as="geometry" />
    </mxCell>

    <!-- Validate schema -->
    <mxCell id="validate" value="Validate XLSX schema&#xa;20 columns present?" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#F59E0B;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="255" y="180" width="250" height="80" as="geometry" />
    </mxCell>
    <mxCell id="reject" value="Reject file&#xa;Return error&#xa;Preserve prior data" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#EF4444;fontColor=#EF4444;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="560" y="195" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Parse records -->
    <mxCell id="parse" value="pandas read_excel()&#xa;1,250+ records" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="280" y="300" width="200" height="50" as="geometry" />
    </mxCell>

    <!-- Normalize -->
    <mxCell id="normalize" value="Normalize fields&#xa;• app_type → COTS|Homegrown|NULL&#xa;• baptist_managed → bool&#xa;• strings → strip whitespace" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="255" y="390" width="250" height="70" as="geometry" />
    </mxCell>

    <!-- UUID -->
    <mxCell id="uuid" value="Generate / preserve UUIDs&#xa;key: name + company&#xa;Re-ingest → same UUID" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="255" y="500" width="250" height="60" as="geometry" />
    </mxCell>

    <!-- Transaction fork -->
    <mxCell id="fork" value="" style="rhombus;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="345" y="600" width="70" height="70" as="geometry" />
    </mxCell>
    <mxCell id="fork_label" value="Write both outputs" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=10;fontColor=#475569;" vertex="1" parent="1">
      <mxGeometry x="320" y="580" width="120" height="20" as="geometry" />
    </mxCell>

    <!-- SQLite write -->
    <mxCell id="sqlite_write" value="SQLite transaction&#xa;• INSERT/UPDATE applications&#xa;• Upsert node tables&#xa;• Upsert edge tables&#xa;• Mark absent → inactive&#xa;• Log etl_runs" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="100" y="700" width="200" height="110" as="geometry" />
    </mxCell>

    <!-- Embed -->
    <mxCell id="embed" value="sentence-transformers&#xa;all-MiniLM-L6-v2 (CPU)&#xa;&#xa;Input: name + description&#xa;(NO owner names / URLs)&#xa;&#xa;Only re-embed changed records" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="460" y="700" width="200" height="110" as="geometry" />
    </mxCell>

    <!-- ChromaDB write -->
    <mxCell id="chroma_write" value="ChromaDB upsert&#xa;doc_id = application_id&#xa;metadata: type, process,&#xa;baptist_managed" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="460" y="840" width="200" height="70" as="geometry" />
    </mxCell>

    <!-- Reload graph -->
    <mxCell id="reload_graph" value="Reload networkx graph&#xa;from SQLite" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="255" y="940" width="250" height="50" as="geometry" />
    </mxCell>

    <!-- Done -->
    <mxCell id="done" value="ETL complete&#xa;Notify UI via WebSocket&#xa;Show: Updated · N apps" style="ellipse;whiteSpace=wrap;html=1;fillColor=#10B981;strokeColor=#059669;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="270" y="1030" width="220" height="60" as="geometry" />
    </mxCell>

    <!-- Error path -->
    <mxCell id="rollback" value="Rollback SQLite transaction&#xa;Preserve prior state" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FEF2F2;strokeColor=#EF4444;fontColor=#EF4444;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="560" y="715" width="160" height="50" as="geometry" />
    </mxCell>

    <!-- Arrows -->
    <mxCell id="a1" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;" edge="1" parent="1" source="start" target="validate">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a2" value="No" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#EF4444;fontColor=#EF4444;fontSize=10;" edge="1" parent="1" source="validate" target="reject">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a3" value="Yes" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;fontColor=#10B981;fontSize=10;" edge="1" parent="1" source="validate" target="parse">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a4" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="parse" target="normalize">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a5" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="normalize" target="uuid">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a6" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="uuid" target="fork">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a7" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;" edge="1" parent="1" source="fork" target="sqlite_write">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a8" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;" edge="1" parent="1" source="fork" target="embed">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a9" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;" edge="1" parent="1" source="embed" target="chroma_write">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a10" value="Error" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#EF4444;fontColor=#EF4444;fontSize=10;" edge="1" parent="1" source="sqlite_write" target="rollback">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a11" value="Success" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;fontColor=#10B981;fontSize=10;" edge="1" parent="1" source="sqlite_write" target="reload_graph">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a11b" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="chroma_write" target="reload_graph">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="a12" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="1" source="reload_graph" target="done">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

### Diagram 4 — SQLite Graph Schema (Entity-Relationship)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="SQLite Graph Schema — Nodes and Edges" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="184" y="20" width="800" height="40" as="geometry" />
    </mxCell>

    <!-- Applications (central node) -->
    <mxCell id="app_table" value="applications&#xa;────────────────&#xa;application_id (PK)&#xa;application_name&#xa;company&#xa;publisher&#xa;description&#xa;application_type&#xa;architecture_type&#xa;baptist_managed&#xa;business_process&#xa;... (20 fields total)" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="430" y="280" width="240" height="260" as="geometry" />
    </mxCell>

    <!-- application_types -->
    <mxCell id="type_table" value="application_types&#xa;────────────────&#xa;type_id (PK)&#xa;type_name&#xa;(COTS | Homegrown)" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;fontStyle=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="80" y="80" width="200" height="100" as="geometry" />
    </mxCell>

    <!-- architecture_types -->
    <mxCell id="arch_table" value="architecture_types&#xa;────────────────&#xa;arch_id (PK)&#xa;arch_name" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;fontStyle=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="80" y="330" width="200" height="90" as="geometry" />
    </mxCell>

    <!-- business_processes -->
    <mxCell id="proc_table" value="business_processes&#xa;────────────────&#xa;process_id (PK)&#xa;process_name" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;fontStyle=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="80" y="580" width="200" height="90" as="geometry" />
    </mxCell>

    <!-- companies -->
    <mxCell id="company_table" value="companies&#xa;────────────────&#xa;company_id (PK)&#xa;company_name" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;fontStyle=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="860" y="80" width="200" height="90" as="geometry" />
    </mxCell>

    <!-- etl_runs -->
    <mxCell id="etl_table" value="etl_runs&#xa;────────────────&#xa;run_id (PK)&#xa;run_at · status&#xa;records_loaded" style="shape=table;html=1;whiteSpace=wrap;startSize=30;container=0;collapsible=0;fontStyle=1;fillColor=#FFFBEB;strokeColor=#F59E0B;fontColor=#1D3269;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="860" y="550" width="200" height="100" as="geometry" />
    </mxCell>

    <!-- Edge tables -->
    <mxCell id="edge_type" value="app_uses_type&#xa;────────────────&#xa;application_id (FK)&#xa;type_id (FK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="270" y="120" width="150" height="70" as="geometry" />
    </mxCell>

    <mxCell id="edge_arch" value="app_has_architecture&#xa;────────────────&#xa;application_id (FK)&#xa;arch_id (FK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="270" y="340" width="150" height="70" as="geometry" />
    </mxCell>

    <mxCell id="edge_proc" value="app_supports_process&#xa;────────────────&#xa;application_id (FK)&#xa;process_id (FK)" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="1">
      <mxGeometry x="270" y="570" width="150" height="70" as="geometry" />
    </mxCell>

    <!-- networkx note -->
    <mxCell id="nx_note" value="networkx DiGraph&#xa;loads these tables at startup&#xa;Nodes: apps + processes + types&#xa;Edges: the three edge tables&#xa;Redundancy = shared process cluster" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;dashed=1;" vertex="1" parent="1">
      <mxGeometry x="660" y="300" width="180" height="100" as="geometry" />
    </mxCell>

    <!-- Relationship arrows -->
    <mxCell id="r1" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#1D3269;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="app_table" target="edge_type">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r2" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#1D3269;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="type_table" target="edge_type">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r3" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#1D3269;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="app_table" target="edge_arch">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r4" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#1D3269;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="arch_table" target="edge_arch">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r5" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#00A8CC;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="app_table" target="edge_proc">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r6" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#00A8CC;endArrow=ERzeroToMany;startArrow=ERmandOne;" edge="1" parent="1" source="proc_table" target="edge_proc">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="r7" style="edgeStyle=entityRelationEdgeStyle;html=1;strokeColor=#1D3269;dashed=1;" edge="1" parent="1" source="app_table" target="nx_note">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

### Diagram 5 — Deployment Topology

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="827" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- Title -->
    <mxCell id="title" value="Deployment Topology — Local Machine (MVP Demo)" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=14;fontStyle=1;fontColor=#1D3269;" vertex="1" parent="1">
      <mxGeometry x="80" y="20" width="660" height="40" as="geometry" />
    </mxCell>

    <!-- Local machine boundary -->
    <mxCell id="machine" value="Local Machine (Windows / macOS laptop)" style="swimlane;fillColor=#F8FAFC;strokeColor=#1D3269;fontColor=#1D3269;fontStyle=1;fontSize=13;startSize=40;dashed=0;rounded=1;" vertex="1" parent="1">
      <mxGeometry x="40" y="80" width="740" height="560" as="geometry" />
    </mxCell>

    <!-- Browser -->
    <mxCell id="browser" value="Browser&#xa;React SPA&#xa;localhost:5173" style="shape=mxgraph.cisco.computers_and_peripherals.pc;html=1;pointerEvents=1;dashed=0;fillColor=#EEF2FB;strokeColor=#1D3269;strokeWidth=2;verticalLabelPosition=bottom;verticalAlign=top;align=center;outlineConnect=0;fontSize=11;" vertex="1" parent="machine">
      <mxGeometry x="40" y="70" width="120" height="100" as="geometry" />
    </mxCell>

    <!-- FastAPI -->
    <mxCell id="fastapi_box" value="FastAPI + uvicorn&#xa;localhost:8000&#xa;&#xa;• REST API routes&#xa;• WebSocket /ws/refresh&#xa;• Agent orchestrator&#xa;• ETL trigger" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E0F7FC;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=11;" vertex="1" parent="machine">
      <mxGeometry x="250" y="60" width="200" height="130" as="geometry" />
    </mxCell>

    <!-- Data files -->
    <mxCell id="data_box" value="data/" style="swimlane;fillColor=#ECFDF5;strokeColor=#10B981;fontColor=#1D3269;fontStyle=1;fontSize=11;startSize=25;" vertex="1" parent="machine">
      <mxGeometry x="520" y="60" width="190" height="180" as="geometry" />
    </mxCell>
    <mxCell id="cmdb_file" value="cmdb.db&#xa;(SQLite)" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="data_box">
      <mxGeometry x="10" y="35" width="80" height="70" as="geometry" />
    </mxCell>
    <mxCell id="chroma_file" value="chroma/&#xa;(ChromaDB)" style="shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#00A8CC;fontColor=#1D3269;fontSize=10;" vertex="1" parent="data_box">
      <mxGeometry x="100" y="35" width="80" height="70" as="geometry" />
    </mxCell>

    <!-- .env -->
    <mxCell id="env_file" value=".env&#xa;OPENAI_API_KEY=sk-...&#xa;⚠ NOT in git" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFBEB;strokeColor=#F59E0B;fontColor=#1D3269;fontSize=11;" vertex="1" parent="machine">
      <mxGeometry x="250" y="230" width="160" height="60" as="geometry" />
    </mxCell>

    <!-- .gitignore note -->
    <mxCell id="gitignore_note" value=".gitignore includes:&#xa;.env · data/ · __pycache__/&#xa;node_modules/ · *.pyc" style="text;html=1;strokeColor=#EF4444;fillColor=#FEF2F2;align=left;verticalAlign=middle;fontSize=10;fontColor=#EF4444;rounded=1;" vertex="1" parent="machine">
      <mxGeometry x="440" y="280" width="250" height="60" as="geometry" />
    </mxCell>

    <!-- networkx in-memory -->
    <mxCell id="nx_mem" value="networkx DiGraph&#xa;(in-memory, ~10MB)&#xa;Loaded at startup&#xa;Refreshed after ETL" style="ellipse;whiteSpace=wrap;html=1;fillColor=#EEF2FB;strokeColor=#1D3269;fontColor=#1D3269;fontSize=10;" vertex="1" parent="machine">
      <mxGeometry x="520" y="380" width="190" height="80" as="geometry" />
    </mxCell>

    <!-- XLSX upload -->
    <mxCell id="xlsx_box" value="CMDB XLSX&#xa;(operator upload)" style="shape=document;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#10B981;fontColor=#1D3269;fontSize=10;" vertex="1" parent="machine">
      <mxGeometry x="60" y="390" width="120" height="80" as="geometry" />
    </mxCell>

    <!-- Port labels -->
    <mxCell id="port_label" value="HTTP :5173 → :8000" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=10;fontColor=#475569;" vertex="1" parent="machine">
      <mxGeometry x="170" y="100" width="80" height="30" as="geometry" />
    </mxCell>

    <!-- Internal network boundary (dashed) -->
    <mxCell id="network_boundary" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#1D3269;strokeWidth=2;dashed=1;" vertex="1" parent="1">
      <mxGeometry x="20" y="60" width="780" height="600" as="geometry" />
    </mxCell>
    <mxCell id="network_label" value="Internal Network Boundary (auth not required for MVP — local machine only)" style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=10;fontColor=#1D3269;fontStyle=2;" vertex="1" parent="1">
      <mxGeometry x="80" y="665" width="660" height="20" as="geometry" />
    </mxCell>

    <!-- External: OpenAI -->
    <mxCell id="openai_ext" value="OpenAI API&#xa;api.openai.com&#xa;gpt-4o" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#1D3269;strokeColor=#0F1C3D;fontColor=#FFFFFF;fontSize=11;" vertex="1" parent="1">
      <mxGeometry x="640" y="700" width="160" height="60" as="geometry" />
    </mxCell>

    <!-- Arrows inside machine -->
    <mxCell id="ma1" value="HTTP" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;" edge="1" parent="machine" source="browser" target="fastapi_box">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="ma2" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;" edge="1" parent="machine" source="fastapi_box" target="cmdb_file">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="ma3" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#00A8CC;" edge="1" parent="machine" source="fastapi_box" target="chroma_file">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="ma4" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#F59E0B;dashed=1;" edge="1" parent="machine" source="fastapi_box" target="env_file">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="ma5" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#10B981;" edge="1" parent="machine" source="xlsx_box" target="fastapi_box">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="ma6" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;" edge="1" parent="machine" source="fastapi_box" target="nx_mem">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- Arrow to OpenAI (crosses boundary) -->
    <mxCell id="ext_arrow" value="HTTPS (gpt-4o function calls only)" style="edgeStyle=orthogonalEdgeStyle;html=1;strokeColor=#1D3269;dashed=1;fontColor=#1D3269;fontSize=10;" edge="1" parent="1" source="fastapi_box" target="openai_ext">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

  </root>
</mxGraphModel>
```

---

## 12. Architecture Decision Log

| ID | Decision | Rationale | Reversible |
|---|---|---|---|
| AD-001 | SQLite over Cloud Spanner | 1,250 records — no distributed scale needed. Zero cloud cost. Portable file. | Yes — schema portable to Postgres/Spanner |
| AD-002 | networkx over GQL | Edge tables map 1:1 to networkx. At this node count, in-memory graph is faster than DB round-trips. | Yes — swap to Postgres + pgRouting if scale demands |
| AD-003 | sentence-transformers CPU | No GPU needed at 1,250 records. Embedding time <5 min. Eliminates Vertex AI dependency. | Yes — swap model or add GPU later |
| AD-004 | ChromaDB SQLite-backed | Native SQLite persistence; same file-based portability as main DB. No separate vector DB server. | Yes — migrate to Pinecone/Weaviate if scale demands |
| AD-005 | OpenAI gpt-4o function calling | Most capable tool-routing model. Function calling maps cleanly to sql/graph/semantic tool set. API-agnostic vs Vertex AI. | Yes — swap to Claude API or local Ollama model |
| AD-006 | FastAPI + uvicorn | Async Python, auto-generated OpenAPI docs, WebSocket support for ETL progress. Native Python ecosystem fit. | No significant lock-in |
| AD-007 | React JS 18 + Vite | Team preference. Standard SPA. Vite gives fast HMR for development. | No significant lock-in |
| AD-008 | No auth MVP | Local machine deployment confirmed safe (OQ-2 closed). Must be revisited for any shared deployment. | Add FastAPI OAuth2/OIDC middleware |
| AD-009 | PII fence in agent system prompt | Owner/engineer names stored in DB and shown in UI but never sent to OpenAI. Data governance requirement (A-8). | Architectural — must stay in all versions |
| AD-010 | SQLite WAL mode | Allows concurrent reads during ETL write operations. No blocking during refresh. | Config — change journal mode anytime |
| AD-011 | In-memory networkx graph | Load once at startup, refresh after ETL. <10MB for 1,250 nodes. Zero query latency. | Add caching layer if graph grows >50k nodes |
| AD-012 | Incremental re-embedding | Only re-embed records whose name or description changed. Avoids 5-min full re-embed on every refresh. | Configurable per-run flag |

---

*Architecture finalized: 2026-06-12. Input documents: brief, PRD, DESIGN.md, EXPERIENCE.md. draw.io diagrams (5) embedded in Section 11 — import via app.diagrams.net → File → Import From → Device.*
