# Manual Yahoo Score Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the now-blocked Yahoo API sync with a manual, on-demand workflow: read live scores from the Browser pane (real page text, not screenshot OCR), verify the extraction with two independent sequential passes before trusting it, then write a full weekly update (points, sidebets, standings) into `js/data.js`.

**Architecture:** A new script, `update_week_scores.py`, takes a verified `{member: score}` JSON for one week and computes everything CLAUDE.md's sidebet formula implies from it — that week's payouts, and the season's running point/sidebet totals and ranks. The verification step that produces that JSON happens separately, via two independent passes over the live Yahoo page (see Task 3), before the script ever runs.

**Tech Stack:** Python 3 stdlib (`json`, `unittest` — matches `calculate_era_adjusted_stats.py`'s existing pattern, no new dependencies), Claude Code's Browser pane tools for live-page reading.

**Spec:** `docs/superpowers/specs/2026-09-13-yahoo-screenshot-sync-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `update_week_scores.py` | New. Takes a year, week, and a verified scores JSON file; computes and writes that week's `weeklyPoints`, `weeklySidebets`, and the season's running `standings`/`sidebetStandings` into `js/data.js`. |
| `test_update_week_scores.py` | New. `unittest` coverage for every pure function, plus an integration test on a small fixture. |
| `js/data.js` | Modified (by running the script, not by hand) — Week 1 2026 data populated. |

---

## Task 1: Build and test the update script (TDD)

**Files:**
- Create: `update_week_scores.py`
- Create: `test_update_week_scores.py`

- [ ] **Step 1: Write the failing tests**

Create `test_update_week_scores.py`:

```python
"""Tests for update_week_scores.py."""

import unittest
from unittest.mock import patch

from update_week_scores import (
    calculate_sidebet_payout,
    rank_members_by_score,
    compute_weekly_sidebets,
    compute_season_totals,
    compute_low_man_count,
    validate_scores,
    update_week,
    TEAM_NAME_TO_MEMBER,
)


class TestCalculateSidebetPayout(unittest.TestCase):
    def test_rank_1_is_65(self):
        self.assertEqual(calculate_sidebet_payout(1), 65)

    def test_rank_7_is_5(self):
        self.assertEqual(calculate_sidebet_payout(7), 5)

    def test_rank_8_is_negative_5(self):
        self.assertEqual(calculate_sidebet_payout(8), -5)

    def test_rank_14_is_negative_65(self):
        self.assertEqual(calculate_sidebet_payout(14), -65)


class TestRankMembersByScore(unittest.TestCase):
    def test_basic_ranking_highest_score_is_rank_1(self):
        scores = {"A": 100.0, "B": 90.0, "C": 110.0}
        order = ["A", "B", "C"]
        ranks = rank_members_by_score(scores, order)
        self.assertEqual(ranks, {"C": 1, "A": 2, "B": 3})

    def test_tie_broken_by_position_in_fixed_order(self):
        scores = {"A": 100.0, "B": 100.0, "C": 90.0}
        order = ["B", "A", "C"]  # B listed before A -> B wins the tie
        ranks = rank_members_by_score(scores, order)
        self.assertEqual(ranks["B"], 1)
        self.assertEqual(ranks["A"], 2)
        self.assertEqual(ranks["C"], 3)


class TestComputeWeeklySidebets(unittest.TestCase):
    def test_two_members(self):
        scores = {"A": 100.0, "B": 90.0}
        order = ["A", "B"]
        payouts = compute_weekly_sidebets(scores, order)
        self.assertEqual(payouts, {"A": 65, "B": 55})

    def test_full_14_member_week_sums_to_zero(self):
        order = [f"M{i}" for i in range(1, 15)]
        scores = {m: float(100 - i) for i, m in enumerate(order)}
        payouts = compute_weekly_sidebets(scores, order)
        self.assertEqual(sum(payouts.values()), 0)


class TestComputeSeasonTotals(unittest.TestCase):
    def test_sums_across_weeks_and_ranks(self):
        values = {
            "A": {"1": 100.0, "2": 90.0},
            "B": {"1": 80.0, "2": 85.0},
        }
        order = ["A", "B"]
        result = compute_season_totals(values, order)
        self.assertAlmostEqual(result["A"]["total"], 190.0)
        self.assertAlmostEqual(result["B"]["total"], 165.0)
        self.assertEqual(result["A"]["rank"], 1)
        self.assertEqual(result["B"]["rank"], 2)


class TestComputeLowManCount(unittest.TestCase):
    def test_counts_negative_65_entries(self):
        weekly = {"1": -65, "2": 45, "3": -65}
        self.assertEqual(compute_low_man_count(weekly), 2)

    def test_zero_when_never_last(self):
        weekly = {"1": 65, "2": -5}
        self.assertEqual(compute_low_man_count(weekly), 0)


class TestValidateScores(unittest.TestCase):
    def test_passes_with_exact_2026_roster(self):
        scores = {m: 90.0 for m in TEAM_NAME_TO_MEMBER["2026"].values()}
        validate_scores(scores, "2026")  # should not raise

    def test_raises_on_missing_member(self):
        scores = {m: 90.0 for m in TEAM_NAME_TO_MEMBER["2026"].values()}
        del scores["CP"]
        with self.assertRaises(ValueError):
            validate_scores(scores, "2026")

    def test_raises_on_unexpected_member(self):
        scores = {m: 90.0 for m in TEAM_NAME_TO_MEMBER["2026"].values()}
        scores["NotARealMember"] = 50.0
        with self.assertRaises(ValueError):
            validate_scores(scores, "2026")


class TestUpdateWeekIntegration(unittest.TestCase):
    def setUp(self):
        self.data = {
            "seasons": {
                "2026": {
                    "weeklyPoints": {},
                    "weeklySidebets": {},
                    "standings": {},
                    "sidebetStandings": {},
                }
            }
        }

    @patch.dict(
        "update_week_scores.TEAM_NAME_TO_MEMBER",
        {"2026": {"Team A": "A", "Team B": "B"}},
        clear=True,
    )
    def test_single_week_two_members(self):
        scores = {"A": 100.0, "B": 90.0}
        update_week(self.data, "2026", 1, scores)

        season = self.data["seasons"]["2026"]
        self.assertEqual(season["weeklyPoints"]["A"]["1"], 100.0)
        self.assertEqual(season["weeklyPoints"]["B"]["1"], 90.0)
        self.assertEqual(season["weeklySidebets"]["A"]["1"], 65)
        # Only 2 members in this fixture, so rank 2's payout is 75-2*10=55
        # (positive) - "-65" specifically means rank 14 in a real 14-person
        # league, which this small fixture can't produce.
        self.assertEqual(season["weeklySidebets"]["B"]["1"], 55)
        self.assertEqual(season["standings"]["A"]["totalPoints"], 100.0)
        self.assertEqual(season["standings"]["A"]["pointsRank"], 1)
        self.assertIsNone(season["standings"]["A"]["yearEndStanding"])
        self.assertEqual(season["sidebetStandings"]["A"]["total"], 65)
        self.assertEqual(season["sidebetStandings"]["A"]["lowManCount"], 0)
        self.assertEqual(season["sidebetStandings"]["B"]["lowManCount"], 0)

    @patch.dict(
        "update_week_scores.TEAM_NAME_TO_MEMBER",
        {"2026": {"Team A": "A", "Team B": "B"}},
        clear=True,
    )
    def test_second_week_accumulates_onto_the_first(self):
        update_week(self.data, "2026", 1, {"A": 100.0, "B": 90.0})
        update_week(self.data, "2026", 2, {"A": 80.0, "B": 95.0})

        season = self.data["seasons"]["2026"]
        self.assertEqual(season["standings"]["A"]["totalPoints"], 180.0)
        self.assertEqual(season["standings"]["B"]["totalPoints"], 185.0)
        self.assertEqual(season["standings"]["B"]["pointsRank"], 1)
        self.assertEqual(season["standings"]["A"]["pointsRank"], 2)
        # A got rank 1 in week 1 (payout 65) and rank 2 in week 2 (payout
        # 55); B is the mirror image. Neither ever hits rank 14/-65 in this
        # 2-member fixture, so both stay at lowManCount 0 - see the note in
        # the previous test.
        self.assertEqual(season["sidebetStandings"]["A"]["total"], 120)
        self.assertEqual(season["sidebetStandings"]["B"]["total"], 120)
        self.assertEqual(season["sidebetStandings"]["A"]["lowManCount"], 0)
        self.assertEqual(season["sidebetStandings"]["B"]["lowManCount"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and verify they fail**

```bash
python3 -m unittest test_update_week_scores -v
```

Expected: FAIL / ERROR — `update_week_scores` module doesn't exist yet (`ModuleNotFoundError`).

- [ ] **Step 3: Implement the script**

Create `update_week_scores.py`:

```python
#!/usr/bin/env python3
"""
Write one week's verified Yahoo scores into js/data.js, and recompute
everything CLAUDE.md's sidebet formula implies from it: that week's
payouts, and the season's running point/sidebet totals and ranks.

This does NOT talk to Yahoo itself - it takes an already-verified
{member: score} JSON for one week (see the dual-extraction process
this is meant to be used with) and does the math + file write.

Usage:
    python3 update_week_scores.py <year> <week> <path/to/scores.json>

Where scores.json looks like:
    {"CP": 39.92, "Yonk": 45.86, ...}
(one entry per member playing that season - see TEAM_NAME_TO_MEMBER
below for the current roster)
"""

import sys
import json
from pathlib import Path

DATA_JS_PATH = Path(__file__).parent / "js" / "data.js"

# Yahoo team name -> data.js member name, per season. Team names are chosen
# by each owner and can change year to year, so this is keyed by year rather
# than being a single global mapping. Confirmed directly against the live
# Yahoo league page for 2026.
TEAM_NAME_TO_MEMBER = {
    "2026": {
        "Beanie's Babies": "CP",
        "Let's Go Aiyuk!": "Yonk",
        "K.Y.K (.)(.)": "JB",
        "Berry Domesticated": "Rizzo",
        "No LAmbs": "Ben",
        "Dues is Lucy": "Dues",
        "Destroying YOR": "Farber",
        "Schmitz & Giggles": "Rick",
        "3X Champ - Hudson's Pack": "Stern",
        "Hot Lloyd Summer": "Lloyd",
        "Los Catchadores": "Jett",
        "Obligatory Invite": "Pinkston",
        "On Cam's Back": "Andrew",
        "Here to break even": "Rich",
    }
}


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


def calculate_sidebet_payout(rank):
    """rank 1-14 -> payout, per CLAUDE.md's documented formula."""
    return 75 - (rank * 10)


def rank_members_by_score(scores, tie_break_order):
    """
    scores: {member: score}
    tie_break_order: list of members in a fixed, deterministic order used
        to break ties (whoever appears earlier in this list wins the tie).
    Returns {member: rank}, where rank 1 is the highest score.
    """
    def sort_key(member):
        return (-scores[member], tie_break_order.index(member))

    ranked = sorted(scores.keys(), key=sort_key)
    return {member: index + 1 for index, member in enumerate(ranked)}


def compute_weekly_sidebets(scores, tie_break_order):
    """scores: {member: score} for one week -> {member: payout}."""
    ranks = rank_members_by_score(scores, tie_break_order)
    return {member: calculate_sidebet_payout(rank) for member, rank in ranks.items()}


def compute_season_totals(values_by_member, tie_break_order):
    """
    values_by_member: {member: {week: value}} - either weeklyPoints or
        weeklySidebets, summed across however many weeks are present.
    Returns {member: {"total": ..., "rank": ...}}.
    """
    totals = {member: sum(weeks.values()) for member, weeks in values_by_member.items()}
    ranks = rank_members_by_score(totals, tie_break_order)
    return {
        member: {"total": totals[member], "rank": ranks[member]}
        for member in values_by_member
    }


def compute_low_man_count(weekly_sidebets_for_member):
    """weekly_sidebets_for_member: {week: payout} for one member."""
    return sum(1 for payout in weekly_sidebets_for_member.values() if payout == -65)


def validate_scores(scores, year):
    """Raise ValueError unless scores has exactly this year's roster."""
    expected = set(TEAM_NAME_TO_MEMBER[year].values())
    actual = set(scores.keys())
    if actual != expected:
        missing = sorted(expected - actual) or "none"
        extra = sorted(actual - expected) or "none"
        raise ValueError(
            f"scores.json doesn't match the {year} roster. "
            f"Missing: {missing}. Unexpected: {extra}."
        )


def update_week(data, year, week, scores):
    """
    Mutate `data` in place: write this week's scores and sidebets, and
    recompute the season's running standings/sidebetStandings from every
    week entered so far. Returns `data`.
    """
    tie_break_order = list(TEAM_NAME_TO_MEMBER[year].values())
    week_key = str(week)

    season = data["seasons"][year]

    weekly_points = season.setdefault("weeklyPoints", {})
    for member, score in scores.items():
        weekly_points.setdefault(member, {})[week_key] = score

    weekly_sidebets_this_week = compute_weekly_sidebets(scores, tie_break_order)
    weekly_sidebets = season.setdefault("weeklySidebets", {})
    for member, payout in weekly_sidebets_this_week.items():
        weekly_sidebets.setdefault(member, {})[week_key] = payout

    points_totals = compute_season_totals(weekly_points, tie_break_order)
    standings = season.setdefault("standings", {})
    for member, agg in points_totals.items():
        entry = standings.setdefault(member, {})
        entry["totalPoints"] = agg["total"]
        entry["pointsRank"] = agg["rank"]
        entry.setdefault("yearEndStanding", None)

    sidebet_totals = compute_season_totals(weekly_sidebets, tie_break_order)
    sidebet_standings = season.setdefault("sidebetStandings", {})
    for member, agg in sidebet_totals.items():
        entry = sidebet_standings.setdefault(member, {})
        entry["total"] = agg["total"]
        entry["rank"] = agg["rank"]
        entry["lowManCount"] = compute_low_man_count(weekly_sidebets[member])

    return data


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 update_week_scores.py <year> <week> <path/to/scores.json>")
        sys.exit(1)

    year = sys.argv[1]
    week = int(sys.argv[2])
    scores_path = Path(sys.argv[3])

    scores = json.loads(scores_path.read_text())
    validate_scores(scores, year)

    print(f"Reading {DATA_JS_PATH}...")
    data = read_data_js()

    if year not in data.get("seasons", {}):
        data.setdefault("seasons", {})[year] = {}

    update_week(data, year, week, scores)

    print(f"Writing {DATA_JS_PATH}...")
    write_data_js(data)

    tie_break_order = list(TEAM_NAME_TO_MEMBER[year].values())
    ranks = rank_members_by_score(scores, tie_break_order)
    print(f"\nWeek {week} ({year}) - {len(scores)} members:")
    for member in sorted(ranks, key=lambda m: ranks[m]):
        payout = calculate_sidebet_payout(ranks[member])
        print(f"  {ranks[member]:>2}. {member:10s} {scores[member]:7.2f} pts  ({payout:+d})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the tests and verify they pass**

```bash
python3 -m unittest test_update_week_scores -v
```

Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add update_week_scores.py test_update_week_scores.py
git commit -m "$(cat <<'EOF'
Add script to write verified weekly Yahoo scores into data.js

Computes that week's sidebet payouts and the season's running
standings/sidebetStandings per CLAUDE.md's payout formula, from a
pre-verified {member: score} JSON for one week.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Dry-run the script against a scratch copy of data.js

**Files:** none (verification only — do not touch the real `js/data.js` in this task)

- [ ] **Step 1: Make a scratch copy**

```bash
mkdir -p /tmp/uws_check/js
cp js/data.js /tmp/uws_check/js/data.js
cp update_week_scores.py /tmp/uws_check/
```

- [ ] **Step 2: Write a small fake scores file and run the script against the copy**

```bash
cd /tmp/uws_check
python3 -c "
import json
fake = {
    'CP': 39.92, 'Yonk': 45.86, 'JB': 50.0, 'Rizzo': 34.16, 'Ben': 60.0,
    'Dues': 92.45, 'Farber': 55.0, 'Rick': 70.0, 'Stern': 65.0, 'Lloyd': 80.0,
    'Jett': 101.75, 'Pinkston': 40.0, 'Andrew': 45.86, 'Rich': 95.23
}
json.dump(fake, open('fake_scores.json', 'w'))
"
python3 update_week_scores.py 2026 1 fake_scores.json
```

Expected: prints a ranked list of all 14 members with points and payouts, payouts sum to 0, and `js/data.js` in `/tmp/uws_check` now has a populated `2026` season.

- [ ] **Step 3: Verify the real repo's data.js was NOT touched**

```bash
cd /Users/andrew/Code/warrior-poets
git status --short js/data.js
```

Expected: no output (clean) — this task only ever touched the `/tmp/uws_check` scratch copy.

- [ ] **Step 4: Clean up the scratch directory**

```bash
rm -rf /tmp/uws_check
```

No commit for this task — it's a dry run with no real changes.

---

## Task 3: Dual-verified extraction of real Week 1 scores

**Files:** none (this task produces a verified scores JSON for Task 4 to consume — it does not write to `js/data.js` itself)

This task requires the user to be logged into Yahoo Fantasy in the Browser pane (`mcp__Claude_Browser__*`) for this conversation. If a screenshot/page-read shows a Yahoo login screen instead of the matchups page, stop and ask the user to log in before continuing — do not guess or proceed with incomplete data.

- [ ] **Step 1: Dispatch the first extraction pass (Agent 1)**

Dispatch a subagent with this task (it needs Browser pane tool access):

```
Navigate the Browser pane to https://football.fantasysports.yahoo.com/f1/739035
(the "Warrior Poets" league). Find the Week 1 matchups. If you land on a
Yahoo login page instead of the matchups, STOP and report BLOCKED - do not
guess at scores.

Read the page's actual text content (not a screenshot) to find each of the
14 teams' final score for Week 1. The 14 team names and their owners are:

  Beanie's Babies -> CP
  Let's Go Aiyuk! -> Yonk
  K.Y.K (.)(.) -> JB
  Berry Domesticated -> Rizzo
  No LAmbs -> Ben
  Dues is Lucy -> Dues
  Destroying YOR -> Farber
  Schmitz & Giggles -> Rick
  3X Champ - Hudson's Pack -> Stern
  Hot Lloyd Summer -> Lloyd
  Los Catchadores -> Jett
  Obligatory Invite -> Pinkston
  On Cam's Back -> Andrew
  Here to break even -> Rich

For each team, find its Week 1 final score on the page and map it to the
owner using the table above. If you see a team name on the page that ISN'T
in this table, report it clearly as unmapped rather than guessing which
owner it might be.

Report back a JSON object with exactly these 14 keys (owner names) and
their Week 1 scores as the values, e.g.:
  {"CP": 39.92, "Yonk": 45.86, ...}

Report ONLY this JSON and which page/URL you read it from. Do not report a
partial result if you can't find all 14 - report BLOCKED with whatever you
could and couldn't find instead.
```

- [ ] **Step 2: Wait for Agent 1 to finish, then dispatch the second, independent pass (Agent 2)**

Once Agent 1 has reported back, dispatch a **second, separate** subagent with the **exact same task text** as Step 1 (copy it verbatim — do not mention Agent 1's result anywhere in this second agent's task, and do not run it at the same time as Agent 1 was running).

- [ ] **Step 3: Compare the two results**

Compare Agent 1's and Agent 2's 14-entry JSON results, member by member.

- If every one of the 14 values matches exactly between the two: proceed to Step 4.
- If anything differs (even one member, even a small decimal difference): **stop**. Show the user both agents' results side by side, highlighting the specific discrepancy, and ask them to confirm the correct value by checking the live page themselves before proceeding. Do not average the two values or pick one arbitrarily.

- [ ] **Step 4: Save the verified result**

Once both passes agree exactly, save the confirmed `{member: score}` JSON to a file for Task 4 to use:

```bash
cat > /tmp/week1_2026_scores.json << 'EOF'
{
  "CP": <verified value>,
  "Yonk": <verified value>,
  "JB": <verified value>,
  "Rizzo": <verified value>,
  "Ben": <verified value>,
  "Dues": <verified value>,
  "Farber": <verified value>,
  "Rick": <verified value>,
  "Stern": <verified value>,
  "Lloyd": <verified value>,
  "Jett": <verified value>,
  "Pinkston": <verified value>,
  "Andrew": <verified value>,
  "Rich": <verified value>
}
EOF
```

(Fill in the actual agreed-upon values from Step 3 — this heredoc is a template, not literal output. Validate it's well-formed JSON with all 14 keys before moving on: `python3 -c "import json; d = json.load(open('/tmp/week1_2026_scores.json')); assert len(d) == 14; print('OK', d)"`.)

No commit for this task — nothing in the git repo changes yet.

---

## Task 4: Write Week 1 to the real data.js

**Files:**
- Modify: `js/data.js` (via running the script — not by hand)

- [ ] **Step 1: Run the script for real**

```bash
python3 update_week_scores.py 2026 1 /tmp/week1_2026_scores.json
```

Expected: prints all 14 members ranked by Week 1 score with their payouts, payouts sum to $0.

- [ ] **Step 2: Verify the diff is scoped correctly**

```bash
git diff js/data.js | head -100
```

Expected: only the `2026` season's `weeklyPoints`, `weeklySidebets`, `standings`, and `sidebetStandings` sections changed (previously all empty/zeroed per the season-start data clear from earlier this project) — no other season, no other top-level key, touched.

- [ ] **Step 3: Spot-check against the live page**

Compare 2-3 members' scores and ranks in the diff against what's actually showing on the live Yahoo matchups page right now (screenshot or re-read the page) to confirm the numbers genuinely match what a human would see.

- [ ] **Step 4: Run the full test suites**

```bash
npx jest
python3 -m unittest test_update_week_scores -v
python3 -m unittest test_calculate_era_adjusted_stats -v
```

Expected: all pass (91 JS tests, 13 new Python tests, 16 existing Python tests — none of this task's changes touch those other test files, this just confirms nothing else broke).

- [ ] **Step 5: Commit**

```bash
git add js/data.js
git commit -m "$(cat <<'EOF'
Populate 2026 Week 1 scores, sidebets, and standings

Extracted from the live Yahoo Fantasy matchups page via two
independent verification passes (see docs/superpowers/specs/
2026-09-13-yahoo-screenshot-sync-design.md) - both passes agreed on
every value before this was written.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Final verification

**Files:** none (verification only)

- [ ] **Step 1: Confirm the site actually renders the new data**

```bash
python3 -m http.server 8930 &
```

Open `http://localhost:8930/index.html`, confirm the Points/Sidebet Standings tables and Weekly Breakdown tables now show real Week 1 numbers instead of "—" placeholders, and the rank-tier bars/movement-arrow feature (built earlier this project) renders sensibly with real data for the first time. Then:

```bash
kill %1
```

- [ ] **Step 2: Confirm nothing was pushed**

```bash
git status
git log origin/main..HEAD --oneline
```

Expected: clean working tree, this task's commits sitting ahead of `origin/main`, ready for the user's review before anyone runs `git push` — per this project's standing convention.
