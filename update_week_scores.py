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
