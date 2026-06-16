# UI Contract: IT Knowledge Graph Ingestion Pipeline

**Feature**: Epic 1 — Platform Foundation
**Date**: 2026-06-12
**Source**: `docs/mockups/` (dashboard.html, applications.html, app-detail.html, query.html, analytics.html, redundancy.html)

---

## Design System

### Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--primary` | `#1D3269` | Sidebar bg, headings, nav active indicator, metric values |
| `--accent` | `#00A8CC` | Active nav border, links, CTA buttons, filter active state |
| `--surface` | `#F8FAFC` | Page background, table header bg, input bg |
| `--bg` | `#FFFFFF` | Cards, panels, topbar, table rows |
| `--border` | `#E2E8F0` | All borders and dividers |
| `--fg` | `#0F172A` | Primary text |
| `--muted` | `#64748B` | Secondary text, labels, placeholders |
| `--success` | `#10B981` | Active/Yes status indicators |
| `--warning` | `#F59E0B` | Overlap/risk/warning states |
| `--error` | `#EF4444` | Vendor-not-managed indicator |

### Typography

Font: **Inter** (Google Fonts: 300, 400, 500, 600, 700, 800). System fallback: `system-ui, -apple-system, sans-serif`.

| Role | Size | Weight |
|------|------|--------|
| Page title (topbar) | 17px | 700 |
| Section heading | 16px | 700 |
| Body / table cells | 13–13.5px | 400–500 |
| Labels (uppercase) | 10–12px | 600 |
| Metric value | 42px | 800 |
| App name / section value | 13.5–20px | 600–700 |

### Spacing & Shape

- **Viewport min-width**: 1440px
- **Card radius**: 16px
- **Button radius**: 8px
- **Nav item radius**: 10px
- **Pill/badge radius**: 20px
- **Card padding**: 24px
- **Content padding**: 32px
- **Card shadow**: `0 2px 8px rgba(29,50,105,0.06)`
- **Accent button shadow**: `0 2px 8px rgba(0,168,204,0.30)`

---

## Layout Shell

### Structure

```
┌──────────────┬─────────────────────────────────────────┐
│              │  Topbar (56–60px, sticky)               │
│  Sidebar     ├─────────────────────────────────────────┤
│  (240px)     │                                         │
│              │  Content area (32px padding)            │
│              │                                         │
└──────────────┴─────────────────────────────────────────┘
```

Shell: `display: flex; min-height: 100vh; width: 1440px; margin: 0 auto`.

### Sidebar (Full — 240px)

Used on: Dashboard, Applications, Analytics, Redundancy, Query (full-width variant).

- Background: `rgba(29,50,105,0.88)` with `backdrop-filter: blur(16px)`
- Right border: `1px solid rgba(255,255,255,0.12)`
- Box shadow: `4px 0 24px rgba(29,50,105,0.18)`
- Position: `sticky top: 0; height: 100vh` (stays fixed while content scrolls)

**Logo area** (padding: 28px 24px 24px):
- Brand text: "KSquare Group" — 18px, 700, `#FFFFFF`
- Sub text: "AppGraph" — 11px, 500, `rgba(0,168,204,0.90)`, letter-spacing 2px, uppercase

**Nav items** (padding: 10px 14px, gap: 12px, radius: 10px):

| State | Background | Left border | Color |
|-------|-----------|-------------|-------|
| Default | transparent | 3px solid transparent | `rgba(255,255,255,0.65)` |
| Hover | `rgba(255,255,255,0.08)` | transparent | `rgba(255,255,255,0.90)` |
| Active | `rgba(0,168,204,0.20)` | 3px solid `#00A8CC` | `#FFFFFF`, weight 600 |

Nav items (5 routes):

| Route | Icon | Label |
|-------|------|-------|
| `/` | 🏠 | Dashboard |
| `/query` | 💬 | Query |
| `/analytics` | 📊 | Analytics |
| `/redundancy` | 🔗 | Redundancy |
| `/applications` | 📋 | Applications |

