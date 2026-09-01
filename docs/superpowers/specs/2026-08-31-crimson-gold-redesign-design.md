# Crimson & Gold Redesign

## Context

The site currently uses a light, pastel "fun" theme (multi-accent colors, white cards, `#f8f9fc` background) built on a shared `css/styles.css` design-token system, a fixed left sidebar (`js/nav.js`), sortable data tables (`js/tables.js`), and Chart.js visualizations (`js/charts.js`). The owner wants to move the visual feel closer to major sports broadcast/standings sites (ESPN, Premier League table, Formula1.com) while keeping the current information architecture (sidebar nav, page structure) intact.

Three visual directions were mocked up and compared in-browser (Broadcast Bold / ESPN-style, Clean Data Table / Premier League-style, Motorsport Tech / F1-style). **Clean Data Table** was selected as the structural direction. Three palette options were then mocked on top of it (Crimson & Gold, Electric Navy, Refined Current/Light). **Crimson & Gold** was selected.

## Scope

Holistic redesign: every page (`index.html`, member pages, year pages, `hall-of-fame.html`, `all-time.html`, `wagers.html` including its live OAuth/Kalshi form controls) moves to the new theme in one pass, since the design is token-driven and centralizes in `css/styles.css` and `js/charts.js`.

Explicitly **out of scope** for this redesign (asked and declined):
- Light/dark theme toggle — dark-only.
- Colored per-member indicator dots in table rows.
- Sticky table headers on scroll.
- Introducing a new font family — Inter stays, leaning on weight/spacing for the bolder feel.
- Rank movement arrows on any page other than the Current Season page (see below).

## Visual system

### Palette (replaces the `:root` tokens in `css/styles.css`)

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#16131a` | Page background |
| `--bg-secondary` / `--bg-card` | `#1c171f` | Cards, sidebar, table containers |
| `--bg-tertiary` / `--bg-hover` | `#221d27` | Nested panels, hover states |
| `--text-primary` | `#f2ede4` | Primary text (warm off-white) |
| `--text-secondary` | `#b8ac95` | Labels, secondary text |
| `--text-muted` | `#6a6070` | Muted/placeholder text |
| `--accent-primary` (crimson) | `#7a1f2b` | Header bands, active nav state, dividers, brand chrome |
| `--accent-gold` | `#f0c34d` | Stat tile values, rank-1 highlight, links |
| `--border-color` | `#332b3a` | Table/card borders |
| `--positive` | `#3ecf6e` | Positive $ deltas, top-tier rank bar |
| `--negative` | `#ff5c72` | Negative $ deltas, bottom-tier rank bar |
| rank-bar mid tier | `#4a3f52` | Neutral/middle rank bar segment |

Positive/negative and the rank-bar tiers intentionally use a different hue family than the crimson/gold brand accents, so a `+$45` or `-$25` value never gets visually confused with brand chrome.

The existing multi-accent tokens (`--accent-secondary`, `--accent-blue`, `--accent-purple`, `--accent-pink`, `--accent-orange`, `--accent-teal`) are removed from `:root` — nothing outside `chartColors.members` in `js/charts.js` needs a distinct per-member hue, and that palette is being kept as-is (see Charts below).

### Typography

No new font family. Keep `--font-family: 'Inter', ...`. Increase weight to 800 and add `font-variant-numeric: tabular-nums` for rank digits and stat-tile values to get a bolder, broadcast-numeral feel. Table header labels stay small-caps/uppercase (already the existing pattern), recolored to `--text-secondary`.

## Components

### Sidebar (`css/styles.css` sidebar rules, structure unchanged)

- Background `--bg-secondary`, border `--border-color` — no structural change to `js/nav.js`.
- `.nav-link.active` / `.nav-year-link.active` / `.nav-member-link.active`: crimson-tinted background (`rgba(122,31,43,0.35)`), gold text, gold (`--accent-gold`) left border — replacing the current blue-tinted active state.
- `.nav-section-title`: muted crimson-tan uppercase (`--text-secondary` on `--bg-secondary`), replacing the current teal.

