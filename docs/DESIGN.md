---
name: IT Application Knowledge Graph — Agentic Intelligence Platform
status: final
sources:
  - docs/planning-artifacts/prds/prd-BMAD-WorkSpace-2026-06-12/prd.md
  - docs/planning-artifacts/briefs/brief-BMAD-WorkSpace-2026-06-12/brief.md
created: 2026-06-12
updated: 2026-06-12
colors:
  primary: '#1D3269'
  primary-foreground: '#FFFFFF'
  primary-dark: '#0F1C3D'
  primary-mid: '#243E7D'
  primary-surface: '#EEF2FB'
  accent: '#00A8CC'
  accent-foreground: '#FFFFFF'
  accent-light: '#E0F7FC'
  accent-dark: '#007A99'
  background: '#FFFFFF'
  surface: '#F8FAFC'
  surface-glass: 'rgba(255, 255, 255, 0.70)'
  sidebar-glass: 'rgba(29, 50, 105, 0.88)'
  border: '#E2E8F0'
  border-subtle: '#F1F5F9'
  foreground: '#0F172A'
  muted: '#475569'
  muted-foreground: '#94A3B8'
  success: '#10B981'
  success-surface: '#ECFDF5'
  warning: '#F59E0B'
  warning-surface: '#FFFBEB'
  destructive: '#EF4444'
  destructive-surface: '#FEF2F2'
typography:
  display:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '36px'
    fontWeight: '700'
    lineHeight: '1.15'
    letterSpacing: '-0.02em'
  heading-lg:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '24px'
    fontWeight: '600'
    lineHeight: '1.25'
    letterSpacing: '-0.015em'
  heading-md:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '18px'
    fontWeight: '600'
    lineHeight: '1.35'
    letterSpacing: '-0.01em'
  heading-sm:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '14px'
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: '0'
  body:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '14px'
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '13px'
    fontWeight: '400'
    lineHeight: '1.55'
  label:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '12px'
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: '0.01em'
  metric:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '36px'
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: '-0.02em'
  metric-sm:
    fontFamily: 'Inter, system-ui, sans-serif'
    fontSize: '24px'
    fontWeight: '700'
    lineHeight: '1.15'
    letterSpacing: '-0.015em'
  code:
    fontFamily: 'JetBrains Mono, Fira Code, monospace'
    fontSize: '13px'
    fontWeight: '400'
    lineHeight: '1.6'
rounded:
  xs: '4px'
  sm: '6px'
  md: '8px'
  lg: '12px'
  xl: '16px'
  2xl: '20px'
  pill: '9999px'
spacing:
  1: '4px'
  2: '8px'
  3: '12px'
  4: '16px'
  5: '20px'
  6: '24px'
  8: '32px'
  10: '40px'
  12: '48px'
  16: '64px'