**Avatar footer** (margin-top: auto, padding: 16px, border-top: 1px `rgba(255,255,255,0.10)`):
- 36px circle, gradient `linear-gradient(135deg, #00A8CC, #1D3269)`, initials (weight 700)
- Name: 13px, weight 600, `rgba(255,255,255,0.92)`
- Role: 11px, `rgba(255,255,255,0.45)`

### Sidebar (Icon — 64px)

Used on: app-detail panel overlay context. Icon-only icons with tooltip `title` attributes, active state uses absolute left-edge indicator (`::after` pseudo element: 3px wide, 24px tall, `#00A8CC`).

### Topbar

Height: 56px (60px on Query page). Background: `#FFFFFF`. Border-bottom: `1px solid #E2E8F0`. Position: sticky, z-index 100.

- **Left**: Page title — 17px, weight 700, `#0F172A`
- **Right**: metadata + action buttons
  - Metadata: "Last refresh: **Jun 12, 2026** · 1,250 apps loaded" — 12.5px, `#64748B`
  - Primary CTA: "Refresh Data" — accent bg, white text, 8px radius, shadow

---

## Pages

### Dashboard (`/`)

**Topbar title**: "Analytics Dashboard"

#### Metric Cards Row (4 × equal-width grid)

Cards use `border-radius: 16px`, `border: 1px solid #E2E8F0`, 3px gradient top bar (`linear-gradient(90deg, #1D3269, #00A8CC)`, opacity 0.7).

| Card | Value | Sub-text |
|------|-------|---------|
| Total Applications | **1,250** | "All active" badge (green) + "In Production" |
| Application Types | **2** | "COTS: 765 · Homegrown: 26" badge (teal) + "Unclassified: 459" |
| Redundancy Clusters | **5+** | "Overlap detected" badge (warning) + "2+ apps per process" |
| Business Processes | **47** | "Unique processes covered" |

Metric value: 42px, weight 800, `#1D3269`, letter-spacing -2px.

#### Charts Row (60/40 split)

**Left card — "Distribution by Business Process"**:
- Section badge: "Top 8 of 47 processes"
- Horizontal bar chart. Each bar row: 3-column grid (180px label | track | 48px count).
- Bar track: height 28px, `#F8FAFC` bg, 6px radius.
- Bar fill: `#1D3269`, turns `#00A8CC` on hover + tooltip chip ("67 apps · 5.4%").
- Label: 13px, weight 500; Count: 13px, weight 700, `#1D3269`.
- Rows separated by 1px `rgba(226,232,240,0.5)` border.

Sample data (top 5): Technology & Digital (161), Radiation Oncology (88), TD Infrastructure (82), Imaging (67), Laboratory (49).

