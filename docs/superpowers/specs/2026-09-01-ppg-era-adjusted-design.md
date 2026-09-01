# PPG and Era-Adjusted PPG

## Context

A league member gave this feedback: raw all-time point totals/averages aren't a fair comparison across the league's history, because both the number of owners (10 in 2009-10, 12 in 2011-15, 14 since 2016) and the number of weeks per season (16 weeks in 2017-2020, 17 weeks every other year) have changed over time. The site's current "Avg/Season" stat (`total career points ÷ seasons played`) doesn't correct for either.

## Formulas

**PPG (Points Per Game)**

```
ppg = total career points ÷ total weeks played
```

Every individual week is weighted equally, regardless of which season it fell in or how many seasons a member played. This directly removes the season-length bias. (Confirmed via `js/data.js`: every member has a consistent week count within a given season — no partial-week gaps to account for.) If a member has `0` total weeks played (shouldn't occur for anyone currently in `allTime.pointsTotals`, since presence there implies at least one season played, but is a real possibility for a future edge case like a member added with no games yet), `ppg` and `eraAdjustedPpg` are both `0` rather than dividing by zero.

**Era-Adjusted PPG**

Answers "how many standard deviations above/below their peers did this person typically score, translated back into points using the league's overall scoring environment as the reference." Computed in steps:

1. For every (year, week) that was played, compute the population mean and population standard deviation of every member's score that week.
2. For each of a member's individual weekly scores, compute `z = (score - week_mean) / week_stdev`. If `week_stdev` is `0` (degenerate case — every score that week was identical), that week's `z` is `0`.
3. A member's **career z-score** is the average of all their per-week `z` values.
4. Compute the **all-time reference mean and stdev**: the population mean and stdev across every individual weekly score ever recorded, league-wide, all members, all years.
5. `eraAdjustedPpg = allTimeMean + (careerZScore × allTimeStdev)`

This produces a number in the same "points per week" units as PPG, so it's directly comparable and doesn't require explaining an abstract z-score.

Population statistics (not sample) are used throughout, since "every week in league history" is the entire population being measured, not a sample of some larger population.

## Scope

**Points only — not Sidebets.** Sidebets are already a zero-sum, rank-based payout system (finish position each week, not raw score), so they're inherently era-neutral already; this fix doesn't apply to them.

**New standalone script**: `calculate_era_adjusted_stats.py` at the repo root, following the existing `sync_*.py` scripts' read/modify/write pattern for `js/data.js`. It:
- Reads `js/data.js`
- Computes `ppg` and `eraAdjustedPpg` for every member in `allTime.pointsTotals`
- Writes those two new fields into each member's entry in `allTime.pointsTotals[name]`, alongside the existing `total`/`rank`/`avg`/`yearly` fields (which are left untouched — nothing removes `avg` from the data, only the UI stops reading it)
- Saves `js/data.js` back out

It is **not** wired into `sync_yahoo_data.py` or any other automated flow. It's run manually, whenever the site owner wants the numbers refreshed — expected to be roughly once a year, after a season wraps.

## UI changes

**`all-time.html`'s All-Time Points table:**
- "Avg/Season" column is replaced by a **PPG** column (reads `data.ppg`), remains the default sort column
- New sortable **Era-Adj PPG** column added (reads `data.eraAdjustedPpg`)
- "Total Points" and "Seasons" columns unchanged

**All 18 `members/*.html` pages:** the existing "Avg Pts" stat card switches from reading `pointsData.avg` to `pointsData.ppg` — same card, same label, just a different underlying number. Era-Adjusted PPG is **not** added to member pages (out of scope — it's a leaderboard-comparison stat, member pages don't need a second career-average number).

## Testing

Python's built-in `unittest` (no new dependency — the project has no existing Python test suite or `pytest` installed, and this is a small enough surface that stdlib is sufficient). Test-driven: write failing tests first, then implement. Coverage:
- `calculate_ppg` — basic case, zero-weeks edge case
- Population mean/stdev helper — basic case, single-value case (stdev = 0)
- `calculate_z_score` — basic case, zero-stdev guard (returns `0`, not a division error)
- `calculate_era_adjusted_ppg` — basic case
- An end-to-end integration check against a small hand-computed fixture (2-3 members, 2-3 weeks) verifying the full pipeline produces the expected numbers

## Rollout

1. Build and test the script against a small fixture.
2. Run it against the real `js/data.js`, spot-check 2-3 members' resulting `ppg`/`eraAdjustedPpg` against hand calculations.
3. Update `all-time.html` and all 18 member pages to read the new fields.
4. Visual QA in-browser: All-Time Points table sorts correctly on both new columns; member pages show the new PPG value in the same "Avg Pts" card.
5. Run `npx jest` to confirm no regression to the existing JS test suite (this feature adds no new JS — everything new is Python — so the existing 91 tests should be unaffected).
6. Per this repo's standing convention: commit and push directly to `main`, no PR — but only once the user has reviewed it, consistent with how prior changes this session have gone.
