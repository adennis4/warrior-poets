# Crimson & Gold Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the site's visual theme from its current light, multi-accent-color "fun" theme to a dark "Crimson & Gold" theme with a denser, Premier-League-table-inspired look, plus rank-movement arrows on the current-season standings tables.

**Architecture:** Token-driven CSS redesign. Almost everything centralizes in `css/styles.css`'s `:root` custom properties and `js/charts.js`'s Chart.js default options, which every page already shares. Two islands of duplicated inline styling (18 `members/*.html` pages and `wagers.html`) need their own mechanical color updates because they don't source from those shared files. A new small pure-function layer (mirroring the existing `js/nav.js` → `tests/utils.js` pattern) computes rank-tier coloring and week-over-week rank movement from data already loaded client-side — no backend or `data.js` schema changes.

**Tech Stack:** Vanilla HTML/CSS/JS, Chart.js (CDN), Jest + jsdom for unit tests.

**Spec:** `docs/superpowers/specs/2026-08-31-crimson-gold-redesign-design.md`

**Note on the spec's rank-bar tiers:** The spec describes a 3-tier (green/gray/red) rank bar "mapping to your top 7 earn / bottom 7 pay split." On inspection, that split is a strict binary in `CLAUDE.md` (ranks 1–7 pay out positive, 8–14 negative — there's no neutral middle group), so a fake middle tier would misrepresent the data. This plan implements a 2-tier bar instead: top half of the table green, bottom half red, split at the midpoint. Flagged here for visibility since it's a small deviation from the spec's literal wording, not from the confirmed color/palette decisions.

**Do not push.** Per the user's explicit request, all commits in this plan stay local (`git commit`, never `git push`) until they've reviewed the result in a browser.

**Post-Task-1 correction:** Task 1's code review caught two gaps in the original file audit this plan was based on, both since fixed (commits 13acc2c, fabe3e3 on `redesign/crimson-gold`):
- `hall-of-fame.html` has its own inline `<style>` block that referenced the removed `--accent-blue`/`--accent-teal` tokens — a real regression (vanished timeline connector, wrong label color). This file was missing from every task's file list; it's now fixed as part of Task 1 and needs no further action.
- `wagers.html` has 8 more `var(--accent-blue)` references beyond the hardcoded-hex sites originally caught in Task 3 below. Task 3's steps have been expanded to include them.

---

## File Structure

| File | Responsibility |
|---|---|
| `css/styles.css` | Modify: swap `:root` design tokens to Crimson & Gold, fix every rule that referenced a removed/repurposed token, add rank-tier-bar and rank-arrow styles, add stat-value color. |
| `js/charts.js` | Modify: recolor `defaultOptions` chart chrome (legend/tooltip/grid/ticks) for the dark theme. Per-member line colors (`chartColors.members`) stay unchanged. |
| `js/nav.js` | Modify: add `getRankTier`, `formatRankMovement`, `computeRankMovement` to the `window.WP` namespace. |
| `tests/utils.js` | Modify: mirror the same three new functions (CommonJS), following the file's existing "CommonJS version of nav.js functions" pattern. |
| `tests/utils.test.js` | Modify: add Jest tests for the three new functions (written first, TDD). |
| `js/tables.js` | Modify: table renderer gains `config.showRankTier` (row-level rank-tier class) and `col.movementKey` (inline rank-movement arrow) support. |
| `index.html` | Modify: wire `WP.computeRankMovement` into the Points/Sidebet Standings tables and pass `showRankTier`/`movementKey` into `createTable`. |
| `members/*.html` (18 files) | Modify: mechanical color swap of their duplicated inline Chart.js config (a leftover from before `js/charts.js` existed as a shared module). |
| `wagers.html` | Modify: same inline chart-chrome swap, plus its own hover/toast/error button colors. NFL team-brand gradients and the Yahoo-brand login button are explicitly left untouched (real third-party brand colors, not site theme). |

---

## Task 1: Design tokens and global CSS

**Files:**
- Modify: `css/styles.css:1-41` (`:root` block)
- Modify: `css/styles.css` (every usage site listed below)

- [ ] **Step 1: Replace the `:root` token block**

Replace `css/styles.css:1-41` (from `/* Warrior Poets Fantasy Football - Light & Fun Theme */` through the closing `}` of `:root`) with:

```css
/* Warrior Poets Fantasy Football - Crimson & Gold Theme */

:root {
  /* Colors - Crimson & Gold (dark) */
  --bg-primary: #16131a;
  --bg-secondary: #1c171f;
  --bg-tertiary: #221d27;
  --bg-card: #1c171f;
  --bg-hover: #2a2530;

  --text-primary: #f2ede4;
  --text-secondary: #b8ac95;
  --text-muted: #6a6070;

  /* accent-primary: large fills/backgrounds/borders (crimson).
     accent-primary-bright: anywhere crimson is foreground TEXT or a thin/
     small decorative element - the base crimson is too close to the near-
     black background to read as text. */
  --accent-primary: #7a1f2b;
  --accent-primary-bright: #dc3d52;
  --accent-gold: #f0c34d;

  --border-color: #332b3a;
  --border-light: #4a4152;

  /* Positive/Negative - kept a distinct hue family from the brand accents
     so a +$45 / -$25 delta is never visually confused with brand chrome */
  --positive: #3ecf6e;
  --negative: #ff5c72;

  /* Inactive member styling */
  --inactive-text: #8a7f72;

  /* Spacing */
  --sidebar-width: 240px;
  --header-height: 60px;

  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', monospace;
}
```

