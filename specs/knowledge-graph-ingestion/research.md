# Research: IT Knowledge Graph Ingestion Pipeline

**Feature**: Epic 1 — Platform Foundation
**Date**: 2026-06-12
**Status**: Complete — all design decisions resolved from source documents

---

## Overview

All design decisions for Epic 1 were resolved from existing source documents (`docs/brief.md`, `docs/prd.md`, `docs/architecture.md`, `docs/epics.md`). No NEEDS CLARIFICATION items remain. This document records the rationale for each key decision so implementors understand *why* each choice was made.

---

## Decision 1: SQLite as the Primary Data Store

**Decision**: Use SQLite (`data/cmdb.db`) as the relational store for all CMDB data.

**Rationale**: 1,250 records is well within SQLite's capability. SQLite requires no database server, runs from a single portable file, and integrates directly into Python via the stdlib `sqlite3` module (zero extra infrastructure). The entire database can be moved to another machine by copying one file.

**Alternatives considered**:
- **PostgreSQL**: Overkill at this scale; adds server process, connection management, and deployment complexity.
- **Cloud Spanner / GCP**: Explicitly rejected (see AD-001). Eliminates cloud dependency requirement.
- **DuckDB**: Considered for analytics workloads; rejected because SQLite WAL mode handles concurrent read/write adequately at this scale and the edge table schema maps cleanly to SQLite foreign keys.

**When to revisit**: If the dataset grows beyond ~50,000 records, or if multiple concurrent write processes are needed, migrate to PostgreSQL (the schema is portable — same DDL with minor type adjustments).

---

## Decision 2: WAL Mode for Concurrent Read/Write

**Decision**: Enable `PRAGMA journal_mode=WAL` on the SQLite connection at startup.

**Rationale**: Without WAL mode, SQLite's default journal mode uses file-level locking — a write lock blocks all readers. During ETL (which can take up to 5 minutes for 1,250 records + embeddings), this would make the API unresponsive. WAL mode allows concurrent readers to proceed even while the ETL transaction is being written, so the web interface remains usable during a data refresh.

**Alternatives considered**:
- **Default rollback journal**: Blocks all reads during write. Unacceptable UX during 5-minute ETL.
- **WAL mode with checkpoint tuning**: Default checkpoint thresholds (1,000 pages) are sufficient at this scale.

---

## Decision 3: Atomic ETL Transaction with Full Rollback

**Decision**: Wrap all SQLite writes in a single transaction. On any failure, perform a full `ROLLBACK` — preserving the prior data state entirely.

**Rationale**: The PRD requires (NFR-2) that the ETL pipeline never leave the database in a partial state. A malformed XLSX or mid-pipeline error must not corrupt the production data. By wrapping the entire write sequence in one transaction, either all 1,250+ records (across all node + edge tables) are committed together, or none are.

**Implementation**: 
- `BEGIN TRANSACTION` before the first INSERT/UPDATE
- `COMMIT` only after all tables are updated AND `etl_runs` is written
- `ROLLBACK` on any exception

**Alternatives considered**:
- **Per-table transactions**: Would leave tables in inconsistent states if the pipeline fails mid-way (e.g., `applications` updated but `app_supports_process` not).
- **Two-phase: write to temp tables then swap**: More complex, same guarantee. Not needed at this scale.

---

## Decision 4: UUID Deduplication Key — Application Name + Company

**Decision**: Use `(application_name, company)` as the natural key for UUID preservation across XLSX re-ingestions.

**Rationale**: The PRD (FR-3, A-3) specifies this as the deduplication key. Application Name is the primary identifier within a company context. The CMDB does not have a stable ServiceNow CMDB record ID exposed in the XLSX export. Using Name + Company is the best available stable identifier in the data.

**Consequences**:
- If an application is renamed in ServiceNow, it appears as a new application on re-ingest (new UUID). The old name record is soft-deleted (active_status=0). A warning is logged.
- Applications with identical names within the same company are treated as duplicates — each gets a distinct UUID, and a warning is logged. Both records are loaded.

**Alternatives considered**:
- **Application Name only**: Risk of collision across companies.
- **Application URL**: Many applications have NULL URLs; not a reliable key.
- **ServiceNow sys_id**: Not present in the XLSX export schema.

---

## Decision 5: Soft Delete for Absent Records

**Decision**: Records present in the previous load but absent from the new XLSX are marked `active_status = 0` — not deleted.

**Rationale**: Application records may be temporarily removed from CMDB exports due to data governance processes, not because the application was actually decommissioned. Preserving the record with its UUID allows:
- Historical reference without data loss
- UUID stability if the record reappears in a future export
- The `etl_runs` log to reflect the change

**Implementation**: After all current-run UUIDs are written, execute:
```sql
UPDATE applications SET active_status = 0 
WHERE application_id NOT IN (<current_run_uuid_list>)
  AND active_status = 1
```

**Default query filter**: All application queries use `WHERE active_status = 1` by default. Inactive records are not shown unless explicitly requested.

---

## Decision 6: networkx In-Memory Graph

**Decision**: Load all application nodes and edge relationships into a `networkx.DiGraph` at FastAPI startup, and reload after each successful ETL run.

