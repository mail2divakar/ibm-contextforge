---
title: "IT Application Knowledge Graph — Agentic Intelligence Platform"
status: final
created: 2026-06-12
updated: 2026-06-12
---

# PRD: IT Application Knowledge Graph — Agentic Intelligence Platform

## 0. Document Purpose

This PRD is for the PM (Uday Kumar), downstream workflow owners (architecture, UX, epics/stories), and the MVP acceptance stakeholder (Chakri, T&D). It is structured with a Glossary-anchored vocabulary, features grouped with globally-numbered FRs nested inside, and inline `[ASSUMPTION]` tags indexed in §9. The product brief (finalized 2026-06-12) is the upstream input; this PRD does not duplicate it but builds on it. The 6 Jira epics from the Baptist Health CMDB initiative are the primary requirements source.

---

## 1. Vision

Baptist Health South Florida maintains a CMDB of 1,250 active production applications. This dataset is authoritative and current, yet almost entirely inaccessible to the stakeholders who most need it. Enterprise architects manually hunt through ServiceNow exports. Clinical directors raise tickets to T&D when they need to know whether a scheduling tool already exists. Application rationalization decisions are made without evidence of what overlaps with what.

This platform transforms that static dataset into a live, queryable knowledge graph with a natural-language interface. Applications and their relationships (by type, architecture, business process, and vendor) are modeled as a graph that is queryable by structured SQL, graph traversal, and plain English. The result: any stakeholder answers portfolio questions in seconds, with evidence, without a ticket.

The MVP targets T&D architects and application owners as the primary operators, with Chakri as the acceptance owner. A React JS web interface makes the NL agent accessible to non-technical stakeholders from day one. The system uses local, open-source infrastructure (SQLite, ChromaDB, sentence-transformers) and OpenAI's gpt-4o to power the agentic layer — zero GCP dependency, near-zero infrastructure cost.

---

## 2. Target User

### 2.1 Jobs To Be Done

- **Enterprise Architect**: Know what capabilities exist before recommending new solutions; generate evidence for decommission proposals; understand vendor concentration and architecture distribution.
- **T&D Application Owner (Chakri and peers)**: Answer portfolio questions on demand; identify redundant applications supporting the same business process; track ownership gaps.
- **Business Stakeholder (Clinical Director, Operations Lead)**: Ask "do we have X?" in plain English and get a direct answer without raising a T&D ticket.
- **Procurement / Vendor Management** *(secondary)*: Identify vendor duplication before signing new contracts.
- **New T&D Hire / Onboarding Architect** *(secondary)*: Get a fast orientation to the application landscape without weeks of CMDB spelunking.

### 2.2 Non-Users (v1)

- External users / patients / vendors — this platform is internal-only
- Developers who need real-time CMDB sync — manual refresh is the v1 model
- Mobile users — web only in MVP

### 2.3 Key User Journeys

**UJ-1. Alex the architect checks for capability overlap before a procurement recommendation.**
- **Persona + context:** Alex, enterprise architect, preparing a recommendation memo on whether to procure a new clinical scheduling tool for BHMG.
- **Entry state:** Authenticated to internal network; opens the React web app in browser.
- **Path:** (1) Types "Do we already have a scheduling application for BHMG?" into the NL query field. (2) Agent returns a structured list of applications tagged with "Scheduling" or matching the BHMG business process. (3) Alex clicks one result to see its full CMDB record — owner, install status, architecture type. (4) Alex asks a follow-up: "Which of these are Baptist-managed?" — agent filters and re-responds. (5) Alex copies the result citations into the recommendation memo.
- **Climax:** Alex sees 3 overlapping applications before recommending procurement — the recommendation becomes "evaluate existing tools first."
- **Resolution:** Alex has a cited, evidence-backed finding in under 5 minutes. No ticket raised.
- **Edge case:** Query returns zero results — agent responds with "No applications found matching 'BHMG Scheduling'. Closest matches by business process: [Baptist Health Medical Group (BHMG) — 29 apps]" and offers to broaden the search.