- [ ] **Step 2: Fix every remaining reference to a removed/repurposed token**

Each of these is an exact find-and-replace within `css/styles.css`. Apply them all (the removed tokens — `--accent-secondary`, `--accent-blue`, `--accent-purple`, `--accent-pink`, `--accent-orange`, `--accent-teal` — no longer exist after Step 1, so every rule below currently pointing at one of them would otherwise resolve to nothing):

| Selector (for context) | Old | New |
|---|---|---|
| `a` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `a:hover` | `color: var(--accent-primary);` | `color: var(--accent-primary-bright);` |
| `.sidebar-logo span` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `.nav-section-title` | `color: var(--accent-teal);` | `color: var(--text-secondary);` |
| `.nav-section-toggle:hover` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `.nav-year-link.active` | `background-color: rgba(52, 89, 237, 0.15);` | `background-color: rgba(122, 31, 43, 0.35);` |
| `.nav-year-link.active` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `.nav-member-link.active` | `background-color: rgba(52, 89, 237, 0.15);` | `background-color: rgba(122, 31, 43, 0.35);` |
| `.nav-member-link.active` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `.nav-link.active` | `background-color: rgba(52, 89, 237, 0.1);` | `background-color: rgba(122, 31, 43, 0.3);` |
| `.nav-link.active` | `color: var(--accent-blue);\n  border-left-color: var(--accent-blue);` | `color: var(--accent-gold);\n  border-left-color: var(--accent-gold);` |
| `.page-title` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `thead` | `background: linear-gradient(135deg, rgba(52, 89, 237, 0.08) 0%, rgba(32, 201, 151, 0.08) 100%);` | `background: linear-gradient(135deg, rgba(122, 31, 43, 0.18) 0%, rgba(122, 31, 43, 0.05) 100%);` |
| `th` | `color: var(--accent-blue);` | `color: var(--text-secondary);` |
| `th.sort-asc::after` | `border-bottom: 4px solid var(--accent-primary);` | `border-bottom: 4px solid var(--accent-gold);` |
| `th.sort-desc::after` | `border-top: 4px solid var(--accent-primary);` | `border-top: 4px solid var(--accent-gold);` |
| `.card-title::before` | `background: var(--accent-teal);` | `background: var(--accent-primary-bright);` |
| `.stat-label` | `color: var(--accent-purple);` | `color: var(--text-secondary);` |
| `.year-btn:hover` | `border-color: var(--accent-primary);` | `border-color: var(--accent-primary-bright);` |
| `.member-card:hover` | `border-color: var(--accent-primary);` | `border-color: var(--accent-primary-bright);` |
| `.member-avatar` | `color: var(--accent-primary);` | `color: var(--accent-primary-bright);` |
| `.hof-champion` | `background: linear-gradient(135deg, rgba(249, 168, 37, 0.08) 0%, rgba(255, 107, 107, 0.05) 100%);` | `background: linear-gradient(135deg, rgba(240, 195, 77, 0.08) 0%, rgba(220, 61, 82, 0.05) 100%);` |

`.year-btn.active` (`background-color: var(--accent-primary); border-color: var(--accent-primary); color: var(--text-primary);`) and `.hof-name` / `.trophy` / `.badge-gold` (`color: var(--accent-gold);`) need **no code change** — they already reference tokens that still exist, they just pick up the new values automatically from Step 1.

- [ ] **Step 3: Style the stat tiles**

Find `.stat-value` in `css/styles.css` (currently):

```css
.stat-value {
  font-size: 2rem;
  font-weight: 700;
  font-family: var(--font-mono);
}
```

Replace with:

```css
.stat-value {
  font-size: 2rem;
  font-weight: 800;
  font-family: var(--font-mono);
  color: var(--accent-gold);
  font-variant-numeric: tabular-nums;
}
```

- [ ] **Step 4: Add zebra striping**

The spec calls for alternating-row zebra striping, which doesn't exist yet. Find in `css/styles.css`:

```css
tr:hover {
  background-color: var(--bg-hover);
}
```

Replace with (the zebra rule must come *before* `tr:hover` in source order so hover — equal specificity — wins on even rows too):

```css
tr:nth-child(even) {
  background-color: var(--bg-tertiary);
}

tr:hover {
  background-color: var(--bg-hover);
}
```

- [ ] **Step 5: Verify no orphaned token references remain**

