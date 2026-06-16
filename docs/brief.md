---
title: "IT Application Knowledge Graph — Agentic Intelligence Platform"
status: final
created: 2026-06-12
updated: 2026-06-12
project: BMAD WorkSpace
author: uday kumar
---

# Product Brief: IT Application Knowledge Graph — Agentic Intelligence Platform

## Executive Summary

Baptist Health South Florida manages a portfolio of 1,250 active production applications spanning clinical operations, infrastructure, and administration. Today, knowledge about these applications lives in a CMDB queried by only a handful of technical staff — meaning enterprise architects, business owners, and clinical leads cannot answer basic questions about redundancy, ownership, or capability coverage without raising a ticket.

This platform transforms that static CMDB into a queryable, graph-structured knowledge base with a natural-language interface. By modeling applications and their relationships as a graph and layering semantic search and an AI agent on top, any stakeholder — clinical, operational, or technical — can ask "which applications support Radiation Oncology?" or "do we have redundant scheduling tools?" and get a structured, explainable answer in seconds.

The system is built entirely on local, open-source infrastructure (SQLite, sentence-transformers, ChromaDB, OpenAI API) — eliminating GCP dependency and cloud cost during development and initial deployment, while remaining fully upgradeable if scale demands it.

---

## The Problem

### Organizational Reality
Baptist Health South Florida operates 1,250 production applications across multiple companies and hospital entities. The CMDB is authoritative but inaccessible:

- **Data is trapped in a spreadsheet / ServiceNow UI** — no queryable interface, no graph view, no semantic search
- **Redundancy is invisible** — multiple apps supporting the same business process (e.g., Imaging: 67 apps; Lab: 49 apps) but no automated way to identify overlap
- **Stakeholders write tickets instead of asking questions** — a clinical director wanting to know "do we have a scheduling tool for BHMG?" currently requires a T&D analyst to manually query CMDB data
- **Architecture decisions lack evidence** — solution architects cannot quickly identify what capabilities exist, what architecture patterns are in use, or which vendors are already trusted

### The Cost of the Status Quo
- Application rationalization decisions are made with incomplete information
- Redundant applications continue to be funded and maintained
- New procurement proposals do not account for existing overlapping solutions
- Onboarding new architects or business analysts takes weeks to develop CMDB familiarity

---

## The Solution

A four-layer platform built on the existing CMDB data:

### Layer 1 — Structured Data Store (SQLite)
The CMDB XLSX (1,250 records) is ingested, normalized, and loaded into a SQLite relational database. Applications, application types, architecture types, and business processes become first-class entities with explicit relationships (edge tables). UUID-based identifiers enable stable cross-system references.

### Layer 2 — Graph Analysis Engine (Python + networkx)
Application relationships are modeled as a graph. Graph traversal identifies:
- Applications sharing the same business process (redundancy candidates)
- Applications sharing a vendor/publisher (vendor concentration risk)
- Architectural clustering by type and company

### Layer 3 — Semantic Search (sentence-transformers + ChromaDB)
Application names and descriptions are embedded into a local vector store. Fuzzy, natural-language queries ("find something like Epic but for smaller clinics") return ranked application matches — enabling discovery beyond exact-keyword search.

### Layer 4 — Agentic Q&A Interface (OpenAI API)
A natural language agent orchestrates the graph queries and semantic search to answer stakeholder questions conversationally. Responses are structured, cited, and explainable — not black-box. Sample capabilities:

> "Which applications overlap with Epic in Imaging?"
> "How many COTS vs homegrown applications do we have by business process?"
> "Which apps are Baptist-managed in Radiation Oncology?"
> "Do we already have a scheduling tool for BHMG?"

---

## What Makes This Different

| Dimension | Status Quo (CMDB Spreadsheet) | This Platform |
|---|---|---|
| Access | T&D analysts only | Any stakeholder via NL |
| Query method | Manual filter/sort | Graph + semantic + NL |
| Redundancy detection | Manual, ad hoc | Automated, systematic |
| Architecture insight | None | Pattern analysis across 1,250 apps |
| Deployment | Cloud (ServiceNow) | Local / portable |
| Cost | Ongoing GCP/ServiceNow licensing | Near-zero (open source) |

