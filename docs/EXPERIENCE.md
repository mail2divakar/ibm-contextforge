---
name: IT Application Knowledge Graph — Agentic Intelligence Platform
status: final
sources:
  - docs/planning-artifacts/prds/prd-BMAD-WorkSpace-2026-06-12/prd.md
  - docs/planning-artifacts/briefs/brief-BMAD-WorkSpace-2026-06-12/brief.md
created: 2026-06-12
updated: 2026-06-12
---

# IT Application Knowledge Graph — Experience Spine

> Visual identity reference: `DESIGN.md`. All color tokens, typography, component visual specs, and elevation rules live there. This spine owns behavior, information architecture, state patterns, interactions, and accessibility.

## Foundation

Responsive web application. React JS (18.x) frontend, Python/FastAPI backend, SQLite + ChromaDB data layer. No UI component library mandated — implement directly against the `DESIGN.md` token system. Single-tenant, single-organization (Baptist Health South Florida). Internal deployment on a local machine for MVP demo; no authentication required in v1.

Primary surface: desktop/laptop `≥ 1280px`. Responsive to `768px`. Below 768px is not in scope for MVP.

5 named surfaces, fixed left sidebar navigation, white content area, sticky topbar.

## Information Architecture

| Surface | Path | Purpose | Entry points |
|---|---|---|---|
| Dashboard | `/` | Analytics overview — metric cards, distribution charts, architecture breakdown | App load, sidebar Dashboard item |
| Query | `/query` | NL query interface — ask questions, get cited answers | Sidebar Query item, quick-query pills anywhere |
| Analytics | `/analytics` | Full distribution analytics — all 5 pre-built queries with drill-down | Sidebar Analytics item, metric card click-through |
| Redundancy Explorer | `/redundancy` | Cluster list, drill-down, CSV export | Sidebar Redundancy item, metric card click-through |
| Applications | `/applications` | Full application index — searchable, filterable table of all 1,250 records | Sidebar Applications item, Agent result "View all" links |

**Detail panel** is not a surface — it is a full-height overlay that slides in from the right edge over any surface when an Application name is clicked. It does not change the URL in v1.

**Modal stack depth**: one level maximum. The detail panel is the only overlay type in v1. No dialogs stacked on top of the detail panel.

→ Mockup references: `mockups/dashboard.html` · `mockups/query.html` · `mockups/redundancy.html` · `mockups/app-detail.html`. Spine wins on conflict.

## Voice and Tone

Microcopy only. Brand voice and aesthetic posture live in `DESIGN.md`.

The platform speaks to practitioners — enterprise architects and T&D owners — and occasionally to non-technical clinical stakeholders. The voice is **direct, evidence-grounded, and respectful of the user's expertise**. It never oversells findings or hedges obvious facts.

| Do | Don't |
|---|---|
| "88 applications support Radiation Oncology" | "We found some apps that might be related to Radiation Oncology!" |
| "Source: SQL analytics · Business Process filter" | "Based on my analysis of your data..." |
| "5 redundancy clusters found across 1,250 applications" | "Great news! We detected potential overlaps 🎉" |
| "Not specified" for NULL fields | "N/A", "null", "undefined", blank |
| "Refresh data" | "Sync" or "Update" |
| "Ask the Knowledge Graph" | "Chat with your data" |
| "43 applications excluded — no business process assigned" | "Some data is missing" |
| "No applications match 'BHMG Scheduling'. Closest: Baptist Health Medical Group (BHMG) — 29 apps." | "No results found." |

Agent response microcopy: always opens with the direct answer, then evidence, then source citation. Never opens with "As an AI language model..." or "Based on the data provided...".

## Component Patterns

Behavioral specs. Visual specs (colors, radius, shadow, typography) live in `DESIGN.md.Components`.