components:
  sidebar:
    background: 'rgba(29, 50, 105, 0.88)'
    backdrop-filter: 'blur(16px)'
    webkit-backdrop-filter: 'blur(16px)'
    border-right: '1px solid rgba(255, 255, 255, 0.12)'
    box-shadow: '4px 0 24px rgba(29, 50, 105, 0.18)'
    width: '240px'
    width-collapsed: '64px'
  sidebar-item-active:
    background: 'rgba(0, 168, 204, 0.20)'
    border-left: '3px solid #00A8CC'
    color: '#FFFFFF'
    border-radius: '{rounded.md}'
  sidebar-item-default:
    color: 'rgba(255, 255, 255, 0.65)'
    border-radius: '{rounded.md}'
  sidebar-item-hover:
    background: 'rgba(255, 255, 255, 0.08)'
    color: '#FFFFFF'
  glass-card:
    background: 'rgba(255, 255, 255, 0.70)'
    backdrop-filter: 'blur(12px)'
    webkit-backdrop-filter: 'blur(12px)'
    border: '1px solid rgba(255, 255, 255, 0.80)'
    box-shadow: '0 4px 24px rgba(29, 50, 105, 0.08)'
    border-radius: '{rounded.xl}'
  metric-card:
    background: '{colors.background}'
    border: '1px solid {colors.border}'
    box-shadow: '0 2px 8px rgba(29, 50, 105, 0.06)'
    border-radius: '{rounded.xl}'
  button-primary:
    background: '{colors.primary}'
    color: '{colors.primary-foreground}'
    border-radius: '{rounded.md}'
    padding: '8px 16px'
    font: '{typography.label}'
    box-shadow: '0 1px 3px rgba(29, 50, 105, 0.20)'
  button-accent:
    background: '{colors.accent}'
    color: '{colors.accent-foreground}'
    border-radius: '{rounded.md}'
    padding: '8px 16px'
    font: '{typography.label}'
    box-shadow: '0 1px 3px rgba(0, 168, 204, 0.25)'
  button-secondary:
    background: '{colors.background}'
    color: '{colors.foreground}'
    border: '1px solid {colors.border}'
    border-radius: '{rounded.md}'
    padding: '8px 16px'
    font: '{typography.label}'
  badge-cots:
    background: '{colors.primary-surface}'
    color: '{colors.primary}'
    border-radius: '{rounded.pill}'
    font: '{typography.label}'
    padding: '2px 8px'
  badge-homegrown:
    background: '{colors.accent-light}'
    color: '{colors.accent-dark}'
    border-radius: '{rounded.pill}'
    font: '{typography.label}'
    padding: '2px 8px'
  badge-success:
    background: '{colors.success-surface}'
    color: '#065F46'
    border-radius: '{rounded.pill}'
    font: '{typography.label}'
    padding: '2px 8px'
  badge-warning:
    background: '{colors.warning-surface}'
    color: '#92400E'
    border-radius: '{rounded.pill}'
    font: '{typography.label}'
    padding: '2px 8px'
  query-input:
    background: '{colors.background}'
    border: '1.5px solid {colors.border}'
    border-radius: '{rounded.xl}'
    padding: '16px 20px'
    box-shadow: '0 2px 12px rgba(29, 50, 105, 0.06)'
    focus-border: '{colors.accent}'
    focus-ring: '0 0 0 3px rgba(0, 168, 204, 0.15)'
    font: '{typography.body}'
  detail-panel:
    background: '{colors.background}'
    border-left: '1px solid {colors.border}'
    box-shadow: '-8px 0 40px rgba(29, 50, 105, 0.12)'
    width: '480px'
  data-table-header:
    background: '{colors.surface}'
    font: '{typography.label}'
    color: '{colors.muted}'
  data-table-row-hover:
    background: 'rgba(0, 168, 204, 0.05)'
  topbar:
    background: '{colors.background}'
    border-bottom: '1px solid {colors.border}'
    height: '56px'
    padding: '0 32px'
---

## Brand & Style

The IT Application Knowledge Graph is an enterprise intelligence platform for Baptist Health South Florida — built and delivered by KSquare Group. The visual identity communicates two things simultaneously: institutional authority (the deep KSquare navy `#1D3269`) and analytical clarity (the teal accent `#00A8CC`). The platform must feel like premium internal tooling, not a generic admin dashboard.

The **Glass Platform** direction is the chosen design language: elevated surfaces, generous whitespace, frosted glass effects at the structural edges (sidebar, detail panels), and clean white workspace where data breathes. The glassmorphism sidebar is the brand anchor — navy translucency framing the white content field at all times. It is never absent, never collapsed by default.

The visual register is **calm, precise, evidence-forward**. The NL query input is the hero element on the Query surface. Charts answer questions; tables confirm them. Every pixel of decoration must earn its place by aiding comprehension or signaling interaction.

Anti-patterns: dark-mode gradients on content areas, more than two brand colors in a single view, decorative imagery, alert-red for anything that is not a genuine error.

## Colors

### Brand palette

- **Primary Navy (`#1D3269`)** — KSquare Group brand color. Used on: sidebar glass base, primary buttons, active nav indicators, section headings where brand authority is needed. Never used as a content area background.
- **Teal (`#00A8CC`)** — accent and interaction color. Used on: active nav border, primary CTAs (Query, Export, Ask), chart highlights, focus rings, badges for capability matches, teal citation chips. One accent only — no competing secondaries.
- **White (`#FFFFFF`)** — main content background. Always. No exceptions.
- **Surface (`#F8FAFC`)** — table headers, secondary card backgrounds, page sub-regions.
- **Primary Surface (`#EEF2FB`)** — tinted background for navy-branded badges and chips.
- **Accent Light (`#E0F7FC`)** — tinted background for teal badges.

### Semantic palette

