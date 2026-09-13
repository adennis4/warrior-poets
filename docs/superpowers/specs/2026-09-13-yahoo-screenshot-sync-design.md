# Manual Yahoo Score Sync (Browser-Read, Dual-Verified)

## Context

Yahoo's Fantasy Sports API access now requires a formal application/review process (`sports.yahoo.com/developer/access/`) that the existing `sync_yahoo_data.py`/`yahoo_fantasy.py` integration depends on — see the diagnostic work in this conversation, which conclusively ruled out account mismatch, stale tokens, and app misconfiguration, and confirmed the block is a Yahoo platform-level restriction (even the most generic endpoint, `/game/nfl`, 403s with a fully fresh token from the confirmed-correct account). Approval timeline is unknown and not guaranteed.

This is the **permanent replacement** for weekly data entry while that's pending (not a stopgap) — the user has low confidence API approval will come through.

## Approach

Since Yahoo's API is unavailable but the regular Yahoo Fantasy *website* remains fully usable in a browser, this reads the live matchups page directly through Claude Code's Browser pane (`mcp__Claude_Browser__*`), logged in as the user, and extracts each team's score from the page's actual text/DOM — not a screenshot interpreted visually, which would risk OCR-style misreads on numbers that drive real money calculations.

**Trigger**: on-demand only. The user asks (e.g. "sync week 2"); there's no scheduled/autonomous job. A scheduled job risks failing silently if the Yahoo login session in the Browser pane has expired, which requires human re-login to fix anyway — on-demand keeps a human in the loop for exactly the failure mode that would otherwise need one.

**Session note**: the Browser pane's Yahoo login is tied to the current conversation. In a new conversation, the user will likely need to log in again in that pane before a sync can run.

## Team name → owner mapping (2026)

Yahoo team names don't map to owner names, and can change season to season (confirmed by comparing 2025's team names, read from the user's own spreadsheet earlier in this project, against 2026's actual names — e.g. Andrew's team changed from "On Pat's Back" to "On Cam's Back"). Confirmed directly with the user for the current season:

| Team Name (2026) | Owner |
|---|---|
| Beanie's Babies | CP |
| Let's Go Aiyuk! | Yonk |
| K.Y.K (.)(.) | JB |
| Berry Domesticated | Rizzo |
| No LAmbs | Ben |
| Dues is Lucy | Dues |
| Destroying YOR | Farber |
| Schmitz & Giggles | Rick |
| 3X Champ - Hudson's Pack | Stern |
| Hot Lloyd Summer | Lloyd |
| Los Catchadores | Jett |
| Obligatory Invite | Pinkston |
| On Cam's Back | Andrew |
| Here to break even | Rich |

Stored as a Python dict keyed by year (`TEAM_NAME_TO_MEMBER["2026"] = {...}`) in the new script, so future seasons extend the mapping without touching prior years' data. If a season's page shows a team name not in that year's mapping, the extraction must flag it rather than guess.

## Dual-verified extraction

Because this data drives real money payouts, every week's sync gets independently extracted twice before anything is written:

1. Dispatch a subagent (Agent 1) with browser access: navigate to the matchups page for the requested year/week, read the page's actual text content, extract all 14 teams' names and scores, map each to an owner via the table above, and report back a clean `{member: score}` result — 14 entries, nothing guessed for an unmapped team name.
2. Wait for Agent 1 to finish, then dispatch a second, independent subagent (Agent 2) to do the exact same thing from scratch, with no knowledge of Agent 1's result.
3. **Sequential, not concurrent** — both agents share the same single logged-in Browser pane instance, so running them at the same time would have them fight over the same browser tab. Sequential dispatch avoids that race entirely.
4. Compare the two `{member: score}` results. If they match exactly (all 14 members, identical scores), proceed. If anything differs, stop and show the user the discrepancy — never guess which one is right or average them.

## Script: `update_week_scores.py`

```
python3 update_week_scores.py <year> <week> <path/to/scores.json>
```

Where `scores.json` is the verified `{member: score}` result from the dual-extraction step above (14 entries for a 14-member season).

Given a verified week's scores, the script:

1. Writes each member's score into `data["seasons"][year]["weeklyPoints"][member][str(week)]`.
2. Computes that week's sidebet payouts: rank all members by that week's score (descending; ties broken by the member's position in the `TEAM_NAME_TO_MEMBER` mapping table for that year — a fixed, deterministic order — matching this codebase's existing "stable sort, first-encountered-wins" tie convention used elsewhere, just pinned to an explicit order instead of incoming-JSON order, which isn't guaranteed stable), then `payout = 75 - (rank * 10)` per `CLAUDE.md`'s documented formula. Writes into `weeklySidebets[member][str(week)]`.
3. Recomputes season-to-date aggregates from **every week entered so far this season** (not just the new one): `standings[member].totalPoints` (sum of `weeklyPoints` entered), `standings[member].pointsRank` (rank by `totalPoints` descending, ties broken the same deterministic way as step 2), `sidebetStandings[member].total` (sum of `weeklySidebets` entered), `sidebetStandings[member].rank` (rank by `total` descending, same tie-break), `sidebetStandings[member].lowManCount` (count of weeks where that member's payout was exactly `-65`, i.e. last place).
4. Leaves `standings[member].yearEndStanding` untouched (`null` until the real season ends and Yahoo's own final standings are known — this script has no way to know that mid-season).
5. Writes the updated data back to `js/data.js`, in the same format `sync_yahoo_data.py`/`calculate_era_adjusted_stats.py` already use (`read_data_js`/`write_data_js` helpers, duplicated locally per this codebase's established per-script convention rather than importing across scripts).

## Testing

Python `unittest` (matching `test_calculate_era_adjusted_stats.py`'s pattern), TDD. Pure functions, each tested in isolation before wiring into the write path:

- `calculate_sidebet_payout(rank)` → `75 - rank * 10`
- `rank_members_by_score(scores)` → `{member: rank}`, stable tie-break by name
- `compute_weekly_sidebets(scores)` → `{member: payout}`, composing the two functions above
- `compute_season_totals(weekly_points_by_member)` → `{member: {"total": ..., "rank": ...}}` from however many weeks have been entered so far
- `compute_low_man_count(weekly_sidebets_for_member)` → count of `-65` entries
- One end-to-end integration test on a small fixture (a handful of members, two weeks of scores) verifying the full script output matches hand-computed expected values

## Rollout

1. Build and test the script.
2. Run the dual-verified extraction for Week 1 (already complete, confirmed live in the Browser pane during this conversation).
3. Spot-check the resulting `js/data.js` diff against the live page before considering it done.
4. Commit and push directly to `main`, per this project's standing convention — after the user reviews the diff, consistent with how every other change this session has gone.

No UI/HTML changes are needed — `index.html` and the other pages already read live from `js/data.js` correctly (built during the earlier Crimson & Gold redesign work), so populating real weekly data is sufficient on its own.