| Component | Surfaces | Behavioral rules |
|---|---|---|
| **Sidebar nav item** | All | Click navigates to surface. Active item is non-clickable (no redundant reload). Keyboard: `Tab` cycles items, `Enter` navigates. Collapsed state (1024–1279px) shows icon only; tooltip reveals label on hover/focus. |
| **Metric card** | Dashboard, Analytics | Click-through to the relevant surface (e.g., "Redundancy Clusters" card → `/redundancy`). No action on cards that have no drill-down target. Hover: elevation lifts to Level 2 shadow. |
| **Query input** | Query | `Enter` or teal submit button fires the query. `Shift+Enter` inserts newline (for multi-line queries). While the Agent is processing, the input is disabled and shows an animated indicator. On response, input re-enables and focuses. |
| **Quick-query pill** | Query | Click pre-fills the query input with the pill text and fires immediately (no second Enter needed). |
| **Citation chip** | Query | Non-interactive display element. Appears above every Agent result block. `{typography.code}` format. |
| **Agent result table** | Query | Application Name column is a teal link — click opens the detail panel for that application. "Show all N results" link navigates to `/applications` with the filter pre-applied. |
| **Follow-up pill** | Query | Appears below an Agent result. Click appends the suggested follow-up to the query input and fires. Dismissed automatically when a new manual query is submitted. |
| **Conversation history item** | Query | Click replays the selected query (pre-fills and fires). Timestamp shown relative (e.g., "2m ago") until > 24h, then absolute date. |
| **Cluster card** | Redundancy Explorer | Click on the header row expands/collapses. Expanded state shows member application table (Application Name as teal link) and action row. "Export cluster" triggers CSV download for that cluster only. |
| **Data table row** | Applications, Query results | Click anywhere on the row opens the detail panel for that application. Hover reveals a subtle row highlight. |
| **Detail panel** | All (overlay) | Opens from right edge with a 240ms ease-out slide. Backdrop dims main content to 40% opacity. Closes on ✕ click, `Escape` key, or clicking the backdrop. Scroll within the panel is independent of the page scroll. "Find similar apps" button pre-fills the Query input with a semantic search query for that application's description and navigates to `/query`. |
| **Data Refresh form** | Dashboard (topbar action) | Click "Refresh Data" opens a small inline panel (not a full modal) with a file upload input. Accepts `.xlsx` only — other types show inline error "Only .xlsx files are accepted." Upload triggers the ETL pipeline. Status indicator in the topbar replaces the button text with a spinner during processing, then shows "Updated · Jun 12, 2026 · 1,250 apps" on success. |
| **Filter bar** | Analytics, Redundancy, Applications | Dropdown filters for Business Process, Application Type, Company, Baptist Managed. Filters are applied immediately on change (no separate "Apply" button). Active filter count shown as a badge on the filter icon. "Clear filters" link appears when any filter is active. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| **Cold load** | All | Skeleton loaders matching the expected layout (metric card skeletons, table row skeletons). Resolves on first data fetch. |
| **Agent processing** | Query | Query input disabled. Animated teal dot indicator below the input: "Querying 1,250 applications…". Response replaces the indicator; processing time shown in the citation chip. |
| **Agent error** | Query | Inline error below input: "Couldn't reach the AI agent. SQL analytics and search are still available — try the Analytics or Applications surfaces." Destructive color `{colors.destructive}`. Retry link. |
| **Empty query results** | Query | "No applications match '[query]'. Closest business process: [name] — [N] apps." with a teal "Search [name]" suggestion pill. |
| **Redundancy no clusters** | Redundancy Explorer | Display text: "No redundancy clusters found for the current filters." with "Clear filters" CTA. |
| **Data Refresh success** | Dashboard topbar | "Updated · [date] · [N] apps" replaces the Refresh button for 5 seconds, then reverts to "Refresh Data". Analytics dashboard reloads data automatically. |
| **Data Refresh failure** | Dashboard topbar | "Refresh failed — check the file format." in `{colors.destructive}`. Retry link. Prior data remains intact. |
| **ETL warning (partial load)** | Dashboard topbar | Amber warning chip: "[N] records skipped — see ETL log". Click opens a small log drawer listing skipped records and reasons. |
| **Detail panel loading** | Overlay | Skeleton of the full detail panel content (two skeleton blocks for Overview, Ownership grid, Graph Relationships). |
| **NULL field in detail panel** | Detail panel | Display "Not specified" in `{colors.muted-foreground}`. Never blank, never "null". |
| **Applications surface empty** | Applications | "No applications match the current filters." with "Clear filters" CTA. |
| **OpenAI API unreachable** | Query | Banner at top of Query surface: "AI agent is offline. SQL analytics and semantic search are available — use the Analytics and Applications surfaces." Banner dismissible. NL query input is disabled; quick-query pills route to Analytics instead. |