**UJ-2. Chakri runs a redundancy analysis across Imaging applications.**
- **Persona + context:** Chakri, T&D application owner, preparing quarterly rationalization review for the Imaging business process (67 apps).
- **Entry state:** Web app open; navigates to Analytics view.
- **Path:** (1) Selects "Business Process" breakdown — sees Imaging: 67 apps. (2) Clicks into Imaging — system shows all 67 apps grouped by application type (COTS vs Homegrown) and architecture type. (3) Switches to "Redundancy View" — system runs graph traversal and returns clusters of 2+ apps sharing the same business process with similar descriptions. (4) Exports the redundancy cluster list as CSV.
- **Climax:** Chakri receives a ranked list of redundancy candidates — applications with overlapping functionality — that would have taken a full day to assemble manually.
- **Resolution:** CSV delivered; Chakri has a shortlist for the rationalization review meeting.

**UJ-3. Maria the clinical director asks whether a new app is needed.**
- **Persona + context:** Maria, Director of Radiation Oncology, approached by a vendor pitching a new dosimetry QA tool. She wants to know if Baptist Health already has one.
- **Entry state:** Web app open in browser; Maria has never used it before.
- **Path:** (1) Types "Do we have a dosimetry QA application for Radiation Oncology?" (2) Agent returns matching applications with names, publishers, and owners. (3) Maria sees "3D Scanner" and "ADAPTIIV MEDICAL TECHNOLOGIES" in the results. (4) She shares the URL/result with her T&D contact as evidence.
- **Climax:** Maria learns within 30 seconds that a dosimetry QA tool already exists — and who owns it — before the vendor conversation progresses.
- **Resolution:** Vendor meeting is redirected; no redundant procurement initiated.

---

## 3. Glossary

- **Application** — A discrete software system tracked in the CMDB with a unique `application_id`. Synonyms ("system," "tool," "platform") are not used elsewhere in this PRD.
- **CMDB** — Configuration Management Database. The ServiceNow-managed authoritative source of application records at Baptist Health. The v1 data source is an XLSX export from CMDB.
- **Business Process** — The organizational function an Application serves (e.g., "Radiation Oncology," "Imaging," "Pharmacy"). A single Application may support multiple Business Processes.
- **Application Type** — A classification of an Application's commercial origin: `COTS` (commercial off-the-shelf), `Homegrown` (internally developed), or unclassified.
- **Architecture Type** — The deployment pattern of an Application: `Client Server`, `Platform Host`, `Web Based`, `N-Tier`, `Other`, or unclassified.
- **Graph Model** — The relational representation of Applications and their relationships as nodes (Applications, ApplicationTypes, ArchitectureTypes, BusinessProcesses) and edges (App_Uses_Type, App_Has_Architecture, App_Supports_Process).
- **Redundancy Cluster** — A set of two or more Applications that share the same Business Process and are identified by the system as potentially overlapping in function.
- **NL Query** — A natural-language question submitted by a user to the Agentic Q&A Interface.
- **Semantic Search** — Vector-similarity search over Application names and descriptions using sentence-transformer embeddings stored in ChromaDB.
- **Agent** — The OpenAI gpt-4o-powered orchestration layer that routes NL Queries to graph queries, SQL analytics, or Semantic Search, and assembles structured responses.
- **ETL Pipeline** — The extract-transform-load process that ingests the CMDB XLSX, normalizes fields, generates UUIDs, and loads data into the SQLite database and ChromaDB vector store.
- **Data Refresh** — A manual or automated re-execution of the ETL Pipeline against an updated CMDB XLSX export.

---

## 4. Features

### 4.1 Data Ingestion & Normalization

**Description:** The ETL Pipeline reads the CMDB XLSX export, normalizes fields to canonical values, generates stable UUID-based `application_id` values for all records, and loads the normalized data into the SQLite relational schema and ChromaDB vector store. This is the foundation all other features depend on. Fulfills UJ-2 (Chakri needs complete, consistent data for analytics). The pipeline is triggered manually by an authorized operator uploading a new XLSX file. `[ASSUMPTION: No ServiceNow API integration in v1 — CMDB data enters the system only via XLSX upload. See OQ-1.]`