**Right card — "Application Type Breakdown"**:
- SVG donut chart: radius 60, stroke-width 22, rotated -90deg (12 o'clock start).
- Segments: COTS `#1D3269` (61.2%), Homegrown `#00A8CC` (2.1%), Unclassified `#CBD5E1` (36.7%).
- Center label: "1,250" (28px, weight 800) + "Total Apps" (11px, muted).
- Legend below donut: dot + name + count + percentage (right-aligned).

#### Architecture Types Row (full-width card)

6-column grid: Client Server (66), Platform Host (62), Web Based (20), N-Tier (4), Other (5), Unclassified (1,093).

Each item: name (12.5px, 600) → count (22px, 800, `#1D3269`) → 6px progress bar (`#00A8CC` fill, `#CBD5E1` for Unclassified) → percentage (11px, muted). Progress bars sized relative to max (Client Server = 100%).

---

### Applications (`/applications`)

**Topbar title**: "Applications"

#### Search + Filter Bar

Full-width bar below topbar. Background `#FFFFFF`, border-bottom, padding 12px 32px.

- **Search input** (flex: 0 0 320px): `#F8FAFC` bg, `#E2E8F0` border, 10px radius, 36px height. Left icon 🔍. Right: Cmd+K keyboard shortcut hint. Focus: border `#00A8CC`, `box-shadow: 0 0 0 3px rgba(0,168,204,0.12)`.
- **Filter dropdowns** (4): Business Process, Application Type, Baptist Managed, Company. Base: `#F8FAFC` bg, `#E2E8F0` border, 8px radius. Active filter: `#00A8CC` border, `rgba(0,168,204,0.06)` bg, primary color text, optional badge dot.
- **Clear filters** link: 12.5px, accent color.
- **Results count** (right): "**67** of 1,250 applications"
- **Sort toggle button**: border, 7px radius, active state in accent.

#### Applications Table

Full-width, sticky header, scrollable body.

**Columns**: Application Name | Company | Application Type | Business Process | Baptist Managed | Business Owner | (action)

Header: `#F8FAFC` bg, 11.5px uppercase, weight 600, `#64748B`. Sortable (sort indicator suffix). Active sort: `#1D3269`.

Row: height 52px, `border-bottom: 1px solid rgba(226,232,240,0.6)`. Hover: `rgba(248,250,252,0.8)` bg + chevron appears. Selected: `rgba(0,168,204,0.06)` bg.

Cell specs:
- **Application Name**: teal link (`#00A8CC`), weight 600, 13.5px. `aria-label="View {name} details"`.
- **Application Type badge**: COTS — `rgba(29,50,105,0.10)` bg, `#1D3269` color. Homegrown — `rgba(0,168,204,0.12)` bg. Unclassified — surface bg + border.
- **Baptist Managed**: Yes — `rgba(16,185,129,0.12)` bg, `#047857`. No — `rgba(226,232,240,0.8)` bg, muted.
- **Truncated text**: max-width 200px, `text-overflow: ellipsis`.
- **NULL values**: "Not specified" in muted italic.
- **Row chevron** (last col): `opacity: 0`, becomes 1 on row hover.

#### Pagination Bar

Full-width, `border-top: 1px solid #E2E8F0`, padding 12px 32px.

- Left: "Showing **1–10** of **67** applications" + page-size selector (10/25/50 per page).
- Right: Prev button (disabled on page 1) | numbered page buttons | Next button.
- Page button: 32×32px, 7px radius. Active page: `#1D3269` bg, white. Hover: surface bg + accent border.

---

### Detail Panel (slide-in overlay)

Triggered by clicking any Application Name link. Appears on top of the Applications table (or Query results).

- **Width**: 480px
- **Position**: fixed right edge, full viewport height
- **Backdrop**: `rgba(15,23,42,0.40)` covering the rest of the viewport
- **Animation**: `translateX(100%) → translateX(0)`, 0.3s, `cubic-bezier(0.16, 1, 0.3, 1)`
- **Shadow**: `-8px 0 32px rgba(29,50,105,0.15)` (or `-8px 0 40px rgba(29,50,105,0.12)`)
- **ARIA**: `role="dialog"`, `aria-label="Application detail: {application_name}"`
- **Dismiss**: ✕ close button, Escape key, backdrop click — focus returns to triggering link

#### Panel Header (padding: 20–24px, border-bottom)

- Application name: 17–20px, weight 700, `#1D3269` or `#0F172A`
- Publisher/subtitle: 14px, `#6B7280`
- Status pills row: "✓ In Production" (green badge), Application Type (navy solid badge), Business Process (teal badge)
- Close button (✕): 32×32px, 8px radius, `#F8FAFC` bg. Hover: `#FEE2E2` bg, red color.

#### Panel Body (scrollable, padding: 24px, thin 5px scrollbar)

Sections separated by section title divider (11px, uppercase, `#1D3269`, weight 700, with `::after` horizontal line extending to panel edge).

**Overview**:
- Description field: styled box (bg `#F8FAFC`, border `#E2E8F0`, 8px radius, 12px padding), 13px, line-height 1.65
- Architecture Type: field-label + field-value (11px uppercase label / 13px value)
- Application URL: field-value

**Ownership** (2-column grid with inner borders):
- Grid with 1px `#E2E8F0` borders between cells
- Fields: Business Owner | T&D Application Owner | Primary Engineer | Support Group | Company | Baptist Managed
- Baptist Managed "No": amber warning dot (7px circle, `#F59E0B`) + "No" in `#B45309`
- Last Updated: full-width cell, 12px, italic, `#6B7280`

**Graph Relationships** (Epic 1 scope: display only):
- Process chip (teal): `#E0F7FA` bg, `#007A96` text, `#80DEEA` border
- Type chip (navy): `#EFF6FF` bg, `#1D3269` text, `#BFDBFE` border
- Relationship hint box: gradient `#F0F9FF → #E0F7FA` bg, `#B2EBF2` border, 10px radius
  - Text: "**N other apps** share the _Business Process_ business process cluster."
  - Link: "View cluster →" (`#00A8CC`, weight 600)

**Record Metadata** (in applications.html variant):
- Active status, Last Updated date, Last Updated By, Application ID (monospace, 11px, truncated UUID)

#### Panel Footer (padding: 16px 24px, border-top)

- Primary button: "🔍 Find similar apps" — accent bg, white, weight 600, flex: 1 or full-width
- Secondary button: "📄 Open in CMDB" — white bg, `#1D3269`, `#E2E8F0` border

---

### Query (`/query`)

**Topbar title**: "Knowledge Graph Query"
**Topbar subtitle** (breadcrumb style): "Powered by SQL Analytics + Semantic Search"
**Topbar actions** (right): Export Results, Share Query, Query History — secondary border buttons

#### Two-Column Layout

`display: flex; gap: 24px; padding: 32px`.

**Left — Query column** (flex: 1):

**Hero query box** (max-width 720px, centered, 20px radius, 36px 40px 32px padding):
- Eyebrow: pulse dot animation + "1,250 Applications Indexed · Live" (`#00A8CC`, 11px, uppercase)
- h1: "Ask the Knowledge Graph" — 24px, weight 700
- Description: "Query 1,250 Baptist Health applications in plain English…" — 14px, `#64748B`
- Query input: full-width, padding `16px 160px 16px 50px`, 16px radius, `#E2E8F0` border, shadow. Focus: `#00A8CC` border + 3px ring.
- "✨ Ask" button: inside input right (absolute position), `#00A8CC` bg, 10px radius
- Quick pills (flex-wrap): "📊 App distribution by type", "🔗 Find redundant apps", "🏥 Baptist-managed apps", "🔍 Search by function" — pill style, hover turns accent

**Results card** (max-width 720px, 16px radius):
- Header: "Query Result" label (11px, uppercase, `#94A3B8`) + query text (15px, weight 600) + count badge (green)
- Citation chip: `rgba(0,168,204,0.10)` bg, 20px radius — "📊 SQL Analytics + Semantic Search · 88 results · 0.8s"
- Results table:
  - Columns: Application Name (with 24×24px icon square), Type (badge), Baptist Managed (colored), Business Owner, T&D Owner
  - Type badges: COTS (`#EEF2FF`/indigo), Homegrown (`#FFF7ED`/orange), SaaS (`#F0FDF4`/green), Hybrid (`#FDF4FF`/purple)
  - Managed Yes: `#16A34A`; No: `#94A3B8`
- Footer: "↗ Show all N results" link + follow-up suggestion pill

**Right — History panel** (width: 300px, glassmorphic card):
- Background: `rgba(255,255,255,0.72)`, `backdrop-filter: blur(12px)`, 16px radius
- Header: "Recent Queries" + "Clear all" link
- Stats row: 2-column grid — "24 Queries Today" | "1.2s Avg Response"
- History list: icon + query text (truncated, weight 500) + timestamp + result count
- Suggested Queries section: 3 pills (full-width, left-aligned)

---

### Analytics (`/analytics`)

**Topbar title**: "Analytics"

#### Filter Bar (below topbar, separate from content)

White bg, border-bottom, padding 12px 32px. Active filter shows `#00A8CC` border + badge dot (18px circle, accent). "Showing N of 1,250 apps" count chip (right).

#### Content Layout (32px padding, 24px gap)

**Row 1** — 2-column grid:
- **Application Type** card: mini donut (160px) + legend
- **Architecture Types** card: 3-column mini grid (name + count + mini bar + %)

**Row 2** — Full-width card: "Distribution by Business Process"
- 2-column bar chart layout (8 processes per column), active/filtered process highlighted in accent
- "Show table ↓" toggle link on each card header

**Row 3** — 2-column grid:
- **Distribution by Company** card: horizontal bar chart (top 5 entities: Baptist Health South Florida 987, Doctors Hospital 109, South Miami Hospital 59, Homestead Hospital 48, Mariners Hospital 47)
- **Baptist Managed vs Vendor Managed** card: donut (Baptist 34.2% navy, Vendor 61.0% teal, Unknown 4.7% muted)

**Row 4** — Full-width card: "Vendor Concentration" (publishers with 3+ apps)
- Ranked list: #1 Microsoft (12 apps), #2 Epic Systems (8), #3 Philips Healthcare (6), #4 3M (3), #5 Cerner (3)
- Each row: rank + vendor name + app pills (truncated with "+ N more" accent link) + count badge

---

### Redundancy Explorer (`/redundancy`)

**Topbar**: breadcrumb "Analysis › Redundancy Explorer", search bar, notification/help icon buttons

#### Page Header

- h1: "Redundancy Explorer" (24px, weight 700, `#1D3269`)
- Subtitle: "Applications sharing the same business process — rationalization candidates." (14px, `#64748B`)
- Right actions: "⬇ Export CSV" button (accent) + "5 clusters found" badge (amber `#F59E0B` bg)

#### Stats Row (4 cards, flex, gap: 16px)

| Icon bg | Label | Value | Sub-text |
|---------|-------|-------|---------|
| blue | Redundancy Clusters | **5** | business process groups |
| amber | Overlapping Applications | **370** | across all clusters |
| red | High-Risk Redundancy | **2** | clusters ≥ 60 apps |
| teal | Excluded (NULL Process) | **43** | records omitted |

Each stat card: 42×42px icon (colored bg, 10px radius) + label (12px, muted) + value (22px, weight 800, `#1D3269`) + sub-text (11px, muted).

#### Filter Bar (card style, 12px radius)

"Filter by:" label + Business Process dropdown + App Types dropdown + "Baptist Managed only" checkbox (accent-color) + Sort by dropdown (right-aligned).

#### Clusters List (expandable accordion cards)

Each cluster card: 16px radius, `0 2px 12px rgba(29,50,105,0.06)` shadow.

**Cluster header** (padding: 18px 20px, cursor pointer):
- 38×38px icon (gradient bg)
- Title (15px, weight 700) + subtitle (12px, `#94A3B8`)
- Risk badge: High — `#FEE2E2` bg, `#B91C1C` text; Medium — `#FEF3C7` bg, `#92400E` text
- App count pill: `#FEF3C7` bg, `#92400E`, weight 700
- Chevron: rotates 180° when open

**Cluster body** (expanded):

Table columns: Application Name | Type | Baptist Managed | Rationalization Risk

- Type: `rgba(0,168,204,0.08)` bg badge
- Baptist Managed: ✓ Yes (`#10B981`) | ✗ No (`#EF4444`)
- Risk: High (`#FEE2E2`/`#B91C1C`) | Medium (`#FEF3C7`/`#92400E`)

"+ N more applications →" link (accent, 13px, weight 600).

Cluster actions row (border-top): "📋 View all N apps" | "⬇ Export cluster" | "🗺 Dependency map"

**Cluster body** (collapsed): "Click to expand and view all N overlapping applications in this cluster" (muted, 13px, dot separator)

**5 clusters** (sorted by app count):
1. Technology and Digital — 161 apps, High risk
2. Radiation Oncology — 88 apps, High risk
3. Imaging — 67 apps, High risk
4. Laboratory — 49 apps, Medium risk
5. Health Information Management — 5 apps, Medium risk

#### Hint Row

Amber warning (`#FFFBEB` bg, `#FDE68A` border): "Showing top redundancy clusters. Applications with NULL business process are excluded (43 records)."

---

## Component Inventory

All components below map to files in `frontend/src/components/` and `frontend/src/surfaces/`.

| Component | File | Used By |
|-----------|------|---------|
| Sidebar (full) | `Sidebar.tsx` | All surfaces |
| Topbar | `Topbar.tsx` | All surfaces |
| MetricCard | `MetricCard.tsx` | Dashboard, Redundancy |
| HorizontalBarChart | `HorizontalBarChart.tsx` | Dashboard, Analytics |
| DonutChart | `DonutChart.tsx` | Dashboard, Analytics |
| ArchitectureGrid | `ArchitectureGrid.tsx` | Dashboard, Analytics |
| FilterBar | `FilterBar.tsx` | Applications, Analytics |
| SearchInput | `SearchInput.tsx` | Applications |
| ApplicationsTable | `ApplicationsTable.tsx` | Applications |
| PaginationBar | `PaginationBar.tsx` | Applications |
| DetailPanel | `DetailPanel.tsx` | Applications, Query results |
| RefreshForm | `RefreshForm.tsx` | Topbar (all surfaces) |
| QueryHero | `QueryHero.tsx` | Query |
| ResultsCard | `ResultsCard.tsx` | Query |
| HistoryPanel | `HistoryPanel.tsx` | Query |
| ClusterCard | `ClusterCard.tsx` | Redundancy |
| StatCard | `StatCard.tsx` | Redundancy |
| VendorConcentration | `VendorConcentration.tsx` | Analytics |

---

## Epic 1 Scope vs. Later Epics

Epic 1 implements only the surfaces and components required by Stories 1.1–1.6:

| Surface | Epic 1 | Later |
|---------|--------|-------|
| Dashboard — 4 metric cards | ✅ Full | — |
| Dashboard — bar + donut charts | ❌ Shell only ("Coming soon") | Epic 2 |
| Applications — table + filters + pagination | ✅ Full | — |
| Detail Panel — 20-field display + footer | ✅ Full | — |
| Query — hero input + results table | ❌ Shell only | Epic 4 |
| Analytics — all charts | ❌ Shell only | Epic 2 |
| Redundancy — cluster cards | ❌ Shell only | Epic 2 |

The shell surfaces (Query, Analytics, Redundancy) must match the mockup sidebar/topbar/nav exactly and show a "Coming soon" placeholder where chart/query content appears. This ensures navigation is consistent from day one and the overall application feels cohesive even before the feature surfaces are complete.

---

## Accessibility Requirements (WCAG 2.1 AA)

| Element | Requirement |
|---------|-------------|
| Sidebar nav | `role="navigation"`, focus-visible ring on all nav items |
| Detail panel | `role="dialog"`, `aria-label`, focus trap while open, Escape closes |
| Table | `role="table"`, sortable columns announce sort state |
| Filter dropdowns | Native `<select>` elements for screen reader compatibility |
| Application Name links | `aria-label="View {application_name} details"` |
| Skeleton loaders | `aria-hidden="true"` while loading |
| Color alone | Never sole differentiator — badges always include text label |
| Contrast | All text on colored backgrounds meets 4.5:1 ratio (Inter on `#1D3269` backgrounds uses white `#FFFFFF`) |