| Token | Value | Usage |
|---|---|---|
| `foreground` | `#0F172A` | All body text, headings |
| `muted` | `#475569` | Secondary labels, subtitles |
| `muted-foreground` | `#94A3B8` | Placeholder text, disabled labels |
| `border` | `#E2E8F0` | Card borders, dividers, input borders |
| `border-subtle` | `#F1F5F9` | Row separators, inner dividers |
| `success` | `#10B981` | "In Production" status, positive KPIs |
| `warning` | `#F59E0B` | Redundancy cluster count, data quality alerts |
| `destructive` | `#EF4444` | Genuine errors only — ETL failure, API unreachable |

### Glass surfaces

- **Sidebar**: `rgba(29, 50, 105, 0.88)` + `backdrop-filter: blur(16px)` + `border-right: 1px solid rgba(255,255,255,0.12)` + `box-shadow: 4px 0 24px rgba(29,50,105,0.18)`
- **Glass cards** (optional elevation on hover/focus): `rgba(255,255,255,0.70)` + `backdrop-filter: blur(12px)` + `border: 1px solid rgba(255,255,255,0.80)`
- **Detail panel overlay**: white surface, `box-shadow: -8px 0 40px rgba(29,50,105,0.12)`

## Typography

Single typeface: **Inter** (system-ui fallback). No display serif. Enterprise data tools demand legibility at speed over personality. The type system does its work through weight and size contrast, not family switching.

| Role | Size | Weight | Usage |
|---|---|---|---|
| `display` | 36px / –0.02em | 700 | Page hero moments only — empty states, onboarding |
| `heading-lg` | 24px / –0.015em | 600 | Page titles, section headers |
| `heading-md` | 18px / –0.01em | 600 | Card titles, panel headers |
| `heading-sm` | 14px | 600 | Table column headers, label groups |
| `body` | 14px | 400 | All body copy, data cell text |
| `body-sm` | 13px | 400 | Secondary descriptions, footnotes |
| `label` | 12px / +0.01em | 500 | Badges, chips, button text, form labels |
| `metric` | 36px / –0.02em | 700 | KPI numbers on metric cards |
| `metric-sm` | 24px / –0.015em | 700 | Secondary metric numbers |
| `code` | 13px | 400 | Query citations, source labels, technical identifiers |

Line-height defaults: 1.6 for body, 1.15–1.35 for headings. Never go below 1.1 on any text.

## Layout & Spacing

4px base grid. Spacing scale: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.

**Page shell:**
- Sidebar: 240px fixed left, full viewport height, position fixed
- Top bar: 56px, full width minus sidebar, position sticky
- Content area: `margin-left: 240px`, `padding: 32px`, `max-width: 1440px`

**Content grid:**
- Metric card rows: 4-column grid, `gap: 24px`
- Two-column sections: 60/40 split, `gap: 24px`
- Full-width cards: `width: 100%`
- Detail panel: 480px, slides from right edge, full height, overlays content

**Responsive breakpoints:**
- `≥ 1280px` — full layout, sidebar expanded
- `1024–1279px` — sidebar collapses to 64px icon-only
- `768–1023px` — sidebar becomes a slide-in drawer (hamburger trigger in topbar)
- `< 768px` — not required for MVP demo

## Elevation & Depth

Three levels:

| Level | Usage | Shadow |
|---|---|---|
| 0 (flat) | Table rows, list items, inline elements | None |
| 1 (card) | Metric cards, section cards, form inputs | `0 2px 8px rgba(29,50,105,0.06)` |
| 2 (elevated) | Hover state on cards, glass cards | `0 4px 24px rgba(29,50,105,0.08)` |
| 3 (overlay) | Detail panel, modals, tooltips | `0 8px 40px rgba(29,50,105,0.12)` |

Glassmorphism is a structural device, not a decorative one. It appears only on the sidebar and optional glass-card variant. Do not apply `backdrop-filter` to metric cards or data tables — it adds visual noise to content areas.

## Shapes

| Token | Value | Used on |
|---|---|---|
| `rounded.xs` | 4px | Small chips, inline badges |
| `rounded.sm` | 6px | Tooltips, small inputs |
| `rounded.md` | 8px | Buttons, dropdown menus, tab indicators |
| `rounded.lg` | 12px | Standard cards, form panels |
| `rounded.xl` | 16px | Metric cards, query input, main content cards |
| `rounded.2xl` | 20px | Modal dialogs, large glass cards |
| `rounded.pill` | 9999px | Status badges, type badges, quick-query pills |