**Functional Requirements:**

#### FR-1: CMDB XLSX Ingestion
The ETL Pipeline ingests a CMDB XLSX file conforming to the 20-column Baptist Health schema (Application Name, Company, Publisher, Description, Updated, Last Updated By, Business Owner, T&D Application Owner, Primary Engineer, Application Support Group, Active, Install Status, Application URL, Application Portfolio Manager, Application Type, Architecture Type, Baptist Managed, Business Criticality, Business Process, Environment).

**Consequences (testable):**
- All 1,250 records from the reference XLSX are loaded without data loss.
- Records with missing optional fields (Architecture Type, Business Criticality, Environment) are loaded with `NULL` values and do not raise an error.
- When duplicate application names exist within the same Company, the system generates a warning log entry and loads them with distinct UUIDs.

#### FR-2: Field Normalization
The ETL Pipeline normalizes Application Type values to `COTS`, `Homegrown`, or `NULL`; trims whitespace from all string fields; and converts `Baptist Managed` to a boolean. `[ASSUMPTION: No canonical Business Process taxonomy exists in v1 — raw values are loaded as-is. Data quality cleanup is post-launch.]`

**Consequences (testable):**
- Application Type values not matching `COTS` or `Homegrown` (case-insensitive) are stored as `NULL` with a warning log entry.
- No leading/trailing whitespace exists in any string field after load.
- `Baptist Managed` values of `True`/`False`/`1`/`0`/`Yes`/`No` (case-insensitive) all resolve to SQLite boolean.

#### FR-3: UUID Generation
The ETL Pipeline generates a stable UUID v4 `application_id` for each Application record on first ingest, and preserves existing `application_id` values on re-ingest (matched by Application Name + Company). `[ASSUMPTION: Application Name + Company is the natural key for deduplication.]`

**Consequences (testable):**
- Re-ingesting the same XLSX produces identical `application_id` values for unchanged records.
- A record whose Application Name changes across XLSX versions is treated as a new Application with a new UUID; a warning is logged.

#### FR-4: Manual Data Refresh
An authorized operator can trigger a Data Refresh by uploading a new CMDB XLSX via the web interface or CLI. The system re-runs the ETL Pipeline, preserves existing UUIDs for unchanged records, adds new records, and flags removed records as `inactive` rather than deleting them. `[ASSUMPTION: "Authorized operator" in v1 is anyone with access to the internal deployment — no RBAC.]`

**Consequences (testable):**
- After refresh, new Application records appear in query results within 60 seconds.
- Records present in the prior load but absent from the new XLSX are marked `inactive` and excluded from default query results.
- The UI displays the timestamp of the last successful Data Refresh on the home screen.
- If the uploaded XLSX is malformed or missing required columns, the system rejects the file with an error message and preserves the prior data state (no partial writes).
- ETL errors are logged with the record identifier and failure reason; the operator is notified of any records that failed to load.

---

### 4.2 Graph Model & Relationship Queries

**Description:** Applications and their relationships are modeled in SQLite as a graph with explicit node tables (Applications, ApplicationTypes, ArchitectureTypes, BusinessProcesses) and edge tables (App_Uses_Type, App_Has_Architecture, App_Supports_Process). Python networkx traversal handles graph analysis — no GQL layer is required at this scale. Fulfills UJ-1 (Alex needs relationship traversal) and UJ-2 (Chakri needs redundancy clustering).

**Functional Requirements:**

#### FR-5: Relational Graph Schema
The system maintains a SQLite schema with the node and edge tables defined in the Jira Epic 2 schema, extended with a `companies` table and `baptist_managed`, `active_status`, `description`, and `publisher` fields on the Applications table.

**Consequences (testable):**
- All 20 CMDB columns are queryable via the SQLite schema after ETL.
- Foreign key relationships between edge tables and node tables enforce referential integrity.
- Schema migrations run without data loss on Data Refresh.