**Rationale**: At 1,250 nodes, the full graph fits comfortably in memory (<10MB RAM estimated). Loading the graph at startup eliminates per-query database join overhead for graph traversal. networkx provides all required graph algorithms (BFS, connected components, subgraph extraction) without a graph database.

**Lifecycle**:
- Loaded once at FastAPI startup via lifespan event
- Reloaded after each successful ETL refresh (triggered by the ETL completion handler)
- Thread-safe for reads; writes only happen at reload (not incremental)

**Alternatives considered**:
- **Build graph per-query**: Acceptable latency (~200ms for 1,250 nodes) but wastes CPU on every request.
- **Neo4j / Cypher**: Overkill; adds a separate graph database server process; GQL adds complexity.
- **SQLite recursive CTE for traversal**: Works for simple queries but unwieldy for multi-hop patterns.

**When to revisit**: If the graph grows beyond ~50,000 nodes, or if real-time edge insertion is needed (current model is batch-refresh only).

---

## Decision 7: WebSocket for ETL Progress Streaming

**Decision**: Use a FastAPI WebSocket endpoint (`/ws/refresh`) to stream ETL progress events to the browser in real time.

**Rationale**: ETL can take up to 5 minutes. Polling `GET /api/refresh/status` every few seconds would provide coarse progress feedback and add unnecessary API load. WebSocket allows the ETL pipeline to push granular progress events (per-step, per-batch) to the browser with minimal overhead.

**Fallback**: If the WebSocket connection drops, the React frontend falls back to polling `GET /api/refresh/status` at 5-second intervals.

**Implementation notes**:
- ETL runs as a FastAPI `BackgroundTask` (async)
- Progress events are passed via an asyncio queue from the ETL coroutine to the WebSocket handler
- WebSocket closes automatically on ETL completion

**Alternatives considered**:
- **Server-Sent Events (SSE)**: Simpler protocol, but WebSocket is already in the FastAPI tech stack and supports bi-directional communication if needed in the future.
- **Polling only**: Simpler, but coarser feedback. Acceptable fallback, not the primary path.

---

## Decision 8: Incremental Re-Embedding (Epic 3 Concern, Established in Epic 1)

**Decision**: On data refresh, only re-embed applications whose `application_name` or `description` has changed since the last ingest.

**Rationale**: Generating embeddings for all 1,250 records takes up to 5 minutes on CPU. If 90% of records are unchanged, a full re-embed wastes 4+ minutes. Incremental re-embedding is achieved by storing a hash of `name + description` per record during ETL and comparing it on re-ingest.

**Implementation in Epic 1**: The ETL pipeline (ingest.py / normalize.py) tracks which records have changed. The `applications` table stores a `content_hash` column (SHA-256 of `name + description`). On re-ingest, only records with a different `content_hash` are flagged for re-embedding.

**Epic 3 executes** the actual embedding call. Epic 1 establishes the hash tracking infrastructure.

---

## Decision 9: PII Exclusion Fence — Established at ETL Level

**Decision**: PII-adjacent fields (Business Owner, T&D Application Owner, Primary Engineer, Last Updated By) are stored in SQLite and displayed in the UI detail panel, but are explicitly excluded from:
1. ChromaDB embedding input (Epic 3)
2. OpenAI API payloads (Epic 4)

**Rationale**: The PRD (Data Governance section, A-8, NFR-6) requires this. Employee names are PII-adjacent. Sending them to external AI services (OpenAI) would violate the data governance constraint. ChromaDB embeddings derived from employee names would encode PII into the vector store.

**Implementation**: The `normalize.py` module provides a `build_embed_payload(record)` function that explicitly constructs the embedding input string as `f"{record['application_name']} {record['description']}"` — with no other fields. This function is used by `embed.py` in Epic 3. The contract is established in Epic 1.

---

## Decision 10: No Authentication in MVP

**Decision**: No login, session tokens, or RBAC in v1. Network boundary (localhost) is the sole access control.

**Rationale**: The PRD (OQ-2 resolved, A-7, NFR-8) explicitly confirms this is acceptable for the MVP demo scope — a local machine deployment with the operator running both the browser and the server.

**Guardrails established in Epic 1**:
- CLAUDE.md and plan documentation note: **must add auth before any shared/networked deployment**
- FastAPI app is structured to make adding OAuth2/JWT middleware straightforward (route handlers have no auth-bypass logic baked in; auth is added as middleware, not per-route)

---

## Resolved Questions Summary

| Question | Resolution |
|----------|-----------|
| Data deduplication key | Application Name + Company (A-3 in PRD) |
| Business Process taxonomy normalization | Deferred post-launch; raw values loaded as-is (A-2) |
| Authentication model | None in MVP; network boundary only (A-7, confirmed by Chakri) |
| Data refresh trigger | Manual XLSX upload via web UI; no ServiceNow API in v1 (A-1, OQ-1 open for v2) |
| OpenAI API key management | `.env` file; no organizational secrets management for MVP (OQ-3 resolved) |
| Acceptance test definition | 20-query semantic test set and pilot session — Chakri + Uday Kumar to define before Sprint 1 (OQ-4) |
| Architecture type inference | Leave unpopulated fields as NULL; not a blocker (resolved in brief) |
