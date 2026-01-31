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

## Kalshi Prediction Markets API

### Overview

Kalshi is a regulated prediction market where you can trade on the outcomes of real-world events. The API supports both public market data endpoints and authenticated trading endpoints.

### Environment Variables

```bash
KALSHI_USE_DEMO=true|false    # Use demo (default) or production API
KALSHI_API_KEY_ID=<key>       # API key ID for authenticated endpoints
KALSHI_PRIVATE_KEY_PATH=<path> # Path to RSA private key file
```

### Sports Series Tickers

| League | Series | Description |
|--------|--------|-------------|
| NFL    | KXSB   | Super Bowl / Pro Football Championship |
| NBA    | KXNBA  | NBA Finals / Pro Basketball Finals |
| NHL    | KXNHL  | Stanley Cup Finals |
| MLB    | KXMLB  | World Series / Pro Baseball Championship |

### CLI Commands

```bash
# Check exchange status
python3 kalshi_api.py status

# List open markets
python3 kalshi_api.py markets [query]

# Sports championship markets
python3 kalshi_api.py sports [nfl|nba|nhl|mlb]
python3 kalshi_api.py nfl     # Super Bowl markets
python3 kalshi_api.py nba     # NBA Finals markets
python3 kalshi_api.py nhl     # Stanley Cup markets
python3 kalshi_api.py mlb     # World Series markets

# Get orderbook for a market
python3 kalshi_api.py orderbook <ticker>

# Get account balance (requires auth)
python3 kalshi_api.py balance
```

### Market Ticker Format

Championship markets follow the pattern: `KXSB-26-KC`
- `KXSB` = Series (Super Bowl)
- `26` = Season/Year
- `KC` = Team abbreviation

### API Endpoints

**Public (no auth required):**
- `get_exchange_status()` - Exchange status
- `get_markets()` - List markets with filters
- `get_market(ticker)` - Single market details
- `get_market_orderbook(ticker)` - Order book
- `search_markets(query)` - Search by keyword

**Authenticated (requires API key + private key):**
- `get_balance()` - Account balance
- `get_positions()` - Current positions
- `get_orders()` - Active orders
- `create_order()` - Place new order
- `cancel_order()` - Cancel order

### Authentication

Kalshi uses RSA-PSS signatures for authentication:
1. Create API key at kalshi.com (generates key ID + private key)
2. Save private key to file
3. Set `KALSHI_API_KEY_ID` and `KALSHI_PRIVATE_KEY_PATH` env vars

Signature format: `timestamp + method + path` signed with RSA-PSS SHA256
