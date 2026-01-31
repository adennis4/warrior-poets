# Yahoo Fantasy Integration - Resume Point

## Status: Ready to Test

The Yahoo Sports API integration is complete. Next steps:

### To Test
```bash
# Preview what would sync (no changes made)
python3 sync_yahoo_data.py 2024 --dry-run

# Actually sync 2024 data to data.js
python3 sync_yahoo_data.py 2024
```

### Files Created
- `.env` - Yahoo API credentials (Client ID, Secret, League IDs)
- `yahoo_fantasy.py` - OAuth client + data fetching + member name mapping
- `sync_yahoo_data.py` - Syncs Yahoo data → js/data.js
- `requirements.txt` - Python dependencies

### To Add Future Seasons
1. Find the new league ID from Yahoo (it changes each year when renewed)
2. Add to `.env`: `YAHOO_LEAGUE_ID_2025=50810` (already added for 2025)
3. Run: `python3 sync_yahoo_data.py 2025`

### Notes
- OAuth token is cached in `oauth_token.json` (auto-refreshes)
- Manager name → member name mapping is in `yahoo_fantasy.py` (MANAGER_TO_MEMBER dict)
- Game keys (Yahoo's season IDs) are mapped in `yahoo_fantasy.py` (GAME_KEYS dict)