Run:

```bash
grep -nE "accent-secondary|accent-blue|accent-purple|accent-pink|accent-orange|accent-teal" css/styles.css
```

Expected: no output (empty). If anything prints, it's a usage site Step 2 missed — fix it the same way (map to `--accent-gold` for text/links, `--accent-primary`/`--accent-primary-bright` for crimson chrome, `--text-secondary` for muted labels).

- [ ] **Step 6: Visual check**

```bash
python3 -m http.server 8930 &
```

Open `http://localhost:8930/index.html` in the browser tool, screenshot it, and confirm: dark background, crimson/gold sidebar active states, gold page title and links, visible zebra striping, no leftover light-theme colors or visibly broken (invisible/transparent) elements. Then:

```bash
kill %1
```

- [ ] **Step 7: Commit**

```bash
git add css/styles.css
git commit -m "Redesign: swap to Crimson & Gold dark theme tokens"
```

---

## Task 2: Chart.js default chrome

**Files:**
- Modify: `js/charts.js:39-90` (`defaultOptions`)

- [ ] **Step 1: Recolor the shared chart chrome**

In `js/charts.js`, replace:

```js
// Default chart options for light theme
const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    tooltip: {
      backgroundColor: '#ffffff',
      titleColor: '#1a1a2e',
      bodyColor: '#5a5a7a',
      borderColor: '#e0e4ed',
      borderWidth: 1,
      cornerRadius: 8,
      titleFont: {
        family: "'Inter', sans-serif",
        weight: 600
      },
      bodyFont: {
        family: "'Inter', sans-serif"
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: '#e0e4ed',
        drawBorder: false
      },
      ticks: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    y: {
      grid: {
        color: '#e0e4ed',
        drawBorder: false
      },
      ticks: {
        color: '#5a5a7a',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    }
  }
};
```

with:

```js
// Default chart options for dark theme
const defaultOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#b8ac95',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    tooltip: {
      backgroundColor: '#1c171f',
      titleColor: '#f2ede4',
      bodyColor: '#b8ac95',
      borderColor: '#332b3a',
      borderWidth: 1,
      cornerRadius: 8,
      titleFont: {
        family: "'Inter', sans-serif",
        weight: 600
      },
      bodyFont: {
        family: "'Inter', sans-serif"
      }
    }
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(255, 255, 255, 0.06)',
        drawBorder: false
      },
      ticks: {
        color: '#b8ac95',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    },
    y: {
      grid: {
        color: 'rgba(255, 255, 255, 0.06)',
        drawBorder: false
      },
      ticks: {
        color: '#b8ac95',
        font: {
          family: "'Inter', sans-serif"
        }
      }
    }
  }
};
```

`chartColors.members` (the 14 per-member line colors) and `chartColors.primary`/`.gold`/etc. (the generic fallback/highlight colors) are unchanged — out of scope per the spec.

- [ ] **Step 2: Visual check**

With the same local server running, open a page with a chart (e.g. `http://localhost:8930/members/andrew.html`, or `all-time.html`), screenshot it, confirm the chart legend/gridlines/tooltip now read clearly against the dark background and member lines are still distinguishable.

- [ ] **Step 3: Commit**

```bash
git add js/charts.js
git commit -m "Redesign: recolor shared Chart.js chrome for dark theme"
```

---

## Task 3: Member pages and wagers.html inline colors

These pages predate `js/charts.js` existing as the single source of chart chrome and still carry their own duplicated inline Chart.js config. All 18 `members/*.html` files have byte-identical color values at this point (verified), so one scripted pass handles all of them.

**Files:**
- Modify: `members/andrew.html`, `members/ben.html`, `members/cp.html`, `members/dues.html`, `members/farber.html`, `members/heath.html`, `members/jb.html`, `members/jerome.html`, `members/jett.html`, `members/lloyd.html`, `members/marty.html`, `members/pinkston.html`, `members/rich.html`, `members/rick.html`, `members/rizzo.html`, `members/stern.html`, `members/woock.html`, `members/yonk.html`
- Modify: `wagers.html`

- [ ] **Step 1: Recolor the member-page inline charts**

Run from the repo root:

```bash
for f in members/*.html; do
  sed -i '' "s/'#868e96'/'#9a8f7a'/g" "$f"
  sed -i '' "s/'#5a5a7a'/'#b8ac95'/g" "$f"
  sed -i '' "s/backgroundColor: '#ffffff'/backgroundColor: '#1c171f'/g" "$f"
  sed -i '' "s/titleColor: '#1a1a2e'/titleColor: '#f2ede4'/g" "$f"
  sed -i '' "s/borderColor: '#e0e4ed'/borderColor: '#332b3a'/g" "$f"
  sed -i '' "s/grid: { color: '#e0e4ed' }/grid: { color: 'rgba(255,255,255,0.06)' }/g" "$f"
  sed -i '' "s/'#666666'/'#b8ac95'/g" "$f"
done
```

