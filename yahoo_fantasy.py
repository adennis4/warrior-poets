#!/usr/bin/env python3
"""
Yahoo Fantasy Sports API client for Warrior Poets league.
Handles OAuth authentication and fetches league data.
"""

import os
import json
import base64
import webbrowser
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("YAHOO_CLIENT_ID")
CLIENT_SECRET = os.getenv("YAHOO_CLIENT_SECRET")

TOKEN_FILE = Path(__file__).parent / "oauth_token.json"
# Try setting YAHOO_REDIRECT_URI in .env if the default doesn't work
REDIRECT_URI = os.getenv("YAHOO_REDIRECT_URI", "oob")

# Game keys map NFL season year to Yahoo game ID
GAME_KEYS = {
    "2025": "461", "2024": "449", "2023": "423", "2022": "414",
    "2021": "406", "2020": "399", "2019": "390", "2018": "380",
    "2017": "371", "2016": "359", "2015": "348", "2014": "331",
    "2013": "314", "2012": "273", "2011": "242", "2010": "223",
    "2009": "199"
}

# League IDs change each season when renewed - map season to league ID
LEAGUE_IDS = {
    "2025": os.getenv("YAHOO_LEAGUE_ID_2025", "50810"),
    "2024": os.getenv("YAHOO_LEAGUE_ID_2024", "95890"),
    # Add older seasons as needed
}

# Yahoo Fantasy NFL Stat ID to readable name mapping
STAT_ID_MAP = {
    "1": "GP",              # Games Played
    "2": "Pass Completions",
    "3": "Pass Incompletions",
    "4": "Pass Yds",
    "5": "Pass TD",
    "6": "INT",
    "7": "Sacks",
    "8": "Rush Att",
    "9": "Rush Yds",
    "10": "Rush TD",
    "11": "Rec",
    "12": "Rec Yds",
    "13": "Rec TD",
    "14": "Return Yds",
    "15": "Return TD",
    "16": "2PT",
    "17": "Fum",
    "18": "Fum Lost",
    "19": "FG 0-19",
    "20": "FG 20-29",
    "21": "FG 30-39",
    "22": "FG 40-49",
    "23": "FG 50+",
    "24": "FG Missed 0-19",
    "25": "FG Missed 20-29",
    "26": "FG Missed 30-39",
    "27": "FG Missed 40-49",
    "28": "FG Missed 50+",
    "29": "PAT Made",
    "30": "PAT Missed",
    "31": "Pts Allowed 0",
    "32": "Pts Allowed 1-6",
    "33": "Pts Allowed 7-13",
    "34": "Pts Allowed 14-20",
    "35": "Pts Allowed 21-27",
    "36": "Pts Allowed 28-34",
    "37": "Pts Allowed 35+",
    "38": "DEF Sack",
    "39": "DEF INT",
    "40": "DEF Fum Rec",
    "41": "DEF TD",
    "42": "DEF Safety",
    "43": "DEF Blk Kick",
    "44": "DEF Ret TD",
    "45": "Tackle Solo",
    "46": "Tackle Assist",
    "47": "Tackle for Loss",
    "48": "Pass Defended",
    "49": "DEF Sacks",
    "50": "DEF INT",
    "51": "DEF Fum Forced",
    "52": "DEF Fum Rec",
    "53": "DEF TD",
    "54": "DEF Safety",
    "55": "DEF Pts Allowed",
    "56": "DEF Yds Allowed",
    "57": "Off Fum Rec TD",
    "58": "Pass Attempts",
    "59": "Pass 300-399 Yds Bonus",
    "60": "Pass 400+ Yds Bonus",
    "61": "Rush 100-199 Yds Bonus",
    "62": "Rush 200+ Yds Bonus",
    "63": "Rec 100-199 Yds Bonus",
    "64": "Rec 200+ Yds Bonus",
    "72": "Pick Six Thrown",
    "73": "40+ Yd Pass TD Bonus",
    "74": "40+ Yd Rush TD Bonus",
    "75": "40+ Yd Rec TD Bonus",
    "77": "50+ Yd Rush TD Bonus",
    "78": "Targets",
}

