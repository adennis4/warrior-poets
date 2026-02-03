#!/usr/bin/env python3
"""
Kalshi Prediction Markets API client.
Supports both public market data and authenticated trading endpoints.

Documentation: https://docs.kalshi.com
"""

import os
import json
import base64
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

import requests
from dotenv import load_dotenv

# Optional: for authenticated requests
try:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import padding
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

load_dotenv()

# API Base URLs
PROD_BASE_URL = "https://api.elections.kalshi.com"
DEMO_BASE_URL = "https://demo-api.kalshi.co"

# API configuration from environment
KALSHI_API_KEY_ID = os.getenv("KALSHI_API_KEY_ID")
KALSHI_PRIVATE_KEY_PATH = os.getenv("KALSHI_PRIVATE_KEY_PATH")
KALSHI_USE_DEMO = os.getenv("KALSHI_USE_DEMO", "true").lower() == "true"


class KalshiAPI:
    """
    Kalshi Prediction Markets API client.

    Public endpoints (market data) don't require authentication.
    Trading endpoints require API key + private key for RSA signature.
    """

    def __init__(self, use_demo: bool = None, api_key_id: str = None, private_key_path: str = None):
        """
        Initialize Kalshi API client.

        Args:
            use_demo: Use demo environment (default: True, reads from KALSHI_USE_DEMO env)
            api_key_id: API key ID (reads from KALSHI_API_KEY_ID env if not provided)
            private_key_path: Path to private key file (reads from KALSHI_PRIVATE_KEY_PATH env)
        """
        self.use_demo = use_demo if use_demo is not None else KALSHI_USE_DEMO
        self.base_url = DEMO_BASE_URL if self.use_demo else PROD_BASE_URL
        self.api_key_id = api_key_id or KALSHI_API_KEY_ID
        self.private_key_path = private_key_path or KALSHI_PRIVATE_KEY_PATH
        self.private_key = None

        if self.private_key_path and HAS_CRYPTO:
            self._load_private_key()

    def _load_private_key(self):
        """Load RSA private key from file."""
        key_path = Path(self.private_key_path)
        if key_path.exists():
            with open(key_path, "rb") as f:
                self.private_key = serialization.load_pem_private_key(
                    f.read(), password=None, backend=default_backend()
                )
            print(f"Loaded private key from {self.private_key_path}")
        else:
            print(f"Warning: Private key file not found: {self.private_key_path}")

    def _create_signature(self, timestamp: str, method: str, path: str) -> str:
        """
        Create RSA-PSS signature for authenticated requests.

        Args:
            timestamp: Current timestamp in milliseconds
            method: HTTP method (GET, POST, etc.)
            path: API path (without query parameters)

        Returns:
            Base64-encoded signature
        """
        if not self.private_key:
            raise Exception("Private key not loaded. Cannot create signature.")

        # Strip query parameters from path
        path_clean = path.split('?')[0]
        message = f"{timestamp}{method}{path_clean}".encode('utf-8')

        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.DIGEST_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')

    def _get_auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """Get authentication headers for a request."""
        if not self.api_key_id or not self.private_key:
            raise Exception("API key ID and private key required for authenticated requests")

        timestamp = str(int(datetime.datetime.now().timestamp() * 1000))
        signature = self._create_signature(timestamp, method, path)

        return {
            'KALSHI-ACCESS-KEY': self.api_key_id,
            'KALSHI-ACCESS-SIGNATURE': signature,
            'KALSHI-ACCESS-TIMESTAMP': timestamp
        }

    def _request(self, method: str, path: str, authenticated: bool = False,
                 params: Dict = None, data: Dict = None) -> Dict:
        """
        Make an API request.

        Args:
            method: HTTP method
            path: API path (e.g., /trade-api/v2/markets)
            authenticated: Whether to include auth headers
            params: Query parameters
            data: Request body for POST/PUT

        Returns:
            JSON response
        """
        url = f"{self.base_url}{path}"
        headers = {'Content-Type': 'application/json'}

        if authenticated:
            headers.update(self._get_auth_headers(method, path))

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data
        )

        if response.status_code not in [200, 201]:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        return response.json()

    # ==================== Public Endpoints (No Auth Required) ====================

    def get_exchange_status(self) -> Dict:
        """Get exchange status and trading hours."""
        return self._request("GET", "/trade-api/v2/exchange/status")

    def get_markets(self,
                    series_ticker: str = None,
                    event_ticker: str = None,
                    status: str = None,
                    cursor: str = None,
                    limit: int = 100) -> Dict:
        """
        Get markets with optional filters.

        Args:
            series_ticker: Filter by series (e.g., "KXNFL" for NFL)
            event_ticker: Filter by event
            status: Filter by status (open, closed, settled)
            cursor: Pagination cursor
            limit: Max results per page

        Returns:
            Dict with 'markets' list and 'cursor' for pagination
        """
        params = {'limit': limit}
        if series_ticker:
            params['series_ticker'] = series_ticker
        if event_ticker:
            params['event_ticker'] = event_ticker
        if status:
            params['status'] = status
        if cursor:
            params['cursor'] = cursor

        return self._request("GET", "/trade-api/v2/markets", params=params)

    def get_market(self, ticker: str) -> Dict:
        """Get details for a specific market."""
        return self._request("GET", f"/trade-api/v2/markets/{ticker}")

    def get_market_orderbook(self, ticker: str, depth: int = 10) -> Dict:
        """
        Get orderbook for a market.

        Note: Kalshi only returns bids (not asks) because of the reciprocal
        relationship between YES and NO positions.
        """
        params = {'depth': depth}
        return self._request("GET", f"/trade-api/v2/markets/{ticker}/orderbook", params=params)

    def get_market_trades(self, ticker: str, cursor: str = None, limit: int = 100) -> Dict:
        """Get recent trades for a market."""
        params = {'limit': limit}
        if cursor:
            params['cursor'] = cursor
        return self._request("GET", f"/trade-api/v2/markets/{ticker}/trades", params=params)

    def get_market_candlesticks(self, ticker: str,
                                 series_ticker: str,
                                 period_interval: int = 60) -> Dict:
        """
        Get candlestick data for a market.

        Args:
            ticker: Market ticker
            series_ticker: Series ticker
            period_interval: Interval in minutes (1, 5, 15, 60, etc.)
        """
        params = {
            'series_ticker': series_ticker,
            'period_interval': period_interval
        }
        return self._request("GET", f"/trade-api/v2/markets/{ticker}/candlesticks", params=params)

    def get_series(self, ticker: str) -> Dict:
        """Get details for a series."""
        return self._request("GET", f"/trade-api/v2/series/{ticker}")

    def get_event(self, ticker: str) -> Dict:
        """Get details for an event."""
        return self._request("GET", f"/trade-api/v2/events/{ticker}")

    def get_events(self,
                   series_ticker: str = None,
                   status: str = None,
                   cursor: str = None,
                   limit: int = 100) -> Dict:
        """Get events with optional filters."""
        params = {'limit': limit}
        if series_ticker:
            params['series_ticker'] = series_ticker
        if status:
            params['status'] = status
        if cursor:
            params['cursor'] = cursor
        return self._request("GET", "/trade-api/v2/events", params=params)

    def search_markets(self, query: str, limit: int = 20) -> Dict:
        """Search for markets by keyword."""
        params = {'query': query, 'limit': limit}
        return self._request("GET", "/trade-api/v2/markets", params=params)

    # ==================== Authenticated Endpoints ====================

    def get_balance(self) -> Dict:
        """Get account balance (requires auth)."""
        return self._request("GET", "/trade-api/v2/portfolio/balance", authenticated=True)

    def get_positions(self, cursor: str = None, limit: int = 100) -> Dict:
        """Get current positions (requires auth)."""
        params = {'limit': limit}
        if cursor:
            params['cursor'] = cursor
        return self._request("GET", "/trade-api/v2/portfolio/positions",
                           authenticated=True, params=params)

    def get_orders(self, status: str = None, cursor: str = None, limit: int = 100) -> Dict:
        """Get orders (requires auth)."""
        params = {'limit': limit}
        if status:
            params['status'] = status
        if cursor:
            params['cursor'] = cursor
        return self._request("GET", "/trade-api/v2/portfolio/orders",
                           authenticated=True, params=params)

    def get_fills(self, cursor: str = None, limit: int = 100) -> Dict:
        """Get fill history (requires auth)."""
        params = {'limit': limit}
        if cursor:
            params['cursor'] = cursor
        return self._request("GET", "/trade-api/v2/portfolio/fills",
                           authenticated=True, params=params)

    def create_order(self,
                     ticker: str,
                     side: str,
                     action: str = "buy",
                     type: str = "limit",
                     count: int = 1,
                     yes_price: int = None,
                     no_price: int = None,
                     expiration_ts: int = None) -> Dict:
        """
        Create a new order (requires auth).

        Args:
            ticker: Market ticker
            side: "yes" or "no"
            action: "buy" or "sell"
            type: "limit" or "market"
            count: Number of contracts
            yes_price: Price in cents for YES (1-99)
            no_price: Price in cents for NO (1-99)
            expiration_ts: Order expiration timestamp (optional)

        Returns:
            Order confirmation
        """
        data = {
            'ticker': ticker,
            'side': side,
            'action': action,
            'type': type,
            'count': count
        }
        if yes_price is not None:
            data['yes_price'] = yes_price
        if no_price is not None:
            data['no_price'] = no_price
        if expiration_ts is not None:
            data['expiration_ts'] = expiration_ts

        return self._request("POST", "/trade-api/v2/portfolio/orders",
                           authenticated=True, data=data)

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel an order (requires auth)."""
        return self._request("DELETE", f"/trade-api/v2/portfolio/orders/{order_id}",
                           authenticated=True)


# ==================== Sports Market Constants ====================

# Known sports series tickers on Kalshi
SPORTS_SERIES = {
    'nfl': 'KXSB',           # Super Bowl / Pro Football Championship
    'nba': 'KXNBA',          # NBA Finals / Pro Basketball Finals
    'nhl': 'KXNHL',          # Stanley Cup Finals
    'mlb': 'KXMLB',          # World Series / Pro Baseball Championship
    'ncaa_basketball': 'KXNCAAMBTOTAL',  # NCAA Basketball totals
}

# NFL prop market series
NFL_PROP_SERIES = {
    'championship': 'KXSB',              # Super Bowl winner
    'spread': 'KXNFLSPREAD',             # Point spreads
    'total': 'KXNFLTOTAL',               # Total points
    'team_total': 'KXNFLTEAMTOTAL',      # Team point totals
    'first_td': 'KXNFLFIRSTTD',          # First touchdown scorer
    'anytime_td': 'KXNFLANYTD',          # Anytime touchdown scorer
    'passing_yards': 'KXNFLPASSYDS',     # Passing yards props
    'rushing_yards': 'KXNFLRUSHYDS',     # Rushing yards props
    'receiving_yards': 'KXNFLRECYDS',    # Receiving yards props
}

# Player prop series (demo environment primarily)
PLAYER_PROP_SERIES = {
    'nhl_assists': 'KXNHLAST',
    'nhl_goals': 'KXNHLGOAL',
    'nhl_first_goal': 'KXNHLFIRSTGOAL',
    'nhl_points': 'KXNHLPTS',
}

# Team abbreviations for major leagues
NFL_TEAMS = {
    'ARI': 'Arizona', 'ATL': 'Atlanta', 'BAL': 'Baltimore', 'BUF': 'Buffalo',
    'CAR': 'Carolina', 'CHI': 'Chicago', 'CIN': 'Cincinnati', 'CLE': 'Cleveland',
    'DAL': 'Dallas', 'DEN': 'Denver', 'DET': 'Detroit', 'GB': 'Green Bay',
    'HOU': 'Houston', 'IND': 'Indianapolis', 'JAX': 'Jacksonville', 'KC': 'Kansas City',
    'LAC': 'LA Chargers', 'LAR': 'LA Rams', 'LV': 'Las Vegas', 'MIA': 'Miami',
    'MIN': 'Minnesota', 'NE': 'New England', 'NO': 'New Orleans', 'NYG': 'NY Giants',
    'NYJ': 'NY Jets', 'PHI': 'Philadelphia', 'PIT': 'Pittsburgh', 'SEA': 'Seattle',
    'SF': 'San Francisco', 'TB': 'Tampa Bay', 'TEN': 'Tennessee', 'WAS': 'Washington',
}


# ==================== Sports Market Helpers ====================

def get_championship_markets(api: KalshiAPI, sport: str = None) -> List[Dict]:
    """
    Get championship/finals markets for major sports leagues.

    Args:
        api: KalshiAPI instance
        sport: Optional sport filter ('nfl', 'nba', 'nhl', 'mlb')

    Returns:
        List of championship markets sorted by volume
    """
    all_markets = []

    series_to_fetch = [SPORTS_SERIES[sport]] if sport and sport in SPORTS_SERIES else SPORTS_SERIES.values()

    for series in series_to_fetch:
        try:
            result = api.get_markets(series_ticker=series, limit=100)
            markets = result.get('markets', [])
            all_markets.extend(markets)
        except Exception as e:
            print(f"Error fetching {series}: {e}")

    # Sort by volume (most active first)
    all_markets.sort(key=lambda m: m.get('volume', 0), reverse=True)
    return all_markets


def get_nfl_super_bowl_markets(api: KalshiAPI) -> List[Dict]:
    """Get all Super Bowl / Pro Football Championship markets."""
    return get_championship_markets(api, 'nfl')


def get_nba_finals_markets(api: KalshiAPI) -> List[Dict]:
    """Get all NBA Finals / Pro Basketball Championship markets."""
    return get_championship_markets(api, 'nba')


def get_nhl_stanley_cup_markets(api: KalshiAPI) -> List[Dict]:
    """Get all Stanley Cup Finals markets."""
    return get_championship_markets(api, 'nhl')


def get_mlb_world_series_markets(api: KalshiAPI) -> List[Dict]:
    """Get all World Series / Pro Baseball Championship markets."""
    return get_championship_markets(api, 'mlb')


def get_nfl_props(api: KalshiAPI) -> Dict[str, List[Dict]]:
    """
    Get all NFL prop markets organized by category.

    Returns:
        Dict with keys for each prop type containing list of markets
    """
    all_props = {}

    for prop_type, series in NFL_PROP_SERIES.items():
        try:
            result = api.get_markets(series_ticker=series, limit=100)
            markets = result.get('markets', [])
            # Filter to active only and sort by volume
            markets = [m for m in markets if m.get('status') == 'active']
            markets.sort(key=lambda m: m.get('volume', 0), reverse=True)
            all_props[prop_type] = markets
        except Exception as e:
            print(f"Error fetching {prop_type}: {e}")
            all_props[prop_type] = []

    return all_props


def find_sports_markets(api: KalshiAPI) -> List[Dict]:
    """
    Find all sports-related markets on Kalshi using known series tickers.

    Returns:
        List of sports markets sorted by volume
    """
    return get_championship_markets(api, sport=None)


def format_market_info(market: Dict) -> str:
    """Format market info for display."""
    ticker = market.get('ticker', 'N/A')
    title = market.get('title', 'N/A')
    status = market.get('status', 'N/A')
    yes_bid = market.get('yes_bid', 0)
    yes_ask = market.get('yes_ask', 0)
    volume = market.get('volume', 0)

    # Format volume with commas
    volume_str = f"{volume:,}" if volume else "0"

    return (f"{ticker}: {title}\n"
            f"  Status: {status} | YES Bid: {yes_bid}¢ | YES Ask: {yes_ask}¢ | Volume: {volume_str}")


def main():
    """Main entry point for testing."""
    import sys

    api = KalshiAPI()

    print(f"Kalshi API Client")
    print(f"Environment: {'DEMO' if api.use_demo else 'PRODUCTION'}")
    print(f"Base URL: {api.base_url}")
    print("=" * 60)

    # Parse command
    command = sys.argv[1] if len(sys.argv) > 1 else "status"

    try:
        if command == "status":
            status = api.get_exchange_status()
            print("\nExchange Status:")
            print(json.dumps(status, indent=2))

        elif command == "markets":
            query = sys.argv[2] if len(sys.argv) > 2 else None
            if query:
                result = api.search_markets(query)
            else:
                result = api.get_markets(status="open", limit=20)

            markets = result.get('markets', [])
            print(f"\nFound {len(markets)} markets:")
            for market in markets[:20]:
                print(f"\n{format_market_info(market)}")

        elif command == "sports":
            sport_filter = sys.argv[2] if len(sys.argv) > 2 else None
            if sport_filter:
                print(f"\nFetching {sport_filter.upper()} championship markets...")
                markets = get_championship_markets(api, sport_filter.lower())
            else:
                print("\nFetching all sports championship markets...")
                markets = find_sports_markets(api)

            print(f"\nFound {len(markets)} markets:")
            for market in markets[:30]:
                print(f"\n{format_market_info(market)}")

        elif command == "nfl":
            print("\nSuper Bowl / Pro Football Championship Markets:")
            markets = get_nfl_super_bowl_markets(api)
            print(f"Found {len(markets)} markets:\n")
            for market in markets[:32]:
                print(format_market_info(market))
                print()

        elif command == "nba":
            print("\nNBA Finals / Pro Basketball Championship Markets:")
            markets = get_nba_finals_markets(api)
            print(f"Found {len(markets)} markets:\n")
            for market in markets[:30]:
                print(format_market_info(market))
                print()

        elif command == "nhl":
            print("\nStanley Cup Finals Markets:")
            markets = get_nhl_stanley_cup_markets(api)
            print(f"Found {len(markets)} markets:\n")
            for market in markets[:32]:
                print(format_market_info(market))
                print()

        elif command == "mlb":
            print("\nWorld Series / Pro Baseball Championship Markets:")
            markets = get_mlb_world_series_markets(api)
            print(f"Found {len(markets)} markets:\n")
            for market in markets[:30]:
                print(format_market_info(market))
                print()

        elif command == "orderbook":
            ticker = sys.argv[2] if len(sys.argv) > 2 else None
            if not ticker:
                print("Usage: python kalshi_api.py orderbook <ticker>")
                return
            orderbook = api.get_market_orderbook(ticker)
            print(f"\nOrderbook for {ticker}:")
            print(json.dumps(orderbook, indent=2))

        elif command == "balance":
            if not api.api_key_id:
                print("Error: KALSHI_API_KEY_ID not set")
                return
            balance = api.get_balance()
            print("\nAccount Balance:")
            print(json.dumps(balance, indent=2))

        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  status              - Get exchange status")
            print("  markets [query]     - List open markets (optional: search query)")
            print("  sports [league]     - All sports markets (optional: nfl, nba, nhl, mlb)")
            print("  nfl                 - Super Bowl / Pro Football markets")
            print("  nba                 - NBA Finals markets")
            print("  nhl                 - Stanley Cup markets")
            print("  mlb                 - World Series markets")
            print("  orderbook <ticker>  - Get orderbook for a market")
            print("  balance             - Get account balance (requires auth)")
            print("\nEnvironment variables:")
            print("  KALSHI_USE_DEMO=false  - Use production API (default: demo)")
            print("  KALSHI_API_KEY_ID      - API key for authenticated endpoints")
            print("  KALSHI_PRIVATE_KEY_PATH - Path to RSA private key file")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
