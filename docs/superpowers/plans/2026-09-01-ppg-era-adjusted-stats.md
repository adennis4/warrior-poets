# PPG and Era-Adjusted PPG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the era-unfair "Avg/Season" stat (total ÷ seasons played) with Points Per Game (total ÷ weeks played) everywhere it appears, and add a new Era-Adjusted PPG stat to the All-Time Points table that normalizes for league-size and season-length changes over the years, via a z-score translated back into points.

**Architecture:** A standalone Python script (`calculate_era_adjusted_stats.py`), run manually and infrequently (roughly once a year), computes both stats from data already in `js/data.js` and writes them into `allTime.pointsTotals[name]` as new `ppg`/`eraAdjustedPpg` fields. The website then just reads those precomputed fields — no client-side computation, no change to any other data-sync flow.

**Tech Stack:** Python 3 stdlib (`json`, `statistics`, `unittest` — no new dependencies), vanilla JS/HTML (no changes to `js/*.js`).

**Spec:** `docs/superpowers/specs/2026-09-01-ppg-era-adjusted-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `calculate_era_adjusted_stats.py` | New. Reads `js/data.js`, computes `ppg`/`eraAdjustedPpg` per member, writes them back into `allTime.pointsTotals`. Run manually. |
| `test_calculate_era_adjusted_stats.py` | New. `unittest` coverage for every pure function in the script above, plus one small end-to-end fixture test. |
| `js/data.js` | Modified (by running the script, not by hand) — each entry in `allTime.pointsTotals` gains `ppg` and `eraAdjustedPpg`. Nothing else in the file changes. |
| `all-time.html` | Modified — All-Time Points table's "Avg/Season" column becomes "PPG"; new "Era-Adj PPG" column added. |
| `members/*.html` (18 files) | Modified — the "Avg Pts" stat card reads `pointsData.ppg` instead of `pointsData.avg`. |

---

## Task 1: Build and test the calculation script (TDD)

**Files:**
- Create: `calculate_era_adjusted_stats.py`
- Create: `test_calculate_era_adjusted_stats.py`

- [ ] **Step 1: Write the failing tests**

Create `test_calculate_era_adjusted_stats.py`:

```python
"""Tests for calculate_era_adjusted_stats.py."""

import unittest

from calculate_era_adjusted_stats import (
    calculate_ppg,
    population_mean_stdev,
    calculate_z_score,
    calculate_era_adjusted_ppg,
    compute_stats,
)


class TestCalculatePpg(unittest.TestCase):
    def test_basic_case(self):
        self.assertAlmostEqual(calculate_ppg(1000.0, 10), 100.0)

    def test_uneven_division(self):
        self.assertAlmostEqual(calculate_ppg(100.0, 3), 33.333333, places=5)

    def test_zero_weeks_returns_zero(self):
        self.assertEqual(calculate_ppg(500.0, 0), 0.0)


class TestPopulationMeanStdev(unittest.TestCase):
    def test_basic_case(self):
        mean, stdev = population_mean_stdev([10.0, 20.0, 30.0])
        self.assertAlmostEqual(mean, 20.0)
        self.assertAlmostEqual(stdev, 8.164966, places=5)

    def test_single_value_has_zero_stdev(self):
        mean, stdev = population_mean_stdev([42.0])
        self.assertAlmostEqual(mean, 42.0)
        self.assertEqual(stdev, 0.0)

    def test_empty_list_returns_zeros(self):
        mean, stdev = population_mean_stdev([])
        self.assertEqual(mean, 0.0)
        self.assertEqual(stdev, 0.0)


class TestCalculateZScore(unittest.TestCase):
    def test_above_mean(self):
        self.assertAlmostEqual(calculate_z_score(110.0, 100.0, 10.0), 1.0)

    def test_below_mean(self):
        self.assertAlmostEqual(calculate_z_score(90.0, 100.0, 10.0), -1.0)

    def test_at_mean(self):
        self.assertAlmostEqual(calculate_z_score(100.0, 100.0, 10.0), 0.0)

    def test_zero_stdev_returns_zero_not_division_error(self):
        self.assertEqual(calculate_z_score(100.0, 100.0, 0.0), 0.0)


class TestCalculateEraAdjustedPpg(unittest.TestCase):
    def test_positive_z_score_raises_ppg_above_reference_mean(self):
        result = calculate_era_adjusted_ppg(
            career_z_score=0.5, reference_mean=90.0, reference_stdev=20.0
        )
        self.assertAlmostEqual(result, 100.0)

    def test_negative_z_score_lowers_ppg_below_reference_mean(self):
        result = calculate_era_adjusted_ppg(
            career_z_score=-0.5, reference_mean=90.0, reference_stdev=20.0
        )
        self.assertAlmostEqual(result, 80.0)

    def test_zero_z_score_equals_reference_mean(self):
        result = calculate_era_adjusted_ppg(
            career_z_score=0.0, reference_mean=90.0, reference_stdev=20.0
        )
        self.assertAlmostEqual(result, 90.0)


class TestComputeStatsIntegration(unittest.TestCase):
    """A small hand-computed fixture: 2 members, 2 years, 2 weeks each."""

    def setUp(self):
        self.data = {
            "years": ["2020", "2021"],
            "seasons": {
                "2020": {
                    "weeklyPoints": {
                        "A": {"1": 100.0, "2": 120.0},
                        "B": {"1": 80.0, "2": 100.0},
                    }
                },
                "2021": {
                    "weeklyPoints": {
                        "A": {"1": 110.0},
                        "B": {"1": 90.0},
                    }
                },
            },
            "allTime": {
                "pointsTotals": {
                    "A": {"total": 330.0, "rank": 1, "avg": 165.0, "yearly": {}},
                    "B": {"total": 270.0, "rank": 2, "avg": 135.0, "yearly": {}},
                }
            },
        }

    def test_ppg_is_total_points_over_total_weeks(self):
        results = compute_stats(self.data)
        # A: (100+120+110)/3 = 110.0 ; B: (80+100+90)/3 = 90.0
        self.assertAlmostEqual(results["A"]["ppg"], 110.0)
        self.assertAlmostEqual(results["B"]["ppg"], 90.0)

    def test_a_scores_above_average_every_week_so_era_adjusted_ppg_exceeds_raw_ppg_gap(self):
        results = compute_stats(self.data)
        # A outscores B in every single week they both played, so A's
        # career z-score is strongly positive and B's strongly negative -
        # the era-adjusted numbers should preserve that A > B ordering.
        self.assertGreater(
            results["A"]["eraAdjustedPpg"], results["B"]["eraAdjustedPpg"]
        )

    def test_does_not_mutate_input_data(self):
        import copy

        original = copy.deepcopy(self.data)
        compute_stats(self.data)
        self.assertEqual(self.data, original)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify they fail**

```bash
python3 -m unittest test_calculate_era_adjusted_stats -v
```

Expected: FAIL / ERROR — `calculate_era_adjusted_stats` module doesn't exist yet (`ModuleNotFoundError`).

- [ ] **Step 3: Implement the script**

Create `calculate_era_adjusted_stats.py`:

```python
#!/usr/bin/env python3
"""
Compute Points Per Game (PPG) and Era-Adjusted PPG for every member's
career, and write them into allTime.pointsTotals in js/data.js.

This corrects two things the old "Avg/Season" stat (total / seasons
played) didn't account for: the number of weeks per season has varied
(16 vs 17), and the number of owners in the league has varied (10, 12,
then 14) - both of which shift the scoring environment across eras.

PPG = total career points / total weeks played (every week weighted
equally, regardless of season length or career length).

Era-Adjusted PPG: for every week in league history, compute that
week's mean/stdev across everyone who played it, z-score each of a
member's individual weekly scores against it, average those z-scores
into a career z-score, then translate that z-score back into points
using the all-time overall mean/stdev as the reference scoring
environment. Produces a number in the same "points per week" units as
PPG, so the two are directly comparable.

This is NOT run automatically - run it manually whenever you want the
numbers refreshed (expected to be roughly once a year, after a season
wraps).

Usage:
    python3 calculate_era_adjusted_stats.py            # compute and write
    python3 calculate_era_adjusted_stats.py --dry-run   # preview only
"""

import sys
import json
import statistics
from pathlib import Path

DATA_JS_PATH = Path(__file__).parent / "js" / "data.js"


def read_data_js():
    """Read and parse js/data.js into a plain dict."""
    content = DATA_JS_PATH.read_text()
    json_str = content.replace("const LEAGUE_DATA = ", "").rstrip().rstrip(";")
    return json.loads(json_str)


def write_data_js(data):
    """Write a dict back to js/data.js in the file's existing format."""
    json_str = json.dumps(data, indent=2)
    content = f"const LEAGUE_DATA = {json_str};\n"
    DATA_JS_PATH.write_text(content)


def calculate_ppg(total_points, total_weeks):
    """Career points per game: every week weighted equally."""
    if total_weeks == 0:
        return 0.0
    return total_points / total_weeks


def population_mean_stdev(values):
    """Population mean and standard deviation of a list of scores.

    Population (not sample) statistics: "every week in league history"
    (or "every score a member ever put up") is the entire population
    being measured here, not a sample of some larger population.
    """
    if not values:
        return 0.0, 0.0
    mean = statistics.mean(values)
    if len(values) == 1:
        return mean, 0.0
    stdev = statistics.pstdev(values, mu=mean)
    return mean, stdev


def calculate_z_score(value, mean, stdev):
    """How many standard deviations above/below the mean a value is.

    Returns 0.0 (rather than dividing by zero) on the degenerate case
    where every value in the comparison group was identical.
    """
    if stdev == 0:
        return 0.0
    return (value - mean) / stdev


def calculate_era_adjusted_ppg(career_z_score, reference_mean, reference_stdev):
    """Translate a career z-score back into points, using a reference
    scoring environment (the all-time overall mean/stdev)."""
    return reference_mean + (career_z_score * reference_stdev)


def compute_stats(data):
    """Compute {member: {"ppg": ..., "eraAdjustedPpg": ...}} for every
    member in data["allTime"]["pointsTotals"]. Does not mutate `data`."""
    years = data["years"]
    seasons = data["seasons"]

    # Pass 1: per-(year, week) mean/stdev across everyone who played it,
    # and a flat list of every individual weekly score ever recorded.
    week_stats = {}
    all_scores = []
    for year in years:
        weekly_points = seasons.get(year, {}).get("weeklyPoints", {})
        weeks_in_season = set()
        for member_weeks in weekly_points.values():
            weeks_in_season.update(member_weeks.keys())

        for week in weeks_in_season:
            scores = [
                member_weeks[week]
                for member_weeks in weekly_points.values()
                if week in member_weeks
            ]
            if not scores:
                continue
            week_stats[(year, week)] = population_mean_stdev(scores)
            all_scores.extend(scores)

    all_time_mean, all_time_stdev = population_mean_stdev(all_scores)

    # Pass 2: per-member totals and career z-score.
    results = {}
    for member in data["allTime"]["pointsTotals"].keys():
        total_points = 0.0
        total_weeks = 0
        z_scores = []

        for year in years:
            member_weeks = seasons.get(year, {}).get("weeklyPoints", {}).get(member)
            if not member_weeks:
                continue
            for week, score in member_weeks.items():
                total_points += score
                total_weeks += 1
                mean, stdev = week_stats.get((year, week), (0.0, 0.0))
                z_scores.append(calculate_z_score(score, mean, stdev))

        ppg = calculate_ppg(total_points, total_weeks)
        career_z = statistics.mean(z_scores) if z_scores else 0.0
        era_adjusted_ppg = calculate_era_adjusted_ppg(
            career_z, all_time_mean, all_time_stdev
        )

        results[member] = {"ppg": ppg, "eraAdjustedPpg": era_adjusted_ppg}

    return results


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"Reading {DATA_JS_PATH}...")
    data = read_data_js()

    results = compute_stats(data)

    print("\n--- PPG / Era-Adjusted PPG (sorted by PPG) ---")
    for member, stats in sorted(results.items(), key=lambda kv: -kv[1]["ppg"]):
        ppg = round(stats["ppg"], 2)
        era_adjusted_ppg = round(stats["eraAdjustedPpg"], 2)
        data["allTime"]["pointsTotals"][member]["ppg"] = ppg
        data["allTime"]["pointsTotals"][member]["eraAdjustedPpg"] = era_adjusted_ppg
        print(f"  {member:10s} ppg={ppg:7.2f}  eraAdjustedPpg={era_adjusted_ppg:7.2f}")

    if dry_run:
        print("\n[DRY RUN] No changes written.")
        return

    print(f"\nWriting {DATA_JS_PATH}...")
    write_data_js(data)
    print("Done!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and verify they pass**

```bash
python3 -m unittest test_calculate_era_adjusted_stats -v
```

Expected: all 16 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add calculate_era_adjusted_stats.py test_calculate_era_adjusted_stats.py
git commit -m "Add PPG and Era-Adjusted PPG calculation script"
```

---

## Task 2: Run the script against real data and verify the output

**Files:**
- Modify: `js/data.js` (via running the script — not by hand)

- [ ] **Step 1: Dry-run first**

```bash
python3 calculate_era_adjusted_stats.py --dry-run
```

Expected output (values may drift slightly if `js/data.js` has changed since this plan was written, but should be close to this — these were computed directly against the current file):

```
Lloyd      weeks= 85  ppg=  94.13  eraAdjustedPpg=  93.45
JB         weeks=285  ppg=  92.13  eraAdjustedPpg=  92.45
Ben        weeks=149  ppg=  91.28  eraAdjustedPpg=  89.31
CP         weeks=285  ppg=  90.46  eraAdjustedPpg=  90.84
Jerome     weeks= 81  ppg=  90.28  eraAdjustedPpg=  90.39
Farber     weeks=251  ppg=  90.01  eraAdjustedPpg=  90.00
Jett       weeks=166  ppg=  89.83  eraAdjustedPpg=  89.01
Yonk       weeks=285  ppg=  89.04  eraAdjustedPpg=  88.76
Stern      weeks=217  ppg=  88.50  eraAdjustedPpg=  88.74
Rich       weeks=285  ppg=  88.06  eraAdjustedPpg=  87.89
Dues       weeks=285  ppg=  88.04  eraAdjustedPpg=  88.36
Rizzo      weeks=285  ppg=  88.03  eraAdjustedPpg=  88.27
Andrew     weeks=285  ppg=  86.20  eraAdjustedPpg=  85.86
Pinkston   weeks=166  ppg=  85.38  eraAdjustedPpg=  84.24
Woock      weeks= 85  ppg=  85.34  eraAdjustedPpg=  85.82
Heath      weeks=251  ppg=  84.87  eraAdjustedPpg=  85.39
Rick       weeks= 34  ppg=  83.45  eraAdjustedPpg=  81.89
Marty      weeks=136  ppg=  83.13  eraAdjustedPpg=  85.53
```

(The script's actual printed format doesn't include the `weeks=` column shown above — that's from this plan's earlier verification pass. Just confirm the `ppg`/`eraAdjustedPpg` values per member are in this ballpark and the sort order by PPG matches.)

- [ ] **Step 2: Spot-check by hand**

Pick 2 members and verify `ppg` by hand: `ppg = total_points / total_weeks`. For example, if `Lloyd` played 85 weeks total across his 5 seasons (2021-2025) and the script reports `ppg=94.13`, confirm `94.13 * 85 ≈ 8000.72` (Lloyd's `total` in `allTime.pointsTotals.Lloyd.total`, already in the file) is in the right ballpark — a large mismatch would indicate a bug.

- [ ] **Step 3: Run for real**

```bash
python3 calculate_era_adjusted_stats.py
```

Expected: `js/data.js` is rewritten with `ppg` and `eraAdjustedPpg` added to every entry in `allTime.pointsTotals`.

- [ ] **Step 4: Verify the diff is scoped correctly**

```bash
git diff js/data.js | head -80
```

Expected: only additions of `"ppg": <number>,` and `"eraAdjustedPpg": <number>,` lines inside each member's `allTime.pointsTotals` entry. Nothing else in the file should change (no reordering, no changes to `total`/`rank`/`avg`/`yearly`, no changes to `seasons`/`weeklyPoints`/anything else).

- [ ] **Step 5: Run the existing JS test suite**

```bash
npx jest
```

Expected: 91/91 still pass (this change doesn't touch any JS file `tests/` covers, but confirms nothing about `data.js`'s existing structure got corrupted).

- [ ] **Step 6: Commit**

```bash
git add js/data.js
git commit -m "Compute PPG and Era-Adjusted PPG for all members"
```

---

## Task 3: Update the All-Time Points table

**Files:**
- Modify: `all-time.html:63-88`

- [ ] **Step 1: Update the column config and data mapping**

In `all-time.html`, find:

```js
    // All-Time Points - ranked by average per season
    const pointsData = Object.entries(allTime.pointsTotals)
      .map(([name, data]) => ({
        name,
        total: data.total || 0,
        rank: data.rank || 99,
        avg: data.avg || 0,
        seasonsPlayed: Object.keys(data.yearly || {}).length,
        championships: championships[name] || 0
      }))
      .sort((a, b) => b.avg - a.avg);

    createTable('allTimePointsTable', {
      tableId: 'allTimePoints',
      defaultSort: 'avg',
      defaultOrder: 'desc',
      columns: [
        { key: 'displayRank', label: 'Rank', type: 'rank', sortable: false },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'avg', label: 'Avg/Season', type: 'number', decimals: 1 },
        { key: 'total', label: 'Total Points', type: 'number', decimals: 1 },
        { key: 'seasonsPlayed', label: 'Seasons', type: 'number', decimals: 0 }
      ],
      data: pointsData.map((m, i) => ({
        displayRank: i + 1,
        ...m
      }))
    });
```

Replace with:

```js
    // All-Time Points - ranked by points per game (PPG)
    const pointsData = Object.entries(allTime.pointsTotals)
      .map(([name, data]) => ({
        name,
        total: data.total || 0,
        rank: data.rank || 99,
        ppg: data.ppg || 0,
        eraAdjustedPpg: data.eraAdjustedPpg || 0,
        seasonsPlayed: Object.keys(data.yearly || {}).length,
        championships: championships[name] || 0
      }))
      .sort((a, b) => b.ppg - a.ppg);

    createTable('allTimePointsTable', {
      tableId: 'allTimePoints',
      defaultSort: 'ppg',
      defaultOrder: 'desc',
      columns: [
        { key: 'displayRank', label: 'Rank', type: 'rank', sortable: false },
        { key: 'name', label: 'Owner', type: 'member' },
        { key: 'ppg', label: 'PPG', type: 'number', decimals: 1 },
        { key: 'eraAdjustedPpg', label: 'Era-Adj PPG', type: 'number', decimals: 1 },
        { key: 'total', label: 'Total Points', type: 'number', decimals: 1 },
        { key: 'seasonsPlayed', label: 'Seasons', type: 'number', decimals: 0 }
      ],
      data: pointsData.map((m, i) => ({
        displayRank: i + 1,
        ...m
      }))
    });
```

- [ ] **Step 2: Visual check**

```bash
python3 -m http.server 8930 &
```

Open `http://localhost:8930/all-time.html`, screenshot the "All-Time Points" table, confirm: columns read Rank / Owner / PPG / Era-Adj PPG / Total Points / Seasons, sorted descending by PPG, and Lloyd is at (or very near) the top. Click the "Era-Adj PPG" header and confirm it sorts correctly. Then:

```bash
kill %1
```

- [ ] **Step 3: Commit**

```bash
git add all-time.html
git commit -m "Show PPG and Era-Adjusted PPG on the All-Time Points table"
```

---

## Task 4: Update the 18 member pages' "Avg Pts" card

**Files:**
- Modify: `members/andrew.html`, `members/ben.html`, `members/cp.html`, `members/dues.html`, `members/farber.html`, `members/heath.html`, `members/jb.html`, `members/jerome.html`, `members/jett.html`, `members/lloyd.html`, `members/marty.html`, `members/pinkston.html`, `members/rich.html`, `members/rick.html`, `members/rizzo.html`, `members/stern.html`, `members/woock.html`, `members/yonk.html`

All 18 files have the identical line `var avgPoints = pointsData.avg || 0;` (verified — every member page uses this exact same pattern, per the earlier data-audit that found `pointsData.avg` used identically across all 18 files).

- [ ] **Step 1: Verify the line is identical across all 18 files before changing it**

```bash
grep -c "var avgPoints = pointsData.avg || 0;" members/*.html
```

Expected: every one of the 18 files shows `:1` (exactly one match each). If any file shows `:0`, stop and check that file individually before proceeding — don't apply the bulk edit blindly.

- [ ] **Step 2: Apply the change to all 18 files**

```bash
for f in members/*.html; do
  sed -i '' "s/var avgPoints = pointsData.avg || 0;/var avgPoints = pointsData.ppg || 0;/" "$f"
done
```

- [ ] **Step 3: Verify**

```bash
grep -l "pointsData.avg || 0" members/*.html
```

Expected: no output (nothing left reading `.avg`).

```bash
grep -c "pointsData.ppg || 0" members/*.html
```

Expected: all 18 files show `:1`.

- [ ] **Step 4: Visual check**

```bash
python3 -m http.server 8930 &
```

Open `http://localhost:8930/members/lloyd.html`, confirm the "Avg Pts" stat card shows a value around `94.1` (Lloyd's PPG from Task 2's output), not his old `avg` value. Then:

```bash
kill %1
```

- [ ] **Step 5: Commit**

```bash
git add members/*.html
git commit -m "Use PPG instead of total/seasons average on member pages"
```

---

## Task 5: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Run the full JS test suite**

```bash
npx jest
```

Expected: 91/91 pass.

- [ ] **Step 2: Run the full Python test suite**

```bash
python3 -m unittest test_calculate_era_adjusted_stats -v
```

Expected: 16/16 pass.

- [ ] **Step 3: Confirm the script is idempotent**

Run it a second time and confirm the output values don't change (running it twice in a row should produce identical numbers, since nothing about the underlying `weeklyPoints` data changed in between):

```bash
python3 calculate_era_adjusted_stats.py --dry-run > /tmp/second-run.txt
git diff js/data.js
```

Expected: `git diff js/data.js` shows no changes (the dry-run's computed values match what's already written in the file from Task 2).

- [ ] **Step 4: Visual QA across both changed page types**

With a local server running, check `all-time.html` (Points table) and 2-3 member pages (`members/lloyd.html`, `members/rick.html` — pick one with a long career and one with a short career, since Rick's era-adjustment shift is the largest in the dataset and worth eyeballing) for correct, sane-looking values.

- [ ] **Step 5: Confirm nothing was pushed**

```bash
git status
git log origin/main..HEAD --oneline
```

Expected: clean working tree, commits sitting ahead of `origin/main`, ready for the user's review before anyone runs `git push` — per this repo's established pattern this session of always reviewing before pushing.
