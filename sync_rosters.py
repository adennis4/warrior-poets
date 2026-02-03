#!/usr/bin/env python3
"""
Sync fantasy team rosters for the Wagers page.
Fetches current rosters from Yahoo and saves as JS for frontend display.
"""

import json
from datetime import datetime
from yahoo_fantasy import YahooFantasyAPI

# Manager nickname to display name mapping
MANAGER_TO_MEMBER = {
    "Ryan": "Pinkston",
    "Cliff": "CP",
    "Joe Rizzo": "Rizzo",
    "Josh": "Farber",
    "Bradley": "Dues",
    "Jett Miller": "Jett",
    "Rick": "Rick",
    "Jonathan": "Lloyd",
    "Eric": "Stern",
    "Justin Bagdzius": "JB",
    "Michael Y": "Yonk",
    "Ben": "Ben",
    "Richard": "Rich",
    "Andrew": "Andrew"
}


def extract_player_name(player_data):
    """Extract player name from Yahoo roster data structure."""
    if not isinstance(player_data, dict) or "player" not in player_data:
        return None

    player = player_data["player"]
    if not isinstance(player, list) or len(player) < 1:
        return None

    # First element contains player info
    player_info = player[0]
    if not isinstance(player_info, list):
        return None

    for item in player_info:
        if isinstance(item, dict) and "name" in item:
            name_data = item["name"]
            if isinstance(name_data, dict):
                return name_data.get("full")

    return None


def extract_manager_name(team_data):
    """Extract manager nickname from team data."""
    if not isinstance(team_data, dict) or "team" not in team_data:
        return None

    team = team_data["team"]
    if not isinstance(team, list) or len(team) < 1:
        return None

    team_info = team[0]
    if not isinstance(team_info, list):
        return None

    for item in team_info:
        if isinstance(item, dict) and "managers" in item:
            managers = item["managers"]
            if isinstance(managers, list) and len(managers) > 0:
                manager = managers[0].get("manager", {})
                return manager.get("nickname")

    return None


def sync_rosters():
    """Fetch rosters from Yahoo and save as JS file."""
    print("Syncing fantasy team rosters...")

    api = YahooFantasyAPI()
    year = 2025  # Current NFL season (Super Bowl in Feb 2026)

    # Get all teams
    print("  Fetching teams...")
    teams_data = api.get_teams(year)

    # Build team_key to manager mapping
    team_managers = {}
    fantasy_content = teams_data.get("fantasy_content", {})
    league = fantasy_content.get("league", [])

    for item in league:
        if isinstance(item, dict) and "teams" in item:
            teams = item["teams"]
            for key, team_data in teams.items():
                if key == "count":
                    continue
                if isinstance(team_data, dict):
                    manager_nick = extract_manager_name(team_data)
                    team_info = team_data.get("team", [[]])[0]
                    team_key = None
                    for part in team_info:
                        if isinstance(part, dict) and "team_key" in part:
                            team_key = part["team_key"]
                            break
                    if team_key and manager_nick:
                        team_managers[team_key] = manager_nick

    print(f"  Found {len(team_managers)} teams")

    # Fetch rosters for each team
    manager_players = {}

    for team_key, manager_nick in team_managers.items():
        member_name = MANAGER_TO_MEMBER.get(manager_nick, manager_nick)
        print(f"  Fetching roster for {member_name} ({team_key})...")

        try:
            roster_data = api.get_team_roster(team_key)
            players = []

            # Extract players from roster
            fc = roster_data.get("fantasy_content", {})
            team = fc.get("team", [])

            for item in team:
                if isinstance(item, dict) and "roster" in item:
                    roster = item["roster"]
                    roster_players = roster.get("0", {}).get("players", {})

                    for pk, pv in roster_players.items():
                        if pk == "count":
                            continue
                        player_name = extract_player_name(pv)
                        if player_name:
                            players.append(player_name)

            if players:
                manager_players[member_name] = players
                print(f"    Found {len(players)} players")

        except Exception as e:
            print(f"    Error: {e}")

    # Write as JS file
    data = {
        'rosters': manager_players,
        'updated': datetime.utcnow().isoformat() + 'Z'
    }

    js_content = "// Fantasy team rosters - auto-generated\n"
    js_content += f"// Last updated: {data['updated']}\n\n"
    js_content += f"const ROSTER_DATA = {json.dumps(data, indent=2)};\n"

    with open('js/roster-data.js', 'w') as f:
        f.write(js_content)

    total_players = sum(len(p) for p in manager_players.values())
    print(f"\nSaved to js/roster-data.js")
    print(f"  Total managers: {len(manager_players)}")
    print(f"  Total players: {total_players}")


if __name__ == '__main__':
    sync_rosters()
