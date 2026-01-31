# Warrior Poets Fantasy Football - Project Memory

## Sidebet Calculation Logic

Each week, all 14 members are ranked by their weekly fantasy points (highest to lowest). Payouts are assigned in $10 increments based on rank position. The top 7 earn money, the bottom 7 pay money. It's a zero-sum system (total each week = $0).

### Weekly Payout Structure

| Rank | Sidebet |
|------|---------|
| 1st  | +$65    |
| 2nd  | +$55    |
| 3rd  | +$45    |
| 4th  | +$35    |
| 5th  | +$25    |
| 6th  | +$15    |
| 7th  | +$5     |
| 8th  | -$5     |
| 9th  | -$15    |
| 10th | -$25    |
| 11th | -$35    |
| 12th | -$45    |
| 13th | -$55    |
| 14th | -$65    |

### Calculation Formula

```
payout = 75 - (rank × 10)
```

Examples:
- Rank 1: 75 - 10 = +65
- Rank 7: 75 - 70 = +5
- Rank 8: 75 - 80 = -5
- Rank 14: 75 - 140 = -65

### Additional Notes

- "Low Man Count" tracks how many times someone has finished in last place (14th)
- Cumulative sidebet totals are the sum of all weekly sidebets for the season

## Testing

Run tests with:
```bash
npm test
```

Test coverage:
```bash
npm run test:coverage
```

## Yahoo API Integration

### Manager to Member Name Mapping

| Yahoo Nickname    | Data.js Name |
|-------------------|--------------|
| Ryan              | Pinkston     |
| Cliff             | CP           |
| Joe Rizzo         | Rizzo        |
| Josh              | Farber       |
| Bradley           | Dues         |
| Jett Miller       | Jett         |
| Rick              | Rick         |
| Jonathan          | Lloyd        |
| Eric              | Stern        |
| Justin Bagdzius   | JB           |
| Michael Y         | Yonk         |
| Ben               | Ben          |
| Richard           | Rich         |
| Andrew            | Andrew       |

### Game Keys (NFL Season to Yahoo ID)

- 2026: 461 (projected)
- 2025: 461
- 2024: 449
- 2023: 423

### API Commands

```bash
# Fetch weekly points (default)
python3 yahoo_fantasy.py 2024
python3 yahoo_fantasy.py points 2024

# Fetch team rosters
python3 yahoo_fantasy.py rosters 2024        # Current rosters
python3 yahoo_fantasy.py rosters 2024 5      # Week 5 rosters
```

### Roster Data Structure

Each player in a roster includes:
- `player_key`, `player_id` - Yahoo identifiers
- `name` - Full player name
- `team`, `team_abbr` - NFL team
- `position` - Primary position (QB, RB, WR, etc.)
- `eligible_positions` - All positions player can fill
- `selected_position` - Where slotted in lineup
- `is_starting` - True if in starting lineup (not BN/IR)
- `headshot_url` - Player photo URL
- `injury_status` - Injury designation if any
- `bye_week` - Player's bye week
- `stats` - Season stats (keyed by Yahoo stat_id)