### Tables (`js/tables.js` render logic + `css/styles.css` table rules)

- New 4px colored left-edge bar per data row: green (`--positive`) for top-tier ranks, gray (mid tier) for middle ranks, red (`--negative`) for bottom-tier ranks — mapped to the existing "top 7 earn money / bottom 7 pay" split from the sidebet rules in `CLAUDE.md`, generalized proportionally for tables that aren't exactly 14 rows (e.g., a top-half/bottom-half split).
- Header row: 2px bottom border in `--accent-primary` (crimson), header text in `--text-secondary` uppercase (existing small-caps styling, recolored).
- All numeric columns (`type: 'number'`, `'delta'`, rank columns): right-aligned, `tabular-nums`.
- Row hover/zebra: alternate rows use `--bg-tertiary` at low opacity; hover state `--bg-hover`.

### Stat tiles (homepage cards: Season Leader / Sidebet Leader / Week / Average Points)

- Card background `--bg-secondary`, border `--border-color`.
- Label: small, uppercase, `--text-secondary`.
- Value: bold (800), `--accent-gold`.

### Charts (`js/charts.js`)

- Keep `chartColors.members` (the 14 distinct per-member hues) unchanged — verified legible against the new dark background.
- Update `defaultOptions` chrome only: legend/axis label color → `--text-secondary`; gridlines → low-opacity white (`rgba(255,255,255,0.06)`); tooltip background → `--bg-secondary`, tooltip border → `--accent-primary`, tooltip title/body color → `--text-primary` / `--text-secondary`.

## Rank movement arrows (▲ / ▼ / —)

**Scope**: Current Season page (`index.html`) only — both the Points Standings and Sidebet Standings tables. Not shown on year pages, member pages, hall-of-fame, or all-time stats, since those represent completed/aggregate state with no "current week" to compare against.

**Computation**: Pure client-side, derived from data already loaded in `LEAGUE_DATA.seasons[year]` — no backend or `data.js` schema changes.

For a given member and current week N (the latest week with data, per the existing `weeksCompleted` calculation in `index.html`):
1. Compute cumulative total points (or cumulative sidebet total, depending on which table) through week N for every member, and rank them.
2. Compute the same cumulative totals/ranks through week N−1.
3. Compare: rank improved → `▲` in `--positive`; rank worsened → `▼` in `--negative`; unchanged → `—` in `--text-muted`.
4. If N = 1 (no prior week to compare, or `weeksCompleted === 0`), render nothing (blank) rather than a `—`, since there's no movement to report yet.

This lives as a small pure helper (e.g. `computeRankMovement(weeklyValues, memberNames, currentWeek)` in `js/tables.js` or a shared util), unit-testable the same way `tests/sidebets.test.js` already tests the payout formula.

## Rollout & testing

1. Replace `:root` tokens in `css/styles.css` and sweep the file for any hardcoded color values that bypass the token system (the removed multi-accent tokens in particular).
2. Update `js/charts.js` `defaultOptions` chrome.
3. Add the rank-bar tier logic and tabular-nums styling to the table render path in `js/tables.js` / `css/styles.css`.
4. Add the rank-movement helper and wire it into `index.html`'s Points/Sidebet Standings table rendering.
5. Visual QA in-browser across one representative page per section: `index.html`, a member page, a year page, `hall-of-fame.html`, `all-time.html`, `wagers.html` (including its OAuth/Kalshi form controls) — confirm legibility/contrast and that no page still shows the old light theme or an orphaned accent color.
6. Run `npx jest` — confirm the existing 72 tests still pass and any new rank-movement unit tests pass.
7. Per standing instruction for this repo: commit and push directly to `main` — **except** the user asked explicitly not to push this redesign until they've reviewed it locally first, so the implementation stays uncommitted/unpushed until that review happens.
