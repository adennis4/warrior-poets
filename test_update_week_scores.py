"""Tests for update_week_scores.py."""

import json
import os
import sys
import tempfile
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
    main,
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

    def test_season_level_tie_broken_by_position_in_fixed_order(self):
        # Both members total 100.0 across the season, even though neither
        # week is individually tied - this exercises compute_season_totals'
        # own tie-breaking, not just rank_members_by_score in isolation.
        values = {
            "A": {"1": 50.0, "2": 50.0},
            "B": {"1": 60.0, "2": 40.0},
        }
        order = ["B", "A"]  # B listed before A -> B wins the tie
        result = compute_season_totals(values, order)
        self.assertEqual(result["A"]["total"], 100.0)
        self.assertEqual(result["B"]["total"], 100.0)
        self.assertEqual(result["B"]["rank"], 1)
        self.assertEqual(result["A"]["rank"], 2)


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

    @patch.dict(
        "update_week_scores.TEAM_NAME_TO_MEMBER",
        {"2026": {"Team A": "A", "Team B": "B"}},
        clear=True,
    )
    def test_three_consecutive_weeks_accumulate(self):
        update_week(self.data, "2026", 1, {"A": 100.0, "B": 90.0})
        update_week(self.data, "2026", 2, {"A": 80.0, "B": 95.0})
        update_week(self.data, "2026", 3, {"A": 70.0, "B": 60.0})

        season = self.data["seasons"]["2026"]
        self.assertEqual(season["standings"]["A"]["totalPoints"], 250.0)
        self.assertEqual(season["standings"]["B"]["totalPoints"], 245.0)
        self.assertEqual(season["standings"]["A"]["pointsRank"], 1)
        self.assertEqual(season["standings"]["B"]["pointsRank"], 2)
        # Week 1: A rank1 (+65), B rank2 (+55).
        # Week 2: B rank1 (+65), A rank2 (+55).
        # Week 3: A rank1 (+65), B rank2 (+55).
        # A: 65+55+65=185, B: 55+65+55=175.
        self.assertEqual(season["sidebetStandings"]["A"]["total"], 185)
        self.assertEqual(season["sidebetStandings"]["B"]["total"], 175)
        self.assertEqual(season["sidebetStandings"]["A"]["lowManCount"], 0)
        self.assertEqual(season["sidebetStandings"]["B"]["lowManCount"], 0)

    @patch.dict(
        "update_week_scores.TEAM_NAME_TO_MEMBER",
        {"2026": {"Team A": "A", "Team B": "B"}},
        clear=True,
    )
    def test_raises_when_scores_dont_match_roster(self):
        with self.assertRaises(ValueError):
            update_week(self.data, "2026", 1, {"A": 100.0, "NotARealMember": 90.0})


class TestMainSmoke(unittest.TestCase):
    """
    Smoke-tests main(): the CLI entry point, which otherwise has zero
    coverage even though it's the only thing actually invoked from the
    command line. Mocks file I/O (read_data_js/write_data_js) and uses a
    real temp file for the scores.json argv path, but leaves
    validate_scores as the real function (wrapped, so we can assert on
    calls) since we want to confirm the actual validation wiring, not a
    stand-in for it.
    """

    @patch.dict(
        "update_week_scores.TEAM_NAME_TO_MEMBER",
        {"2026": {"Team A": "A", "Team B": "B"}},
        clear=True,
    )
    @patch("update_week_scores.write_data_js")
    @patch("update_week_scores.read_data_js")
    def test_main_validates_and_bootstraps_new_season(self, mock_read, mock_write):
        # Simulates a brand new season: no "2026" key under "seasons" yet.
        mock_read.return_value = {"seasons": {}}

        scores = {"A": 100.0, "B": 90.0}
        fd, scores_path = tempfile.mkstemp(suffix=".json")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(scores, f)

            real_validate_scores = validate_scores
            with patch(
                "update_week_scores.validate_scores", wraps=real_validate_scores
            ) as mock_validate:
                with patch.object(
                    sys, "argv", ["update_week_scores.py", "2026", "1", scores_path]
                ):
                    main()
        finally:
            os.unlink(scores_path)

        # validate_scores is called once explicitly in main() and once more
        # inside update_week (defense-in-depth per the plan) - both calls
        # succeed as no-ops since the scores are valid, so this should be
        # exactly 2 calls, not an error.
        self.assertEqual(mock_validate.call_count, 2)
        mock_validate.assert_called_with(scores, "2026")

        # New-season bootstrap branch: "2026" should now exist under
        # "seasons" and have been populated by update_week.
        mock_write.assert_called_once()
        written_data = mock_write.call_args[0][0]
        self.assertIn("2026", written_data["seasons"])
        season = written_data["seasons"]["2026"]
        self.assertEqual(season["standings"]["A"]["totalPoints"], 100.0)
        self.assertEqual(season["standings"]["B"]["totalPoints"], 90.0)
        self.assertEqual(season["weeklySidebets"]["A"]["1"], 65)
        self.assertEqual(season["weeklySidebets"]["B"]["1"], 55)


if __name__ == "__main__":
    unittest.main()