## Interaction Primitives

**Mouse-primary.** The MVP pilot audience includes non-technical clinical stakeholders — keyboard shortcuts are supplemental, not primary. All interactions must be completable by click/tap alone.

**Keyboard support (supplemental):**
- `Tab` / `Shift+Tab` — cycle focus through interactive elements in DOM order
- `Enter` — activate focused button, link, or submit focused form
- `Escape` — close detail panel, dismiss filter dropdowns, clear focus from query input
- `/` — focus the query input from any surface (when not already in an input)

**Click targets:** minimum 44×44px touch target on all interactive elements (buttons, nav items, table rows, cluster card headers). Application Name links in tables have a minimum 200px clickable width.

**Transitions:**
- Detail panel slide-in: `transform: translateX(0)` from `translateX(100%)`, `240ms ease-out`
- Sidebar collapse: `width` transition `180ms ease-in-out`
- Card hover elevation: `box-shadow` transition `120ms ease`
- Skeleton to content: `opacity` fade `200ms`

**Banned patterns:**
- Infinite scroll — paginate at 50 rows
- Drag-to-reorder — not in v1
- Hover-only affordances on Application Name links (must be visually indicated at rest via color)
- Auto-refreshing data without user intent
- Modal stacks deeper than 1 level

## Accessibility Floor

Behavioral. Visual contrast ratios live in `DESIGN.md` (all color pairs verified at WCAG AA: `#1D3269` on white = 11.1:1, `#00A8CC` on white = 3.9:1 — acceptable for large/bold text and UI components, not for body copy. Body text uses `#0F172A` on white = 19.1:1).

- **WCAG 2.1 AA** across all surfaces.
- Sidebar nav: `role="navigation"`, `aria-label="Main navigation"`. Active item: `aria-current="page"`.
- Detail panel: `role="dialog"`, `aria-label="Application detail: [name]"`. Focus trapped within the panel while open. Focus returns to the triggering element on close.
- Agent result tables: `role="table"`, column headers `scope="col"`. Application Name links have descriptive `aria-label="View [app name] details"`.
- Query input: `aria-label="Ask the Knowledge Graph"`. Processing state: `aria-busy="true"` on the input container.
- Skeleton loaders: `aria-hidden="true"` — screen readers skip them.
- Filter dropdowns: keyboard-operable, `aria-expanded` on trigger, `aria-activedescendant` on open list.
- Color is never the sole indicator of state — badges use text labels, not just color.
- Focus rings: visible at all times on keyboard navigation. `outline: 2px solid {colors.accent}` with `outline-offset: 2px`.

## Responsive & Platform

| Breakpoint | Behavior |
|---|---|
| `≥ 1280px` | Sidebar expanded (240px). 4-column metric grid. Two-column chart layout (60/40). Full detail panel (480px). |
| `1024–1279px` | Sidebar collapses to icon-only (64px). Metric grid stays 4-column. Detail panel width reduces to 400px. |
| `768–1023px` | Sidebar becomes a slide-in drawer triggered by hamburger icon in topbar. Metric grid drops to 2-column. Chart layout stacks to single column. Detail panel goes full-width. |
| `< 768px` | Not in scope for MVP demo. |

The topbar "Refresh Data" button is always visible at all breakpoints — data refresh is an operator-level action that must never be hidden in a menu.

## Inspiration & Anti-patterns

**Lifted from Linear:** clean sidebar with tight active state indicator (left border strip), no decorative chrome, data tables with hover reveal.

**Lifted from Vercel dashboard:** white content area with subtle card elevation, metric cards as first-class navigation elements, citation-style source labels.

**Lifted from Retool:** agent result tables with inline click-to-drill, filter bars with immediate apply, detail panels as overlays rather than new pages.

**Rejected — chat-bubble UI for Agent responses:** responses are structured data (tables, counts, citations), not conversational text. Rendering them as chat bubbles buries the evidence and makes copy/paste harder for architects writing memos.