The real competitive advantage here is not technology — it is **data**. The CMDB is already authoritative and current (last updated May 2026). The work is unlocking it, not collecting it.

---

## Who This Serves

### Primary Users

**Enterprise Architects** — Need to answer "what do we have?" before recommending new solutions. Today they manually search CMDB. They want: application landscape maps, overlap/redundancy reports, architecture type breakdowns by business process.

**T&D Application Owners** — Responsible for rationalization and portfolio decisions. They want: instant answers to portfolio questions, evidence for decommission proposals, vendor concentration analysis.

**Business Stakeholders (Clinical Directors, Operations Leads)** — Want to know what tools support their domain without writing tickets. They need plain-English answers to "do we have X?", "who owns Y?", "what apps touch my department?"

### Secondary Users

**Procurement / Vendor Management** — Identifying vendor duplication and concentration before new contracts.

**New T&D Hires / Architects** — Accelerated onboarding to the application landscape.

---

## Success Criteria

| Signal | Measure |
|---|---|
| Query capability | Agent answers all 10 sample questions from Jira Epic 5 correctly |
| Redundancy identification | System surfaces ≥5 confirmed redundancy clusters across business processes |
| Semantic precision | Semantic search returns relevant app in top-3 results for 80% of test queries |
| Data completeness | 100% of 1,250 CMDB records loaded and queryable |
| Stakeholder self-service | A non-technical user can use the platform to answer a portfolio question independently |
| Time-to-answer | Any of the 10 sample questions answered in < 10 seconds |

---

## Scope

### In (MVP)
- ETL pipeline: XLSX → normalized SQLite schema
- Graph model: Applications, Types, Architecture, Business Processes + edge tables
- Analytics queries: distribution by type/architecture, redundancy detection
- Semantic search: embedding + ChromaDB vector store
- NL agent: OpenAI API-powered Q&A against graph + semantic search
- React JS web interface for query input and results display

### Out of Scope (MVP)
- Real-time CMDB sync (manual refresh is acceptable for v1)
- User authentication / role-based access
- Write-back to ServiceNow CMDB
- Public deployment / multi-tenant
- Integration with live ticketing or incident data
- Mobile interface

### Explicitly Deferred
- Cloud Spanner / GCP migration (may revisit if dataset grows beyond ~50,000 records)
- BigQuery analytics layer
- Vertex AI replacement (OpenAI API covers the NL interface)

---

## Technical Approach Summary

| Component | Technology | Rationale |
|---|---|---|
| Data store | SQLite | Sufficient for 1,250 records; zero infra cost; portable |
| Graph traversal | Python networkx | Full graph analysis; no GQL needed at this scale |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Free, CPU-runnable, strong English quality |
| Vector store | ChromaDB (SQLite-backed) | Native SQLite persistence; simple API |
| NL agent | OpenAI API (`gpt-4o`) | Structured, explainable responses; function-calling capable |
| Frontend | React JS | Browser-based UI; accessible to non-technical stakeholders |
| ETL | Python (pandas + openpyxl + sqlite3) | Already validated against the XLSX |

---

## Vision

If this works, it becomes the institutional memory layer for Baptist Health's application portfolio. Version 2 adds real-time CMDB sync, integration with ServiceNow change tickets, and the ability to ask forward-looking questions ("if we decommission Epic Bridges, what downstream apps are affected?"). Version 3 extends the graph to infrastructure dependencies — servers, integrations, data flows — making it the authoritative source of truth for enterprise architecture decisions.

The long-term outcome: no architect, business owner, or clinical director ever needs to ask T&D "what do we have for X?" again. The platform answers it in seconds, with evidence.

---

## Open Questions

1. **Data refresh cadence**: How often does the CMDB XLSX need to be re-ingested? Is there a ServiceNow API that could automate this?
2. ~~**Stakeholder access model**~~ → **Resolved**: React JS web interface. Pilot user: Chakri (T&D).
3. ~~**Business process taxonomy**~~ → **Resolved**: Use data as-is for MVP; `'-Not Listed-'` cleanup deferred to post-launch.
4. ~~**Architecture type gaps**~~ → **Resolved**: Leave unpopulated fields as-is; not a blocker for MVP.
5. ~~**Success owner**~~ → **Resolved: Chakri** (T&D stakeholder, MVP acceptance owner)