Prefer `rounded.xl` (16px) as the default card radius — it sets the Glass Platform register. Avoid mixing radius sizes within the same component.

## Components

### Sidebar

The primary navigation and brand element. Always present on `≥ 1024px`.

- Background: `{components.sidebar.background}` (glassmorphism)
- 5 nav items: Dashboard, Query, Analytics, Redundancy Explorer, Applications
- Each item: icon (16px) + label, padding `12px 16px`, `border-radius: {rounded.md}`
- Active: `{components.sidebar-item-active}` — teal left border + teal-tinted background
- Hover: `{components.sidebar-item-hover}`
- Logo area: KSquare Group wordmark in white at top (height 64px)
- User area: avatar + name + role at bottom (above fold)
- Collapse: icon-only mode at 64px wide; tooltip on hover reveals label

### Top Bar

White surface, sticky. Height 56px. Contains: page title (left), action buttons and data-refresh status (right). No global search in top bar — search lives on the Query surface via the NL input.

### Metric Card

`{components.metric-card}`. Internal layout: label (top, `{typography.label}`, `{colors.muted}`), metric number (`{typography.metric}`, `{colors.foreground}`), subtitle (bottom, `{typography.body-sm}`, `{colors.muted-foreground}`). Optional: left accent strip (3px, `{colors.accent}`) for highlighted metrics.

### Query Input

Full-width text input, `{components.query-input}`. Minimum height 56px. Placeholder text in `{colors.muted-foreground}`. Focus state: `border-color: {colors.accent}`, ring `{components.query-input.focus-ring}`. Submit button (teal, `{components.button-accent}`) docked inside the input right edge.

### Quick-Query Pills

Horizontal scrollable row below the query input. Each pill: `border: 1px solid {colors.border}`, `border-radius: {rounded.pill}`, `{typography.label}`, `{colors.muted}`, hover `border-color: {colors.accent}`, `color: {colors.accent}`.

### Data Table

Header: `{components.data-table-header}`. Body rows: `border-bottom: 1px solid {colors.border-subtle}`, hover `{components.data-table-row-hover}`. Clickable rows show cursor pointer. Application Name cell: teal link color `{colors.accent}`, click opens detail panel.

### Cluster Card (Redundancy Explorer)

White card, `{components.metric-card}`. Header row: business process name (`{typography.heading-sm}`), cluster-size badge (`{components.badge-warning}`), expand chevron. Expanded: data table of member applications + action row. Collapsed: header only.

### Detail Panel

`{components.detail-panel}`. Slides from right edge. Dimmed backdrop on content area (40% opacity). Internal sections: header (app name + status badges), body (scrollable, 3 sections: Overview, Ownership, Graph Relationships), footer (sticky, action buttons). Close button top-right.

### Badges / Status Pills

| Badge | Token | Usage |
|---|---|---|
| COTS | `{components.badge-cots}` | Application Type = COTS |
| Homegrown | `{components.badge-homegrown}` | Application Type = Homegrown |
| In Production | `{components.badge-success}` | Install Status |
| Redundancy count | `{components.badge-warning}` | Cluster size on cluster cards |
| Source citation | teal bg / white text | Agent response citations |

### Citation Chip

Agent response source label. Background `{colors.accent}`, color `{colors.accent-foreground}`, `{rounded.pill}`, `{typography.code}`, padding `3px 10px`. Appears above every Agent result table.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Use `#1D3269` for the sidebar glass base, primary buttons, and brand headings | Use navy as a content area background |
| Use `#00A8CC` for active states, CTAs, chart highlights, focus rings, citation chips | Use teal for destructive actions or error states |
| Use `{rounded.xl}` (16px) as the default card corner radius | Mix card radii within the same view |
| Use the glassmorphism sidebar at full 240px width by default | Auto-collapse the sidebar on desktop |
| Show source citations on every Agent response | Render Agent responses without a data source attribution |
| Use `{colors.destructive}` only for genuine system errors | Use red for data quality warnings or business logic alerts |
| Apply glass-card only on structural overlays (sidebar, detail panel) | Apply `backdrop-filter` to metric cards or table rows |
| Keep the main content background `#FFFFFF` at all times | Introduce gray or tinted page backgrounds |
| Show "Not specified" for NULL field values | Show blank, "null", "undefined", or "N/A" |