(`#868e96` is the "Standing" line's border color — mapped to a warm-tinted grey (`#9a8f7a`) so it still reads clearly on the dark background instead of the old cool grey.)

- [ ] **Step 2: Verify no old-theme hex values remain in member pages**

```bash
grep -rlE "#868e96|#5a5a7a|#ffffff|#1a1a2e|#e0e4ed|#666666" members/*.html
```

Expected: no output.

- [ ] **Step 3: Recolor wagers.html's own UI chrome**

Run:

```bash
sed -i '' "s/background: #2a47c9;/background: #dc3d52;/g" wagers.html
sed -i '' "s/color: #e74c3c;/color: #ff5c72;/g" wagers.html
sed -i '' "s/background: #e74c3c;/background: #ff5c72;/g" wagers.html
sed -i '' "s/background: #2ecc71;/background: #3ecf6e;/g" wagers.html
```

This recolors: the `.kalshi-link:hover`, `.btn-submit:hover`, and `.step-btn:hover` background (old accent-blue hover → bright crimson), `.order-error` text and `.toast.error` background (old red → new `--negative` red), and `.toast` success background (old green → new `--positive` green).

**Explicitly not touched** (real third-party brand colors, not site theme — leave as-is):
- `.team-sea` / `.team-ne` gradients (`#002244`/`#69BE28`/`#C60C30`) — actual Seahawks/Patriots team colors.
- `.yahoo-login` / `.yahoo-login:hover` (`#6001d2` / `#4a01a3`) — Yahoo's own brand purple for the "Sign in with Yahoo" button.
- `.odds-btn.no` (`#7c4dab`) — Kalshi's Yes/No market color convention, not a site theme color.

- [ ] **Step 4: Fix wagers.html's remaining `var(--accent-blue)` references**

`wagers.html` has its own inline `<style>` block (like `hall-of-fame.html` did — see the note near the top of this plan) with 8 more references to the now-removed `--accent-blue` token, beyond the hardcoded-hex sites fixed in Step 3. Apply this table exactly (find-and-replace within `wagers.html`):

| Selector (for context) | Old | New |
|---|---|---|
| `.kalshi-link` | `background: var(--accent-blue);` | `background: var(--accent-primary);` |
| `.odds-btn.yes .odds-label` | `color: var(--accent-blue);` | `color: var(--positive);` |
| `.odds-btn.yes .odds-price` | `color: var(--accent-blue);` | `color: var(--positive);` |
| `.order-side.yes` | `color: var(--accent-blue);` | `color: var(--positive);` |
| `.order-adjust:hover` | `border-color: var(--accent-blue);` | `border-color: var(--accent-primary-bright);` |
| `.btn-submit` (base rule, not `:hover`) | `background: var(--accent-blue);` | `background: var(--accent-primary);` |
| `.step-number` | `color: var(--accent-blue);` | `color: var(--accent-gold);` |
| `.step-btn` (base rule, not `:hover`) | `background: var(--accent-blue);` | `background: var(--accent-primary);` |

The `.odds-btn.yes` / `.order-side.yes` mapping to `--positive` (green) is a deliberate choice, not just "whatever was closest": it gives the Kalshi "Yes" side a clear green semantic (paired against `.odds-btn.no`'s existing untouched purple, and `.order-side.no`'s neutral `--text-secondary`), consistent with how the rest of the site already uses green/red for positive/negative.

- [ ] **Step 5: Verify wagers.html's remaining hex/var colors are only the intentionally-excluded ones**

```bash
grep -nE "#[0-9a-fA-F]{6}\b" wagers.html
grep -nE "var\(--accent-blue|var\(--accent-teal|var\(--accent-purple|var\(--accent-pink|var\(--accent-orange|var\(--accent-secondary" wagers.html
```

Expected output for the first command: only the team gradients, `.odds-btn.no`, and `.yahoo-login`/`:hover` lines listed above. Expected output for the second: empty. If anything else shows up, it was missed in Step 3 or Step 4 — map it using the same old→new pairs from Task 1/2/this task.

- [ ] **Step 6: Visual check**

With the local server still running (or restart it), open `http://localhost:8930/members/cp.html` and `http://localhost:8930/wagers.html`, screenshot both, confirm charts and buttons read correctly against the dark theme and the team-color/Yahoo-brand elements are untouched.

- [ ] **Step 7: Commit**

```bash
git add members/*.html wagers.html
git commit -m "Redesign: recolor inline chart/UI chrome in member pages and wagers.html"
```

---

## Task 4: Rank-tier and rank-movement pure functions (TDD)

**Files:**
- Modify: `tests/utils.test.js`
- Modify: `tests/utils.js`
- Modify: `js/nav.js`

- [ ] **Step 1: Write the failing tests**

Add to the end of `tests/utils.test.js` (before the final newline), and add the three new names to the `require` list at the top of the file (`getRankTier`, `formatRankMovement`, `computeRankMovement`):

```js
describe('getRankTier', () => {
  test('returns "top" for ranks in the top half', () => {
    expect(getRankTier(1, 14)).toBe('top');
    expect(getRankTier(7, 14)).toBe('top');
  });

  test('returns "bottom" for ranks in the bottom half', () => {
    expect(getRankTier(8, 14)).toBe('bottom');
    expect(getRankTier(14, 14)).toBe('bottom');
  });

  test('handles odd totals by rounding the top half up', () => {
    expect(getRankTier(1, 5)).toBe('top');
    expect(getRankTier(3, 5)).toBe('top');
    expect(getRankTier(4, 5)).toBe('bottom');
  });

  test('returns null for missing rank or total', () => {
    expect(getRankTier(null, 14)).toBe(null);
    expect(getRankTier(1, 0)).toBe(null);
    expect(getRankTier(undefined, 14)).toBe(null);
  });
});

describe('formatRankMovement', () => {
  test('renders an up arrow for "up"', () => {
    expect(formatRankMovement('up')).toBe(' <span class="rank-arrow rank-arrow-up">▲</span>');
  });

  test('renders a down arrow for "down"', () => {
    expect(formatRankMovement('down')).toBe(' <span class="rank-arrow rank-arrow-down">▼</span>');
  });

  test('renders a flat dash for "same"', () => {
    expect(formatRankMovement('same')).toBe(' <span class="rank-arrow rank-arrow-same">—</span>');
  });

  test('renders nothing for null/undefined', () => {
    expect(formatRankMovement(null)).toBe('');
    expect(formatRankMovement(undefined)).toBe('');
  });
});

describe('computeRankMovement', () => {
  test('returns null movement for every member on week 1', () => {
    const weeklyPoints = {
      A: { '1': 100 },
      B: { '1': 90 }
    };
    expect(computeRankMovement(weeklyPoints, 1)).toEqual({ A: null, B: null });
  });

  test('returns null movement when there is no completed week yet', () => {
    const weeklyPoints = { A: {}, B: {} };
    expect(computeRankMovement(weeklyPoints, 0)).toEqual({ A: null, B: null });
  });

  test('detects a member moving up in rank', () => {
    // Week 1: A=100 (rank 1), B=90 (rank 2). Week 2: A=100+10=110 (rank 2), B=90+50=140 (rank 1).
    const weeklyPoints = {
      A: { '1': 100, '2': 10 },
      B: { '1': 90, '2': 50 }
    };
    const movement = computeRankMovement(weeklyPoints, 2);
    expect(movement.B).toBe('up');
    expect(movement.A).toBe('down');
  });

  test('detects an unchanged rank as "same"', () => {
    const weeklyPoints = {
      A: { '1': 100, '2': 20 },
      B: { '1': 90, '2': 10 }
    };
    const movement = computeRankMovement(weeklyPoints, 2);
    expect(movement.A).toBe('same');
    expect(movement.B).toBe('same');
  });
});
```

- [ ] **Step 2: Run the tests and verify they fail**

```bash
npx jest tests/utils.test.js
```

Expected: FAIL — `getRankTier`, `formatRankMovement`, and `computeRankMovement` are not defined (they don't exist in `tests/utils.js` yet).

- [ ] **Step 3: Implement the functions in `tests/utils.js`**

Add before the `module.exports = { ... }` block at the end of `tests/utils.js`:

```js
/**
 * Return which half of a ranked table a rank falls in ('top' or 'bottom'),
 * or null if the rank/total isn't valid. The top half is rounded up on odd
 * totals (e.g. rank 3 of 5 is "top").
 */
function getRankTier(rank, totalRows) {
  if (!rank || !totalRows) return null;
  return rank <= Math.ceil(totalRows / 2) ? 'top' : 'bottom';
}

/**
 * Render an inline rank-movement indicator for a 'up' | 'down' | 'same' | null
 * movement value. Returns an empty string when there's nothing to show.
 */
function formatRankMovement(movement) {
  if (movement === 'up') return ' <span class="rank-arrow rank-arrow-up">▲</span>';
  if (movement === 'down') return ' <span class="rank-arrow rank-arrow-down">▼</span>';
  if (movement === 'same') return ' <span class="rank-arrow rank-arrow-same">—</span>';
  return '';
}

/**
 * Rank every member by their cumulative total through a given week.
 * Returns { memberName: rank } where rank 1 is the highest cumulative total.
 */
function calculateCumulativeRanks(weeklyValues, throughWeek) {
  const totals = Object.keys(weeklyValues).map(name => {
    let sum = 0;
    for (let w = 1; w <= throughWeek; w++) {
      sum += weeklyValues[name][String(w)] || 0;
    }
    return { name, total: sum };
  });
  totals.sort((a, b) => b.total - a.total);
  const ranks = {};
  totals.forEach((entry, index) => {
    ranks[entry.name] = index + 1;
  });
  return ranks;
}

/**
 * Compute each member's rank movement ('up' | 'down' | 'same') between the
 * previous week and currentWeek, based on cumulative totals. Returns null
 * for every member when currentWeek is 1 or less (no prior week to compare).
 */
function computeRankMovement(weeklyValues, currentWeek) {
  const names = Object.keys(weeklyValues);
  if (!currentWeek || currentWeek < 2) {
    const none = {};
    names.forEach(name => { none[name] = null; });
    return none;
  }

  const currentRanks = calculateCumulativeRanks(weeklyValues, currentWeek);
  const previousRanks = calculateCumulativeRanks(weeklyValues, currentWeek - 1);

  const movement = {};
  names.forEach(name => {
    const cur = currentRanks[name];
    const prev = previousRanks[name];
    if (cur < prev) movement[name] = 'up';
    else if (cur > prev) movement[name] = 'down';
    else movement[name] = 'same';
  });
  return movement;
}
```

Then update the `module.exports` block at the end of `tests/utils.js` to also export the new functions:

```js
module.exports = {
  formatNumber,
  formatDelta,
  getValueClass,
  isInactive,
  formatRank,
  calculateSidebetPayout,
  calculateWeeklySidebets,
  calculateTotalPoints,
  calculateTotalSidebets,
  calculateLowManCount,
  getRankTier,
  formatRankMovement,
  calculateCumulativeRanks,
  computeRankMovement
};
```

- [ ] **Step 4: Run the tests and verify they pass**

```bash
npx jest tests/utils.test.js
```

Expected: PASS, all tests green.

- [ ] **Step 5: Mirror the same functions into `js/nav.js`**

In `js/nav.js`, add the same four functions (`getRankTier`, `formatRankMovement`, `calculateCumulativeRanks`, `computeRankMovement` — identical bodies to Step 3) above the `window.WP = { ... }` block, then add them to that export:

```js
window.WP = {
  initPage,
  formatNumber,
  formatDelta,
  formatRank,
  getValueClass,
  isInactive,
  getTrophySvg,
  icons,
  getRankTier,
  formatRankMovement,
  calculateCumulativeRanks,
  computeRankMovement
};
```

- [ ] **Step 6: Run the full test suite**

```bash
npx jest
```

Expected: all suites pass (the existing 72 tests plus the new ones from Step 1).

- [ ] **Step 7: Commit**

```bash
git add tests/utils.js tests/utils.test.js js/nav.js
git commit -m "Redesign: add rank-tier and rank-movement pure functions"
```

---

## Task 5: Wire rank-tier bars and movement arrows into the table renderer

**Files:**
- Modify: `js/tables.js:151-216` (`createTable`)
- Modify: `css/styles.css` (new rules)

- [ ] **Step 1: Add rank-tier and movement support to the table renderer**

In `js/tables.js`, replace the `createTable` function's row-rendering section. Current code (inside `createTable`, after the `columns` header-row block):

```js
        <tbody>
          ${data.map((row, index) => `
            <tr ${onRowClick ? `onclick="${onRowClick}('${row.id || row.name || index}')"` : ''}>
              ${columns.map(col => {
                let value = row[col.key];
                let displayValue = value;
                let classes = [];
                let dataValue = '';

                // Format based on column type
                if (col.type === 'dynamicRank') {
                  classes.push('rank');
                  classes.push('numeric');
                  classes.push('dynamic-rank');
                  displayValue = index + 1;
                  dataValue = index + 1;
                  if (index === 0) classes.push('rank-1');
                  if (index === 1) classes.push('rank-2');
                  if (index === 2) classes.push('rank-3');
                } else if (col.type === 'rank') {
                  classes.push('rank');
                  classes.push('numeric');
                  if (value === null || value === undefined || value === 0) {
                    displayValue = '—';
                    dataValue = 999;
                  } else {
                    if (value === 1) classes.push('rank-1');
                    if (value === 2) classes.push('rank-2');
                    if (value === 3) classes.push('rank-3');
                    dataValue = value;
                  }
                } else if (col.type === 'number') {
```

Replace with:

```js
        <tbody>
          ${data.map((row, index) => {
            const resolvedRank = config.showRankTier === true
              ? index + 1
              : (typeof config.showRankTier === 'string' ? row[config.showRankTier] : null);
            const rankTier = config.showRankTier ? WP.getRankTier(resolvedRank, data.length) : null;
            const rowClass = rankTier ? ` class="rank-tier-${rankTier}"` : '';

            return `
            <tr${rowClass} ${onRowClick ? `onclick="${onRowClick}('${row.id || row.name || index}')"` : ''}>
              ${columns.map(col => {
                let value = row[col.key];
                let displayValue = value;
                let classes = [];
                let dataValue = '';

                // Format based on column type
                if (col.type === 'dynamicRank') {
                  classes.push('rank');
                  classes.push('numeric');
                  classes.push('dynamic-rank');
                  displayValue = index + 1;
                  dataValue = index + 1;
                  if (index === 0) classes.push('rank-1');
                  if (index === 1) classes.push('rank-2');
                  if (index === 2) classes.push('rank-3');
                  if (col.movementKey) {
                    displayValue = String(displayValue) + WP.formatRankMovement(row[col.movementKey]);
                  }
                } else if (col.type === 'rank') {
                  classes.push('rank');
                  classes.push('numeric');
                  if (value === null || value === undefined || value === 0) {
                    displayValue = '—';
                    dataValue = 999;
                  } else {
                    if (value === 1) classes.push('rank-1');
                    if (value === 2) classes.push('rank-2');
                    if (value === 3) classes.push('rank-3');
                    dataValue = value;
                    if (col.movementKey) {
                      displayValue = String(value) + WP.formatRankMovement(row[col.movementKey]);
                    }
                  }
                } else if (col.type === 'number') {
```

The rest of the column-type `if`/`else if` chain (`'delta'`, `'member'`) is unchanged. Only the closing of the row template needs updating — current code:

```js
                return `<td class="${classes.join(' ')}" ${dataValue !== '' ? `data-value="${dataValue}"` : ''}>${displayValue}</td>`;
              }).join('')}
            </tr>
          `).join('')}
        </tbody>
```

Replace with:

```js
                return `<td class="${classes.join(' ')}" ${dataValue !== '' ? `data-value="${dataValue}"` : ''}>${displayValue}</td>`;
              }).join('')}
            </tr>
          `;
          }).join('')}
        </tbody>
```

(This closes the arrow function with a block body/explicit `return` instead of the old implicit-return template literal, since it now needs to compute `rankTier` before building the row.)

- [ ] **Step 2: Add the rank-tier bar and rank-arrow CSS**

Add to `css/styles.css`, near the existing `/* Rank column */` / `/* Dynamic rank column */` rules (around where `td.rank` / `td.dynamic-rank` are defined):

```css
/* Rank tier bar (top half / bottom half of a ranked table) */
tr.rank-tier-top td:first-child {
  border-left: 4px solid var(--positive);
}

tr.rank-tier-bottom td:first-child {
  border-left: 4px solid var(--negative);
}

/* Rank movement arrows */
.rank-arrow {
  display: inline-block;
  margin-left: 4px;
  font-size: 0.7em;
}

.rank-arrow-up {
  color: var(--positive);
}

.rank-arrow-down {
  color: var(--negative);
}

.rank-arrow-same {
  color: var(--text-muted);
}
```

(`border-left` is applied to each row's first `<td>`, not the `<tr>` itself — with `border-collapse: collapse`, which `table` already uses in this file, borders set directly on `<tr>` are dropped by the collapsed border model and wouldn't render.)

- [ ] **Step 3: Commit**

```bash
git add js/tables.js css/styles.css
git commit -m "Redesign: add rank-tier bar and rank-movement arrow rendering to tables"
```

---

## Task 6: Wire rank movement and tier into the Current Season page

**Files:**
- Modify: `index.html:96-249` (the inline `<script>` block)

- [ ] **Step 1: Compute movement right after `hasData` is known**

In `index.html`, find:

```js
    // Calculate weeks completed
    const weeksCompleted = Object.keys(season2026.weeklyPoints[standingsData[0]?.name] || {}).length;

    // Update stat cards - show "-" if no data
    const hasData = weeksCompleted > 0;
```

Add immediately after that block (still before `topScorer`/`topSidebet`):

```js

    // Week-over-week rank movement, computed client-side from the weekly
    // points/sidebets already loaded above (see spec: Current Season page only).
    const pointsMovement = hasData ? WP.computeRankMovement(season2026.weeklyPoints, weeksCompleted) : {};
    const sidebetMovement = hasData ? WP.computeRankMovement(season2026.weeklySidebets, weeksCompleted) : {};
```

- [ ] **Step 2: Attach movement to the Points Standings rows and enable its rank-tier bar**

Find:

```js
    const pointsWithRank = standingsData.map((m) => ({
      ...m,
      place: null,  // From Yahoo league standings during season
      pointsRank: hasData ? pointsSorted.findIndex(p => p.name === m.name) + 1 : null
    }));

    createTable('pointsStandingsTable', {
      tableId: 'pointsTable',
      defaultSort: 'place',
      defaultOrder: 'asc',
      columns: [
        { key: 'place', label: 'Rank', type: 'rank' },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'totalPoints', label: 'Points', type: 'number', decimals: 1 },
        { key: 'pointsRank', label: 'Pts Rank', type: 'rank' }
      ],
      data: pointsWithRank
    });
```

Replace with:

```js
    const pointsWithRank = standingsData.map((m) => ({
      ...m,
      place: null,  // From Yahoo league standings during season
      pointsRank: hasData ? pointsSorted.findIndex(p => p.name === m.name) + 1 : null,
      pointsMovement: pointsMovement[m.name] || null
    }));

    createTable('pointsStandingsTable', {
      tableId: 'pointsTable',
      defaultSort: 'place',
      defaultOrder: 'asc',
      showRankTier: 'pointsRank',
      columns: [
        { key: 'place', label: 'Rank', type: 'rank' },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'totalPoints', label: 'Points', type: 'number', decimals: 1 },
        { key: 'pointsRank', label: 'Pts Rank', type: 'rank', movementKey: 'pointsMovement' }
      ],
      data: pointsWithRank
    });
```

- [ ] **Step 3: Attach movement to the Sidebet Standings rows and enable its rank-tier bar**

Find:

```js
    const sidebetSortedData = [...sidebetData].sort((a, b) => (b.total || 0) - (a.total || 0));
    createTable('sidebetStandingsTable', {
      tableId: 'sidebetTable',
      defaultSort: 'total',
      defaultOrder: 'desc',
      columns: [
        { key: 'rank', label: 'Rank', type: 'dynamicRank', sortable: false },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'total', label: 'Total', type: 'delta', decimals: 0 },
        { key: 'lowManCount', label: 'Low Man', type: 'number', decimals: 0 }
      ],
      data: sidebetSortedData
    });
```

Replace with:

```js
    const sidebetSortedData = [...sidebetData]
      .sort((a, b) => (b.total || 0) - (a.total || 0))
      .map(m => ({ ...m, sidebetMovement: sidebetMovement[m.name] || null }));

    createTable('sidebetStandingsTable', {
      tableId: 'sidebetTable',
      defaultSort: 'total',
      defaultOrder: 'desc',
      showRankTier: true,
      columns: [
        { key: 'rank', label: 'Rank', type: 'dynamicRank', sortable: false, movementKey: 'sidebetMovement' },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'total', label: 'Total', type: 'delta', decimals: 0 },
        { key: 'lowManCount', label: 'Low Man', type: 'number', decimals: 0 }
      ],
      data: sidebetSortedData
    });
```

(`showRankTier: true` tells the renderer to use each row's post-sort position — `index + 1` — as its rank, since the Sidebet table's rank is `dynamicRank`-typed and has no static rank field the way `pointsRank` does.)

- [ ] **Step 4: Visual check with real week data**

The 2026 season currently has no weekly points (cleared out ahead of the season — see `js/data.js`), so `hasData` is `false` and neither the tier bars nor the arrows will render yet; that's correct/expected. To verify the feature actually works, temporarily test with fixture data in the browser console rather than editing `js/data.js`:

```bash
python3 -m http.server 8930 &
```

Open `http://localhost:8930/index.html`, then in the browser console:

```js
LEAGUE_DATA.seasons['2026'].weeklyPoints = {
  CP: {'1': 100, '2': 90}, Yonk: {'1': 90, '2': 130}, Farber: {'1': 80, '2': 80},
  Rick: {'1': 70, '2': 70}, JB: {'1': 60, '2': 60}, Rizzo: {'1': 50, '2': 50},
  Ben: {'1': 40, '2': 40}, Dues: {'1': 30, '2': 30}, Rich: {'1': 20, '2': 20},
  Stern: {'1': 10, '2': 10}, Andrew: {'1': 9, '2': 9}, Pinkston: {'1': 8, '2': 8},
  Lloyd: {'1': 7, '2': 7}, Jett: {'1': 6, '2': 6}
};
location.reload();
```

Confirm: rows show a green left-edge bar for the top 7 and red for the bottom 7 on both tables, and CP/Yonk show up/down arrows next to their Pts Rank / Rank values (Yonk jumped from 2nd to 1st between week 1 and 2, CP dropped from 1st to 2nd). Then:

```bash
kill %1
```

- [ ] **Step 5: Run the full test suite**

```bash
npx jest
```

Expected: all suites still pass (this task only touches `index.html`, which isn't under test).

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "Redesign: wire rank-tier bars and movement arrows into Current Season tables"
```

---

## Task 7: Full visual QA pass

**Files:** none (verification only)

- [ ] **Step 1: Start a local server and check every page type**

```bash
python3 -m http.server 8930 &
```

Open each of these in the browser tool and screenshot, checking for: dark background throughout, no leftover light-theme colors, legible text/contrast, working sort arrows, working sidebar active-states:

- `http://localhost:8930/index.html` (Current Season)
- `http://localhost:8930/all-time.html`
- `http://localhost:8930/hall-of-fame.html`
- `http://localhost:8930/years/2025.html`
- `http://localhost:8930/members/jb.html`
- `http://localhost:8930/wagers.html`

```bash
kill %1
```

- [ ] **Step 2: Run the full test suite one last time**

```bash
npx jest
```

Expected: all suites pass.

- [ ] **Step 3: Confirm nothing was pushed**

```bash
git status
git log origin/main..HEAD --oneline
```

Expected: `git status` shows a clean working tree, and the log shows this task's commits sitting ahead of `origin/main`, un-pushed — ready for the user's review before anyone runs `git push`.