#### FR-6: Redundancy Cluster Detection
The system identifies Redundancy Clusters — sets of 2 or more Applications sharing the same Business Process — and exposes them as a queryable result set ranked by cluster size (largest first).

**Consequences (testable):**
- A query for redundancy clusters returns at least 5 clusters from the reference CMDB dataset.
- Each cluster result includes: Business Process name, list of Application names, Application Types, and Baptist Managed flags.
- Applications with `NULL` Business Process are excluded from cluster analysis.

#### FR-7: Vendor Concentration Analysis
The system identifies sets of 3 or more Applications sharing the same Publisher (vendor), enabling assessment of vendor concentration risk.

**Consequences (testable):**
- Query returns publishers with 3 or more applications, sorted by application count descending.
- Results include publisher name, application count, and list of application names.

#### FR-8: Graph Traversal for Relationship Queries
The Agent invokes networkx-based graph traversal to answer multi-hop relationship questions (e.g., "which business processes are supported by vendor-managed applications?").

**Consequences (testable):**
- Multi-hop queries spanning 2 edge tables return results in < 5 seconds for the 1,250-node graph.
- Results include the traversal path as a citation (e.g., "App → App_Supports_Process → Business Process").

---

### 4.3 Application Analytics

**Description:** Structured SQL analytics over the Graph Model expose distribution counts, breakdowns, and comparative views across Application Type, Architecture Type, Business Process, and Company. These analytics power both the web dashboard view and Agent responses to counting/distribution NL Queries. Fulfills UJ-2 (Chakri's rationalization review).

**Functional Requirements:**

#### FR-9: Distribution Analytics
The system provides pre-built analytics queries covering: application count by Application Type; application count by Architecture Type; application count by Business Process (top 20); application count by Company; and COTS vs Homegrown breakdown by Business Process.

**Consequences (testable):**
- All 5 distribution queries return results matching the reference CMDB dataset within ±1% (accounting for NULL handling).
- Each query executes in < 2 seconds on the SQLite database.

#### FR-10: Redundancy Report Export
The system exports Redundancy Cluster analysis results as a CSV file containing: Business Process, Application Name, Application Type, Architecture Type, Baptist Managed, Business Owner, T&D Application Owner.

**Consequences (testable):**
- Exported CSV opens correctly in Excel/Google Sheets.
- All fields listed above are present for each row.
- Export completes within 10 seconds for the full 1,250-record dataset.

---

### 4.4 Semantic Search

**Description:** Application names and descriptions are embedded using `sentence-transformers/all-MiniLM-L6-v2` and stored in a ChromaDB collection (SQLite-backed). Semantic Search enables fuzzy, intent-based application discovery — returning Applications whose descriptions and names are semantically similar to the query, even without exact keyword matches. Fulfills UJ-1 (Alex's capability search) and UJ-3 (Maria's vendor/function search).

**Functional Requirements:**

#### FR-11: Embedding Generation
The ETL Pipeline generates sentence-transformer embeddings for the concatenated name and description of each Application and stores them in ChromaDB with the `application_id` as the document ID. Embeddings are regenerated on Data Refresh only for records whose name or description changed. `[ASSUMPTION: Embedding model is all-MiniLM-L6-v2 running on CPU. No GPU required for 1,250 records.]`

**Consequences (testable):**
- All 1,250 Applications have a corresponding embedding in ChromaDB after ETL.
- Embedding generation for the full dataset completes within 5 minutes on a standard laptop CPU.
- Re-ingest only re-embeds changed records, not the full dataset.

#### FR-12: Semantic Search Query
A user can submit a natural-language description and receive a ranked list of up to 10 Applications whose names and descriptions are most semantically similar.

**Consequences (testable):**
- Searching "dosimetry QA radiation" returns "3D Scanner" in the top 3 results.
- Searching "computer assisted coding billing" returns "3M-CAC" in the top 3 results.
- Search response time is < 3 seconds for any query against the 1,250-record collection.

#### FR-13: Search Result Metadata
Each Semantic Search result includes: Application Name, Business Process, Application Type, Baptist Managed flag, Business Owner, and a similarity score.

**Consequences (testable):**
- All 6 metadata fields are present for every search result.
- Similarity scores are normalized to [0, 1] and displayed to 2 decimal places.

---

### 4.5 Agentic NL Q&A Interface

**Description:** The Agent (OpenAI gpt-4o with function calling) interprets NL Queries, selects the appropriate tool (graph traversal, SQL analytics, or Semantic Search), executes the query, and returns a structured, cited response. The Agent must answer all 10 sample questions from Jira Epic 5 correctly. It must not hallucinate — all claims in a response must be traceable to a specific database record or query result. Fulfills UJ-1, UJ-2, UJ-3.

**Functional Requirements:**

#### FR-14: NL Query Routing
The Agent classifies each natural-language query into one of three routing targets: SQL analytics (counting, distribution, breakdown questions), graph traversal (relationship, dependency, multi-hop questions), or Semantic Search (capability-match, "do we have X?" questions). The Agent may invoke multiple tools in sequence for compound queries.

**Consequences (testable):**
- "How many COTS vs homegrown applications do we have?" routes to SQL analytics.
- "Which applications overlap in Imaging?" routes to graph traversal.
- "Do we have a scheduling tool for BHMG?" routes to Semantic Search (with optional graph filter).
- Compound queries (e.g., "Which Baptist-managed apps support Radiation Oncology?") correctly combine SQL filter with graph traversal.

#### FR-15: Coverage of Epic 5 Sample Questions
The Agent correctly answers all 10 sample questions defined in Jira Epic 5, reproduced here for traceability:

1. How many applications do we have, and how are they distributed by type?
2. How many applications are COTS vs homegrown vs others?
3. Which applications support a specific business function (e.g., Scheduling, Imaging)?
4. Do we already have an application that supports [business function]?
5. Which applications have overlapping or redundant functionality?
6. Which business processes are supported by multiple applications?
7. What architecture types are used across our applications?
8. Which applications are Baptist-managed vs vendor-managed?
9. Which applications are associated with a specific business process?
10. Find applications similar to [description or function]

**Consequences (testable):**
- Each of the 10 questions returns a factually correct response (verifiable against the reference CMDB dataset).
- Responses to questions 1, 2, 7, 8 include exact counts matching SQL analytics output.
- Responses to questions 3, 4, 9, 10 include application names and owners.

#### FR-16: Cited, Explainable Responses
Every Agent response cites the data source that produced the answer (e.g., "Source: SQL analytics — Business Process filter" or "Source: Semantic Search — top match score 0.87").

**Consequences (testable):**
- No Agent response omits a source citation.
- Citations are human-readable (not raw JSON).
- If an Agent response references a specific Application, the Application Name, Business Owner, and T&D Application Owner are included.

#### FR-17: Follow-up Query Context
The Agent retains conversation context for at least 5 turns, enabling follow-up queries that reference results from prior turns (e.g., "Which of those are Baptist-managed?"). `[ASSUMPTION: Context is maintained in-memory for the session; no persistent conversation history in v1.]`

**Consequences (testable):**
- A follow-up query referencing "those" or "them" correctly scopes to the result set from the prior turn.
- Context resets on page reload or new session.

---

### 4.6 React JS Web Interface

**Description:** A browser-based React JS frontend providing the NL query interface, analytics dashboard, and application detail view. The interface serves both technical users (architects) and non-technical stakeholders (clinical directors). The application does not require authentication in v1. `[ASSUMPTION: Application is deployed on an internal network; absence of authentication is acceptable for MVP given internal-only access. To be confirmed with Chakri before go-live.]`

**Functional Requirements:**

#### FR-18: NL Query Interface
The web interface provides a prominent text input field for NL Queries, a submit button, and a results panel that renders the Agent's structured response. The system preserves query history within the session.

**Consequences (testable):**
- Users can submit a query and receive a response without any page reload.
- Response rendering handles both plain-text answers and tabular data (application lists).
- Query history (current session) is scrollable above the active input.

#### FR-19: Analytics Dashboard
The web interface provides a dedicated Analytics view displaying the 5 distribution analytics (FR-9) as charts and tables: application count by type, architecture, business process (top 20), company, and COTS/Homegrown by business process.

**Consequences (testable):**
- All 5 distributions render on page load without additional user action.
- Charts update within 2 seconds of Data Refresh completion.
- Each chart is accompanied by its underlying data table (accessible toggle).

#### FR-20: Application Detail View
A user can click any Application name in a query result or analytics table to open a detail panel showing the full CMDB record for that Application (all 20 fields).

**Consequences (testable):**
- Detail panel opens without page navigation (modal or side panel).
- All 20 CMDB fields are displayed with human-readable labels.
- NULL fields are displayed as "Not specified" rather than blank or "null".

#### FR-21: Redundancy Explorer
The web interface provides a Redundancy Explorer view listing Redundancy Clusters (FR-6), with drill-down into each cluster and CSV export (FR-10).

**Consequences (testable):**
- Redundancy Explorer is accessible from the main navigation.
- Each cluster is expandable to show all member Applications.
- CSV export button is present and triggers file download.

#### FR-22: Data Refresh Trigger
An authorized operator triggers a Data Refresh by uploading a new CMDB XLSX file via a form in the web interface. The interface displays refresh status (running, complete, or failed) and the timestamp of the last successful refresh.

**Consequences (testable):**
- File upload accepts `.xlsx` files only; other file types are rejected with an error message.
- Refresh status updates in real time (polling or websocket).
- On completion, the analytics dashboard auto-reloads with the new data.

---

## 5. Non-Goals (Explicit)

- **Real-time CMDB sync** — No ServiceNow API integration in v1; data enters only via XLSX upload.
- **User authentication / RBAC** — No login, no role-based access control in v1. `[ASSUMPTION: Internal network deployment makes this acceptable. Must be revisited before any external or cloud deployment.]`
- **Write-back to CMDB** — The platform is read-only; it does not update ServiceNow records.
- **Predictive or prescriptive analytics** — The system surfaces what exists and where overlap occurs; it does not recommend decommission decisions.
- **Mobile interface** — Web-only in v1; no responsive mobile layout required.
- **Multi-tenant or public deployment** — Internal use only; single organizational context.
- **Cloud Spanner / GCP infrastructure** — Explicitly replaced by local SQLite stack.
- **Infrastructure dependency graph** — Servers, network, integrations are out of scope; application layer only.

---

## 6. MVP Scope

### 6.1 In Scope
- ETL pipeline: CMDB XLSX → normalized SQLite + ChromaDB
- SQLite relational schema with graph edge tables
- networkx-based graph traversal (redundancy clusters, vendor concentration)
- Distribution analytics (5 pre-built queries)
- Semantic search (sentence-transformers + ChromaDB)
- OpenAI gpt-4o agent with function calling (SQL, graph, semantic tools)
- React JS web interface: NL query, analytics dashboard, application detail, redundancy explorer, data refresh
- CSV export of redundancy clusters
- Coverage of all 10 Epic 5 sample questions

### 6.2 Out of Scope for MVP
- ServiceNow API integration for automated data refresh `[NOTE FOR PM: OQ-1 — resolve with Chakri; this is the most likely v2 addition]`
- User authentication and RBAC `[NOTE FOR PM: Required before any deployment outside the internal network]`
- Write-back / CMDB updates
- Mobile interface
- Business process taxonomy normalization (deferred post-launch per Uday Kumar, 2026-06-12)
- Architecture type inference from description (deferred post-launch)
- Infrastructure / integration dependency graph (v3 vision item)

---

## 7. Success Metrics

**Primary**

- **SM-1**: Agent correctly answers all 10 Epic 5 sample questions — 10/10 on acceptance test. Validates FR-15.
- **SM-2**: Redundancy clusters surfaced — system identifies ≥5 confirmed clusters across Business Processes. Validates FR-6.
- **SM-3**: Semantic search precision — relevant application appears in top-3 results for ≥80% of a defined 20-query test set. Validates FR-12.

**Secondary**

- **SM-4**: Data completeness — 100% of 1,250 CMDB records loaded and queryable after ETL. Validates FR-1, FR-2, FR-5.
- **SM-5**: Query response time — any of the 10 sample questions answered end-to-end in < 10 seconds (including Agent round-trip). Validates FR-18.
- **SM-6**: Stakeholder self-service — a non-technical user (clinical director role, per UJ-3) can use the platform independently to answer a portfolio question, observed in a 30-minute pilot session with Chakri. Validates FR-18, FR-20.

**Counter-metrics (do not optimize)**

- **SM-C1**: Agent hallucination rate — The Agent must not fabricate Application names, counts, or owner information not present in the database. Optimizing for fluency at the cost of factual accuracy is a failure. Counterbalances SM-1, SM-5.
- **SM-C2**: Response verbosity — Agent responses must be ≤ 200 words for simple queries. Optimizing for thoroughness at the cost of readability defeats stakeholder self-service. Counterbalances SM-6.

---

## 8. Open Questions

1. **OQ-1 — Data refresh cadence**: How frequently does the CMDB XLSX need to be re-ingested? Is there a ServiceNow API (or scheduled export) that could automate this for v2? *Owner: Chakri. Revisit condition: before sprint planning.*
2. ~~**OQ-2 — Deployment environment**~~ → **Resolved**: Local machine for MVP demo. No-auth assumption (A-7) is confirmed safe for this deployment scope. Must be revisited before any deployment to a shared or networked server. *Resolved by Uday Kumar, 2026-06-12.*
3. ~~**OQ-3 — OpenAI API key management**~~ → **Resolved**: `.env` file is acceptable for MVP. No organizational secrets management required. Key is provisioned via `.env` at the deployment host. *Resolved by Uday Kumar, 2026-06-12.*
4. **OQ-4 — Acceptance test definition**: Chakri is the MVP acceptance owner — who defines the 20-query semantic search test set (SM-3) and the observed pilot session scenario (SM-6)? *Owner: Chakri + Uday Kumar. Revisit condition: before sprint 1.*

---

## 9. Assumptions Index

- **A-1** (§4.1, FR-1): No ServiceNow API integration in v1 — CMDB data enters the system only via XLSX upload. *(Linked to OQ-1)*
- **A-2** (§4.1, FR-2): No canonical Business Process taxonomy exists in v1 — raw values loaded as-is, data quality cleanup is post-launch.
- **A-3** (§4.1, FR-3): Application Name + Company is the natural key for UUID deduplication across XLSX versions.
- **A-4** (§4.1, FR-4): "Authorized operator" in v1 is anyone with access to the internal deployment — no RBAC.
- **A-5** (§4.4, FR-11): Embedding model is `all-MiniLM-L6-v2` running on CPU; no GPU required for 1,250 records.
- **A-6** (§4.5, FR-17): Agent conversation context is in-memory per session; no persistent conversation history in v1.
- **A-7** (§4.6, FR-18): Application is deployed on a local machine for MVP demo; absence of authentication is confirmed safe for this scope. *(OQ-2 resolved.)*
- **A-8** (Data Governance): Internal deployment means no external data transfer beyond OpenAI API calls. Application descriptions sent to OpenAI do not contain employee PII — the ETL Pipeline excludes owner, engineer, and last-updated-by name fields from all embeddings and Agent prompt payloads.

---

## Cross-Cutting NFRs

- **Performance**: All SQL analytics queries execute in < 2 seconds. All Semantic Search queries return results in < 3 seconds. End-to-end Agent response time (including OpenAI API round-trip) is < 10 seconds for simple queries.
- **Data Integrity**: The ETL Pipeline never silently drops records. All ingestion errors are logged with the record identifier and error reason. On any ETL failure, the prior data state is preserved (no partial writes).
- **Factual Accuracy**: The Agent must not generate Application names, counts, or relationships not present in the database. All Agent claims must be traceable to a specific query result.
- **Portability**: The system runs on any machine with Python 3.10+ and Node.js 18+ without cloud dependencies. SQLite and ChromaDB data files are portable as a directory.

---

## Integration & Dependencies

| Dependency | Type | Version | Notes |
|---|---|---|---|
| CMDB XLSX export | Data source | Baptist Health ServiceNow export schema (20 columns) | Manual upload; v2 may automate via API |
| OpenAI API | External API | gpt-4o (2024-08 or later) | API key via `.env` file; usage billed per token |
| sentence-transformers | Python library | `all-MiniLM-L6-v2` | Local; no external API call at query time |
| ChromaDB | Local vector store | 0.4.x+ | SQLite-backed; no separate server required |
| SQLite | Local database | Built into Python stdlib | No server; single-file database |
| React JS | Frontend framework | 18.x | Standard SPA; served by Python backend or static host |
| Python | Runtime | 3.10+ | ETL, Agent orchestration, API backend |
| Node.js | Frontend build | 18.x LTS | React build toolchain only |

---

## Stakeholders & Approvals

| Role | Name | Responsibility |
|---|---|---|
| Product Owner | Uday Kumar | Requirements sign-off, scope decisions |
| MVP Acceptance Owner | Chakri (T&D) | Acceptance testing, go/no-go decision |
| Primary Users (pilot) | Chakri + TBD (architect, clinical lead) | Pilot session for SM-6 |

MVP is accepted when Chakri signs off on: (a) all 10 Epic 5 questions answered correctly, (b) ≥5 redundancy clusters surfaced, (c) successful pilot session per SM-6.

---

## Data Governance

- **Data classification**: CMDB data contains PII-adjacent fields (employee names: Business Owner, T&D Application Owner, Primary Engineer, Last Updated By). These fields are stored in SQLite and displayed in the UI but are not used for embedding or AI training. `[ASSUMPTION: Internal deployment; no external data transfer beyond OpenAI API calls. Application descriptions sent to OpenAI must not contain employee PII — the ETL pipeline excludes owner/engineer name fields from the text sent to the embedding model and the Agent context.]`
- **Data sent to OpenAI**: Only Application Name, Description, Application Type, Architecture Type, and Business Process are included in OpenAI API calls. Owner names, engineer names, and URLs are excluded from all prompts.
- **Retention**: SQLite and ChromaDB data files persist until manually deleted. No automated retention policy in v1.
- **Data residency**: All data resides on the deployment host. No data is written to external systems other than OpenAI API calls (transient; not stored by OpenAI under standard API terms). `[NOTE FOR PM: Confirm with Baptist Health InfoSec that OpenAI API usage for internal application metadata is permitted under the data governance policy.]`

---

## Constraints & Guardrails

- **No authentication in MVP**: Access is restricted by network boundary only (internal deployment). `[ASSUMPTION A-7 — must be confirmed with Chakri and InfoSec before any deployment on a shared or accessible server.]`
- **OpenAI API dependency**: The Agentic Q&A Interface requires an active OpenAI API key and internet connectivity from the deployment host to `api.openai.com`. The system degrades gracefully if the API is unreachable — SQL analytics and Semantic Search remain functional; only the NL agent is unavailable.
- **XLSX schema dependency**: The ETL Pipeline is coupled to the 20-column Baptist Health CMDB export schema. Schema changes in ServiceNow require an ETL update.
- **OpenAI API key**: Provisioned via `.env` file at the deployment host. No organizational secrets management required for MVP. The `.env` file must not be committed to version control.
- **Cost control**: OpenAI API usage is token-billed. `[ASSUMPTION: MVP usage volume (internal pilot, ~10 users, < 100 queries/day) is within a $50/month budget. No rate limiting or cost cap is implemented in v1.]`