# Map Yahoo manager nicknames to data.js member names
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
    "Andrew": "Andrew",
}

API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"


class YahooFantasyAPI:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.token_expiry = None
        self._load_tokens()

    def _get_auth_header(self):
        """Get Basic auth header for token requests."""
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _load_tokens(self):
        """Load tokens from file if they exist."""
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE) as f:
                data = json.load(f)
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                expiry = data.get("token_expiry")
                if expiry:
                    self.token_expiry = datetime.fromisoformat(expiry)

    def _save_tokens(self):
        """Save tokens to file."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expiry": self.token_expiry.isoformat() if self.token_expiry else None
        }
        with open(TOKEN_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def _is_token_valid(self):
        """Check if current access token is valid."""
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry - timedelta(minutes=5)

    def authenticate(self):
        """Run OAuth flow to get access token."""
        if self._is_token_valid():
            print("Using existing valid token.")
            return True

        if self.refresh_token:
            print("Refreshing access token...")
            if self._refresh_access_token():
                return True
            print("Refresh failed, starting new auth flow...")

        return self._run_auth_flow()

    def _run_auth_flow(self):
        """Run the full OAuth authorization flow."""
        auth_url = (
            f"https://api.login.yahoo.com/oauth2/request_auth"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
            f"&response_type=code"
        )

        print(f"\nUsing redirect URI: {REDIRECT_URI}")
        print(f"\nOpening browser for Yahoo authorization...")
        print(f"If browser doesn't open, visit:\n{auth_url}\n")
        webbrowser.open(auth_url)

        print("\nAfter authorizing, you'll be redirected.")
        print("Copy the FULL URL from your browser's address bar (it will show an error page, that's ok).")
        print("Or if Yahoo shows a code directly, paste that.\n")
        response = input("Paste the URL or code here: ").strip()

        # Extract code from URL if they pasted a full URL
        if "code=" in response:
            parsed = urllib.parse.urlparse(response)
            params = urllib.parse.parse_qs(parsed.query)
            auth_code = params.get("code", [None])[0]
        else:
            auth_code = response

        if not auth_code:
            print("No authorization code found.")
            return False

        return self._exchange_code(auth_code)

    def _exchange_code(self, code):
        """Exchange authorization code for access token."""
        response = requests.post(
            "https://api.login.yahoo.com/oauth2/get_token",
            headers={
                "Authorization": self._get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI
            }
        )

        if response.status_code != 200:
            print(f"Token exchange failed: {response.text}")
            return False

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
        self._save_tokens()
        print("Authorization successful!")
        return True

    def _refresh_access_token(self):
        """Refresh the access token using refresh token."""
        response = requests.post(
            "https://api.login.yahoo.com/oauth2/get_token",
            headers={
                "Authorization": self._get_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
        )

        if response.status_code != 200:
            print(f"Token refresh failed: {response.text}")
            return False

        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"])
        self._save_tokens()
        print("Token refreshed successfully!")
        return True

    def _api_request(self, endpoint):
        """Make an authenticated API request."""
        if not self._is_token_valid():
            if not self.authenticate():
                raise Exception("Failed to authenticate")

        url = f"{API_BASE}{endpoint}"
        if "?" in url:
            url += "&format=json"
        else:
            url += "?format=json"

        response = requests.get(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )

        if response.status_code == 401:
            # Token might have expired, try refresh
            if self._refresh_access_token():
                response = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )

        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        return response.json()

    def get_league_key(self, year):
        """Get the league key for a specific year."""
        game_key = GAME_KEYS.get(str(year))
        if not game_key:
            raise ValueError(f"No game key found for year {year}")
        league_id = LEAGUE_IDS.get(str(year))
        if not league_id:
            raise ValueError(f"No league ID found for year {year}. Add YAHOO_LEAGUE_ID_{year} to .env")
        return f"{game_key}.l.{league_id}"

    def get_league_info(self, year):
        """Get basic league information."""
        league_key = self.get_league_key(year)
        return self._api_request(f"/league/{league_key}")

    def get_standings(self, year):
        """Get league standings for a year."""
        league_key = self.get_league_key(year)
        return self._api_request(f"/league/{league_key}/standings")

    def get_scoreboard(self, year, week=None):
        """Get scoreboard (matchups) for a year, optionally for a specific week."""
        league_key = self.get_league_key(year)
        endpoint = f"/league/{league_key}/scoreboard"
        if week:
            endpoint += f";week={week}"
        return self._api_request(endpoint)

    def get_teams(self, year):
        """Get all teams in the league for a year."""
        league_key = self.get_league_key(year)
        return self._api_request(f"/league/{league_key}/teams")

    def get_all_matchups(self, year, num_weeks=17):
        """Get all matchups for all weeks in a season."""
        league_key = self.get_league_key(year)
        all_matchups = {}
        for week in range(1, num_weeks + 1):
            print(f"  Fetching week {week}...")
            try:
                data = self._api_request(f"/league/{league_key}/scoreboard;week={week}")
                all_matchups[week] = data
            except Exception as e:
                print(f"  Warning: Could not fetch week {week}: {e}")
                break
        return all_matchups

    def get_team_roster(self, team_key, week=None):
        """
        Get a team's roster with player details and stats.

        Args:
            team_key: The Yahoo team key (e.g., "449.l.95890.t.1")
            week: Optional week number. If None, gets current roster.

        Returns:
            Roster data including players, positions, and stats.
        """
        endpoint = f"/team/{team_key}/roster/players"
        if week:
            endpoint = f"/team/{team_key}/roster;week={week}/players"
        # Request player stats subresource
        endpoint += ";out=stats"
        return self._api_request(endpoint)

    def get_all_team_rosters(self, year, week=None):
        """
        Get rosters for all teams in the league.

        Args:
            year: Season year
            week: Optional week number

        Returns:
            Dict mapping team_key to roster data
        """
        # First get all teams
        teams_data = self.get_teams(year)
        team_keys = []

        fantasy_content = teams_data.get("fantasy_content", {})
        league = fantasy_content.get("league", [])

        for item in league:
            if isinstance(item, dict) and "teams" in item:
                teams = item["teams"]
                for key, team_data in teams.items():
                    if key == "count":
                        continue
                    if isinstance(team_data, dict) and "team" in team_data:
                        team_info = team_data["team"]
                        for part in team_info:
                            if isinstance(part, list):
                                for item in part:
                                    if isinstance(item, dict) and "team_key" in item:
                                        team_keys.append(item["team_key"])

        # Fetch roster for each team
        rosters = {}
        for team_key in team_keys:
            print(f"  Fetching roster for {team_key}...")
            try:
                rosters[team_key] = self.get_team_roster(team_key, week)
            except Exception as e:
                print(f"  Warning: Could not fetch roster for {team_key}: {e}")

        return rosters


def extract_weekly_points(api, year):
    """Extract weekly points for all teams in a season."""
    print(f"Fetching data for {year}...")

    # Get teams to map team_key to manager name
    teams_data = api.get_teams(year)
    team_map = {}

    fantasy_content = teams_data.get("fantasy_content", {})
    league = fantasy_content.get("league", [])

    # Navigate the nested structure to find teams
    for item in league:
        if isinstance(item, dict) and "teams" in item:
            teams = item["teams"]
            for key, team_data in teams.items():
                if key == "count":
                    continue
                if isinstance(team_data, dict) and "team" in team_data:
                    team_info = team_data["team"]
                    team_key = None
                    manager_name = None

                    for part in team_info:
                        if isinstance(part, list):
                            for item in part:
                                if isinstance(item, dict):
                                    if "team_key" in item:
                                        team_key = item["team_key"]
                                    if "managers" in item:
                                        managers = item["managers"]
                                        for mgr in managers:
                                            if isinstance(mgr, dict) and "manager" in mgr:
                                                manager_name = mgr["manager"].get("nickname")
                                                break

                    if team_key and manager_name:
                        # Map Yahoo nickname to data.js member name
                        member_name = MANAGER_TO_MEMBER.get(manager_name, manager_name)
                        team_map[team_key] = member_name

    print(f"  Found {len(team_map)} teams")

    # Get weekly scores
    weekly_points = {name: {} for name in team_map.values()}
    matchups = api.get_all_matchups(year)

    for week, data in matchups.items():
        fantasy_content = data.get("fantasy_content", {})
        league = fantasy_content.get("league", [])

        for item in league:
            if isinstance(item, dict) and "scoreboard" in item:
                scoreboard = item["scoreboard"]
                matchups_data = scoreboard.get("0", {}).get("matchups", {})

                for key, matchup_data in matchups_data.items():
                    if key == "count":
                        continue
                    if isinstance(matchup_data, dict) and "matchup" in matchup_data:
                        matchup = matchup_data["matchup"]
                        teams = matchup.get("0", {}).get("teams", {})

                        for tkey, team_data in teams.items():
                            if tkey == "count":
                                continue
                            if isinstance(team_data, dict) and "team" in team_data:
                                team_info = team_data["team"]
                                team_key = None
                                points = None

                                for part in team_info:
                                    if isinstance(part, list):
                                        for item in part:
                                            if isinstance(item, dict) and "team_key" in item:
                                                team_key = item["team_key"]
                                    if isinstance(part, dict) and "team_points" in part:
                                        points = float(part["team_points"].get("total", 0))

                                if team_key and points is not None:
                                    manager = team_map.get(team_key)
                                    if manager:
                                        weekly_points[manager][str(week)] = points

    return weekly_points, team_map


def extract_roster_data(roster_response, team_map=None):
    """
    Extract player data from a roster API response.

    Args:
        roster_response: Raw API response from get_team_roster()
        team_map: Optional dict mapping team_key to manager name

    Returns:
        Dict with roster information including players and their stats
    """
    players = []
    team_key = None
    manager_name = None

    fantasy_content = roster_response.get("fantasy_content", {})
    team = fantasy_content.get("team", [])

    # Extract team info
    for part in team:
        if isinstance(part, list):
            for item in part:
                if isinstance(item, dict):
                    if "team_key" in item:
                        team_key = item["team_key"]
                    if "name" in item:
                        team_name = item["name"]
                    if "managers" in item:
                        for mgr in item["managers"]:
                            if isinstance(mgr, dict) and "manager" in mgr:
                                manager_name = mgr["manager"].get("nickname")
                                break

    # Map to member name if team_map provided
    if team_map and team_key:
        manager_name = team_map.get(team_key, manager_name)
    elif manager_name:
        manager_name = MANAGER_TO_MEMBER.get(manager_name, manager_name)

    # Extract roster/players
    for part in team:
        if isinstance(part, dict) and "roster" in part:
            roster = part["roster"]
            coverage_type = roster.get("coverage_type")

            players_data = roster.get("0", {}).get("players", {})
            for key, player_data in players_data.items():
                if key == "count":
                    continue
                if isinstance(player_data, dict) and "player" in player_data:
                    player_info = player_data["player"]
                    player = extract_player_info(player_info)
                    if player:
                        players.append(player)

    return {
        "team_key": team_key,
        "manager": manager_name,
        "players": players
    }


def extract_player_info(player_info):
    """
    Extract individual player information from API response.

    Args:
        player_info: Player data from API

    Returns:
        Dict with player details
    """
    player = {
        "player_key": None,
        "player_id": None,
        "name": None,
        "team": None,
        "team_abbr": None,
        "position": None,
        "eligible_positions": [],
        "selected_position": None,
        "is_starting": False,
        "headshot_url": None,
        "injury_status": None,
        "bye_week": None,
        "stats": {}
    }

    # Bench positions that indicate non-starter
    BENCH_POSITIONS = ["BN", "IR", "IR+"]

    for part in player_info:
        # Check nested list of player attributes
        if isinstance(part, list):
            for item in part:
                if isinstance(item, dict):
                    if "player_key" in item:
                        player["player_key"] = item["player_key"]
                    if "player_id" in item:
                        player["player_id"] = item["player_id"]
                    if "name" in item:
                        player["name"] = item["name"].get("full")
                    if "editorial_team_full_name" in item:
                        player["team"] = item["editorial_team_full_name"]
                    if "editorial_team_abbr" in item:
                        player["team_abbr"] = item["editorial_team_abbr"]
                    if "display_position" in item:
                        player["position"] = item["display_position"]
                    if "eligible_positions" in item:
                        positions = item["eligible_positions"]
                        if isinstance(positions, list):
                            player["eligible_positions"] = [
                                p.get("position") for p in positions
                                if isinstance(p, dict) and "position" in p
                            ]
                    if "headshot" in item:
                        headshot = item["headshot"]
                        if isinstance(headshot, dict):
                            player["headshot_url"] = headshot.get("url")
                    # Injury status can be in 'status' or 'injury_status' field
                    if "status" in item:
                        player["injury_status"] = item["status"]
                    if "injury_status" in item:
                        player["injury_status"] = item["injury_status"]
                    if "bye_weeks" in item:
                        bye = item["bye_weeks"]
                        if isinstance(bye, dict):
                            player["bye_week"] = bye.get("week")

        # Check for selected_position at top level of player_info (not nested in list)
        elif isinstance(part, dict):
            if "selected_position" in part:
                sel_pos = part["selected_position"]
                if isinstance(sel_pos, list):
                    for sp in sel_pos:
                        if isinstance(sp, dict) and "position" in sp:
                            player["selected_position"] = sp["position"]
                            player["is_starting"] = sp["position"] not in BENCH_POSITIONS
                            break

            # Player stats
            if "player_stats" in part:
                stats_data = part["player_stats"]
                coverage = stats_data.get("coverage_type")
                season = stats_data.get("season")

                stats_list = stats_data.get("stats", [])
                for stat in stats_list:
                    if isinstance(stat, dict) and "stat" in stat:
                        stat_info = stat["stat"]
                        stat_id = stat_info.get("stat_id")
                        stat_value = stat_info.get("value")
                        if stat_id and stat_value is not None:
                            player["stats"][stat_id] = stat_value

    # Decode stats to readable names
    if player["stats"]:
        player["stats_decoded"] = decode_stats(player["stats"])

    return player if player["name"] else None


def decode_stats(raw_stats):
    """
    Convert Yahoo stat IDs to readable stat names.

    Args:
        raw_stats: Dict of stat_id -> value

    Returns:
        Dict of readable_stat_name -> value (only non-zero stats)
    """
    decoded = {}
    for stat_id, value in raw_stats.items():
        stat_name = STAT_ID_MAP.get(str(stat_id), f"Stat_{stat_id}")
        # Convert value to number if possible
        try:
            num_value = float(value) if '.' in str(value) else int(value)
        except (ValueError, TypeError):
            num_value = value
        # Only include non-zero stats
        if num_value != 0:
            decoded[stat_name] = num_value
    return decoded


def get_league_rosters(api, year, week=None):
    """
    Get all team rosters for a league with parsed player data.

    Args:
        api: YahooFantasyAPI instance
        year: Season year
        week: Optional week number

    Returns:
        Dict mapping manager name to roster data
    """
    print(f"Fetching rosters for {year}" + (f" week {week}" if week else "") + "...")

    # Get team map first
    teams_data = api.get_teams(year)
    team_map = {}

    fantasy_content = teams_data.get("fantasy_content", {})
    league = fantasy_content.get("league", [])

    for item in league:
        if isinstance(item, dict) and "teams" in item:
            teams = item["teams"]
            for key, team_data in teams.items():
                if key == "count":
                    continue
                if isinstance(team_data, dict) and "team" in team_data:
                    team_info = team_data["team"]
                    team_key = None
                    manager_name = None

                    for part in team_info:
                        if isinstance(part, list):
                            for item in part:
                                if isinstance(item, dict):
                                    if "team_key" in item:
                                        team_key = item["team_key"]
                                    if "managers" in item:
                                        for mgr in item["managers"]:
                                            if isinstance(mgr, dict) and "manager" in mgr:
                                                manager_name = mgr["manager"].get("nickname")
                                                break

                    if team_key and manager_name:
                        member_name = MANAGER_TO_MEMBER.get(manager_name, manager_name)
                        team_map[team_key] = member_name

    # Get all rosters
    raw_rosters = api.get_all_team_rosters(year, week)

    # Parse roster data
    rosters = {}
    for team_key, roster_data in raw_rosters.items():
        parsed = extract_roster_data(roster_data, team_map)
        manager = parsed.get("manager") or team_map.get(team_key)
        if manager:
            rosters[manager] = parsed

    return rosters


def print_player_line(player):
    """Print a formatted player line with stats."""
    pos = player["selected_position"] or player["position"]
    injury = f" ({player['injury_status']})" if player.get("injury_status") else ""

    # Build stats string from decoded stats
    stats_str = ""
    if player.get("stats_decoded"):
        stats = player["stats_decoded"]
        # Prioritize key stats based on position
        key_stats = []
        pos_type = player["position"]

        if pos_type == "QB":
            for stat in ["Pass Yds", "Pass TD", "INT", "Rush Yds", "Rush TD"]:
                if stat in stats:
                    key_stats.append(f"{stats[stat]} {stat}")
        elif pos_type == "RB":
            for stat in ["Rush Yds", "Rush TD", "Rec", "Rec Yds", "Rec TD"]:
                if stat in stats:
                    key_stats.append(f"{stats[stat]} {stat}")
        elif pos_type in ["WR", "TE"]:
            for stat in ["Rec", "Rec Yds", "Rec TD", "Targets"]:
                if stat in stats:
                    key_stats.append(f"{stats[stat]} {stat}")
        elif pos_type == "K":
            for stat in ["FG 0-19", "FG 20-29", "FG 30-39", "FG 40-49", "FG 50+", "PAT Made"]:
                if stat in stats:
                    key_stats.append(f"{stats[stat]} {stat}")
        elif pos_type == "DEF":
            for stat in ["DEF Sack", "DEF INT", "DEF TD", "DEF Fum Rec"]:
                if stat in stats:
                    key_stats.append(f"{stats[stat]} {stat}")

        if key_stats:
            stats_str = " | " + ", ".join(key_stats[:5])  # Limit to 5 stats

    print(f"  {pos:4} {player['name']:25} {player['team_abbr'] or '':4}{injury}{stats_str}")


def main():
    """Main entry point."""
    import sys

    api = YahooFantasyAPI()

    if not api.authenticate():
        print("Authentication failed!")
        return

    # Parse command line arguments
    # Usage: python yahoo_fantasy.py [command] [year] [week]
    # Commands: points (default), rosters
    args = sys.argv[1:]

    command = "points"
    year = "2024"
    week = None

    if args:
        if args[0] in ["points", "rosters"]:
            command = args[0]
            if len(args) > 1:
                year = args[1]
            if len(args) > 2:
                week = int(args[2])
        else:
            year = args[0]
            if len(args) > 1:
                week = int(args[1])

    print(f"\n--- {command.title()} for {year}" + (f" Week {week}" if week else "") + " ---\n")

    try:
        if command == "rosters":
            rosters = get_league_rosters(api, year, week)

            print(f"\n--- Rosters for {year}" + (f" Week {week}" if week else "") + " ---\n")

            for manager, roster in rosters.items():
                print(f"\n{manager}'s Roster:")
                print("=" * 70)

                starters = [p for p in roster["players"] if p["is_starting"]]
                bench = [p for p in roster["players"] if not p["is_starting"]]

                if starters:
                    print("\nSTARTERS:")
                    for p in starters:
                        print_player_line(p)

                print("\nROSTER:" if not starters else "\nBENCH:")
                for p in bench:
                    print_player_line(p)

            # Also output as JSON for programmatic use
            print("\n\n--- JSON Output ---\n")
            print(json.dumps(rosters, indent=2))

        else:
            weekly_points, team_map = extract_weekly_points(api, year)

            print(f"\n--- Weekly Points for {year} ---\n")
            print(json.dumps(weekly_points, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