**Rejected — dark sidebar text on white background:** the glassmorphism sidebar on `#1D3269` is the brand anchor. A light sidebar loses the KSquare identity.

**Rejected — Kanban / card wall for Applications surface:** 1,250 records are a table, not a board. Table view with sort/filter is the correct pattern.

**Rejected — auto-refresh on a timer:** CMDB data is updated manually via XLSX upload. Auto-refresh would create false confidence that data is always current.

## Key Flows

### Flow 1 — Alex checks capability overlap before a procurement recommendation (UJ-1)

1. Alex opens the app in a browser. Dashboard loads — metric cards show 1,250 apps, 5+ redundancy clusters.
2. Alex clicks the sidebar "Query" item. The NL query surface loads with the input focused.
3. Alex types: "Do we already have a scheduling application for BHMG?" and hits `Enter`.
4. Teal dot indicator: "Querying 1,250 applications…". Agent routes to Semantic Search + graph filter.
5. Citation chip appears: "Semantic Search + SQL filter · 8 results · 1.2s". Table shows 8 applications tagged to "Baptist Health Medical Group (BHMG)" business process.
6. Alex clicks "3D Scanner" — detail panel slides in from the right. Alex reads Business Owner: Alonso Gutierrez.
7. Alex types follow-up: "Which of these are Baptist-managed?" — follow-up pill was already present; Alex clicks it instead.
8. **Climax:** New result table: 3 of 8 applications are Baptist-managed. Alex has evidence in under 3 minutes. He copies the application names into his recommendation memo.
9. Alex closes the detail panel with `Escape`. Query surface remains with both exchanges in the conversation history.

*Failure:* Agent returns zero results for "BHMG Scheduling" — the system shows "No match. Closest business process: Baptist Health Medical Group (BHMG) — 29 apps" with a suggestion pill. Alex clicks the pill and gets the broader result set.

---

### Flow 2 — Chakri runs a redundancy analysis for the Imaging rationalization review (UJ-2)

1. Chakri opens the app. Dashboard shows Imaging: 67 apps in the business process bar chart.
2. Chakri clicks the Imaging bar — navigates to `/analytics` with Business Process filter pre-set to "Imaging".
3. Analytics surface loads: 67 Imaging applications, broken down by type (62 COTS, 3 Homegrown, 2 unclassified) and architecture.
4. Chakri clicks sidebar "Redundancy Explorer". Filter bar inherits the Imaging filter.
5. Imaging cluster card shows at the top, expanded: 67 member apps with a table showing the top 10.
6. Chakri clicks "Export cluster" — CSV downloads immediately: Business Process, Application Name, Type, Architecture, Baptist Managed, Business Owner, T&D Owner.
7. **Climax:** CSV opens in Excel. Chakri has a full ranked list for the rationalization review meeting, assembled in under 5 minutes without a T&D ticket.

*Failure:* CSV export fails (disk permissions) — inline error on the Export button: "Export failed. Try again." Retry succeeds.

---

### Flow 3 — Maria asks whether a new clinical app is needed (UJ-3)

1. Maria opens the app — she has never used it before. The sidebar is visible; she sees "Query" and clicks it.
2. The Query surface loads. Heading: "Ask the Knowledge Graph." Subheading: "Query 1,250 Baptist Health applications in plain English." The interface is immediately self-explanatory.
3. Maria types: "Do we have a dosimetry QA application for Radiation Oncology?" and clicks the teal "Ask" button.
4. Agent responds: citation chip "Semantic Search · 3 results · 0.8s". Table: 3D Scanner (ADAPTIIV MEDICAL TECHNOLOGIES), plus 2 more Radiation Oncology dosimetry tools.
5. Maria clicks "3D Scanner" — detail panel opens: full record including Business Owner Alonso Gutierrez and support group "CARETech Sustainment Radiation Oncology."
6. **Climax:** Maria sees the tool already exists and who owns it. She shares the detail panel content with the vendor as evidence. No ticket raised. Vendor meeting redirected.

*Failure:* No semantic match for "dosimetry QA" — zero results returned. Agent shows: "No applications found matching 'dosimetry QA'. Similar business processes: Radiation Oncology (88 apps)." Maria clicks the suggestion and finds the app manually in the broader list.
