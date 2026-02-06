#!/usr/bin/env python3
"""
Sync Kalshi market data for the Wagers page.
Fetches NFL markets and saves as JS for frontend display.
"""

import json
from datetime import datetime
from kalshi_api import KalshiAPI, get_nfl_super_bowl_markets, get_nfl_props


def sync_wagers_data():
    """Fetch NFL market data from Kalshi and save as JS file."""
    print("Syncing Kalshi NFL market data...")

    api = KalshiAPI(use_demo=False)

    # Note: Balance is fetched per-user at runtime, not stored in static data

    # Fetch NFL Super Bowl winner markets
    print("  Fetching Super Bowl winner markets...")
    nfl_champ = get_nfl_super_bowl_markets(api)
    nfl_champ_active = [m for m in nfl_champ if m.get('status') == 'active']
    nfl_champ_active.sort(key=lambda m: m.get('volume', 0), reverse=True)
    print(f"    Found {len(nfl_champ_active)} championship markets")

    # Fetch NFL prop markets
    print("  Fetching NFL prop markets...")
    props = get_nfl_props(api)

    for prop_type, markets in props.items():
        if markets:
            print(f"    {prop_type}: {len(markets)} markets")

    # Build data object
    data = {
        'championship': nfl_champ_active,
        'spread': props.get('spread', [])[:10],
        'total': props.get('total', [])[:10],
        'team_total': props.get('team_total', [])[:10],
        'first_td': props.get('first_td', [])[:15],
        'anytime_td': props.get('anytime_td', [])[:15],
        'passing_yards': props.get('passing_yards', [])[:10],
        'rushing_yards': props.get('rushing_yards', [])[:10],
        'receiving_yards': props.get('receiving_yards', [])[:10],
        'updated': datetime.utcnow().isoformat() + 'Z'
    }

    # Write as JS file
    js_content = f"// Kalshi NFL market data - auto-generated\n"
    js_content += f"// Last updated: {data['updated']}\n\n"
    js_content += f"const WAGERS_DATA = {json.dumps(data, indent=2)};\n"

    with open('js/wagers-data.js', 'w') as f:
        f.write(js_content)

    total_markets = sum(len(v) for k, v in data.items() if isinstance(v, list))
    print(f"\nSaved to js/wagers-data.js")
    print(f"  Total markets: {total_markets}")


if __name__ == '__main__':
    sync_wagers_data()
