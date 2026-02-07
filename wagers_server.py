#!/usr/bin/env python3
"""
Backend server for placing Kalshi wagers.
Supports multi-user authentication via Yahoo OAuth.
Users link their Kalshi accounts after logging in with Yahoo.
Run with: python3 wagers_server.py
"""

import os
import base64
import urllib.parse
from functools import wraps

import requests
from flask import Flask, jsonify, request, redirect, g, make_response
from flask_cors import CORS
from dotenv import load_dotenv

from kalshi_api import KalshiAPI, get_nfl_props
from database import (
    init_db,
    get_or_create_user,
    create_session,
    get_user_by_session,
    delete_session,
    save_kalshi_credentials,
    get_kalshi_credentials,
    delete_kalshi_credentials,
    user_has_kalshi_credentials,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))

# Yahoo OAuth configuration
YAHOO_CLIENT_ID = os.environ.get('YAHOO_CLIENT_ID', '')
YAHOO_CLIENT_SECRET = os.environ.get('YAHOO_CLIENT_SECRET', '')
YAHOO_REDIRECT_URI = os.environ.get(
    'YAHOO_REDIRECT_URI',
    'http://localhost:5001/api/auth/yahoo/callback'
)
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:8000')

# Allow requests from GitHub Pages and localhost
ALLOWED_ORIGINS = [
    'https://adennis4.github.io',
    'http://localhost:8000',
    'http://localhost:5500',
    'http://127.0.0.1:5500',
    'http://localhost:3000',
]
CORS(app, supports_credentials=True, origins=ALLOWED_ORIGINS)

# Cookie settings
COOKIE_NAME = 'wp_session'
COOKIE_MAX_AGE = 30 * 24 * 60 * 60  # 30 days


def get_yahoo_auth_header():
    """Get Basic auth header for Yahoo token requests."""
    credentials = f"{YAHOO_CLIENT_ID}:{YAHOO_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


@app.before_request
def load_user():
    """Load user from session token (header or cookie)."""
    g.user = None
    g.kalshi_api = None

    # Check Authorization header first, then cookie
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        session_token = auth_header[7:]
    else:
        session_token = request.cookies.get(COOKIE_NAME)

    if session_token:
        user = get_user_by_session(session_token)
        if user:
            g.user = user
            # Load Kalshi API if user has linked credentials
            creds = get_kalshi_credentials(user.id)
            if creds:
                api_key, private_key = creds
                g.kalshi_api = KalshiAPI(
                    use_demo=False,
                    api_key_id=api_key,
                    private_key_pem=private_key
                )


def require_auth(f):
    """Decorator to require Yahoo authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            return jsonify({'error': 'Not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated


def require_kalshi(f):
    """Decorator to require Kalshi credentials."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.user:
            return jsonify({'error': 'Not authenticated'}), 401
        if not g.kalshi_api:
            return jsonify({'error': 'Kalshi account not linked'}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================================================
# Yahoo OAuth Endpoints
# ============================================================================

@app.route('/api/auth/yahoo')
def yahoo_auth():
    """Initiate Yahoo OAuth flow - redirects to Yahoo."""
    auth_url = (
        f"https://api.login.yahoo.com/oauth2/request_auth"
        f"?client_id={YAHOO_CLIENT_ID}"
        f"&redirect_uri={urllib.parse.quote(YAHOO_REDIRECT_URI)}"
        f"&response_type=code"
    )
    return redirect(auth_url)


@app.route('/api/auth/yahoo/callback')
def yahoo_callback():
    """Handle Yahoo OAuth callback."""
    error = request.args.get('error')
    if error:
        return redirect(f"{FRONTEND_URL}/wagers.html?error={error}")

    code = request.args.get('code')
    if not code:
        return redirect(f"{FRONTEND_URL}/wagers.html?error=no_code")

    # Exchange code for tokens
    try:
        token_response = requests.post(
            "https://api.login.yahoo.com/oauth2/get_token",
            headers={
                "Authorization": get_yahoo_auth_header(),
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": YAHOO_REDIRECT_URI
            }
        )

        if token_response.status_code != 200:
            return redirect(f"{FRONTEND_URL}/wagers.html?error=token_exchange_failed")

        tokens = token_response.json()
        access_token = tokens.get('access_token')

        # Yahoo returns the GUID in the token response
        yahoo_guid = tokens.get('xoauth_yahoo_guid')

        # If not in token response, fetch from Yahoo Social API
        if not yahoo_guid:
            guid_response = requests.get(
                "https://social.yahooapis.com/v1/me/guid?format=json",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if guid_response.status_code == 200:
                guid_data = guid_response.json()
                yahoo_guid = guid_data.get('guid', {}).get('value')

        # Get user's name from Yahoo Fantasy API (we have access to this)
        yahoo_email = None
        yahoo_name = None
        if yahoo_guid:
            try:
                # Try to get user info from Fantasy API
                fantasy_response = requests.get(
                    "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1?format=json",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                print(f"Yahoo Fantasy response: {fantasy_response.status_code}")
                if fantasy_response.status_code == 200:
                    fantasy_data = fantasy_response.json()
                    print(f"Yahoo Fantasy data: {fantasy_data}")
                    users = fantasy_data.get('fantasy_content', {}).get('users', {})
                    # Navigate the nested structure
                    for key, user_data in users.items():
                        if key == 'count':
                            continue
                        if isinstance(user_data, dict) and 'user' in user_data:
                            user_info = user_data['user']
                            for part in user_info:
                                if isinstance(part, list):
                                    for item in part:
                                        if isinstance(item, dict):
                                            if 'display_name' in item:
                                                yahoo_name = item['display_name']
                                            if 'guid' in item and not yahoo_guid:
                                                yahoo_guid = item['guid']
            except Exception as e:
                print(f"Error fetching Yahoo Fantasy user info: {e}")

        if not yahoo_guid:
            return redirect(f"{FRONTEND_URL}/wagers.html?error=no_user_id")

        print(f"Creating/updating user: guid={yahoo_guid}, name={yahoo_name}, email={yahoo_email}")

        # Create or get user
        user = get_or_create_user(yahoo_guid, yahoo_email, yahoo_name)

        # Create session
        session_token = create_session(user.id)

        # Redirect to frontend with session token in URL
        # Frontend will store in localStorage for subsequent requests
        return redirect(f"{FRONTEND_URL}/wagers.html?login=success&token={session_token}")

    except Exception as e:
        print(f"Yahoo OAuth error: {e}")
        return redirect(f"{FRONTEND_URL}/wagers.html?error=oauth_error")


@app.route('/api/auth/user', methods=['GET'])
def get_user():
    """Get current user info and Kalshi connection status."""
    if not g.user:
        return jsonify({'authenticated': False}), 200

    has_kalshi = user_has_kalshi_credentials(g.user.id)

    result = {
        'authenticated': True,
        'name': g.user.yahoo_name or g.user.yahoo_email or 'User',
        'email': g.user.yahoo_email,
        'has_kalshi': has_kalshi,
    }

    # Include Kalshi balance if connected
    if has_kalshi and g.kalshi_api:
        try:
            balance_data = g.kalshi_api.get_balance()
            result['kalshi_balance'] = balance_data.get('balance', 0)
        except Exception as e:
            result['kalshi_error'] = str(e)

    return jsonify(result)


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session and logout."""
    session_token = request.cookies.get(COOKIE_NAME)
    if session_token:
        delete_session(session_token)

    response = make_response(jsonify({'success': True}))
    response.delete_cookie(COOKIE_NAME, samesite='None', secure=True)
    return response


# ============================================================================
# Kalshi Credential Linking Endpoints
# ============================================================================

@app.route('/api/kalshi/link', methods=['POST'])
@require_auth
def link_kalshi():
    """Link Kalshi API credentials to user account."""
    try:
        data = request.json
        api_key = data.get('api_key')
        private_key = data.get('private_key')

        if not api_key or not private_key:
            return jsonify({'error': 'Missing api_key or private_key'}), 400

        # Verify credentials by testing them
        try:
            test_api = KalshiAPI(
                use_demo=False,
                api_key_id=api_key,
                private_key_pem=private_key
            )
            balance_data = test_api.get_balance()
        except Exception as e:
            return jsonify({'error': f'Invalid Kalshi credentials: {str(e)}'}), 400

        # Save encrypted credentials
        save_kalshi_credentials(g.user.id, api_key, private_key)

        return jsonify({
            'success': True,
            'balance': balance_data.get('balance', 0)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/kalshi/unlink', methods=['POST'])
@require_auth
def unlink_kalshi():
    """Remove Kalshi credentials from user account."""
    try:
        delete_kalshi_credentials(g.user.id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Kalshi Trading Endpoints (require Kalshi credentials)
# ============================================================================

@app.route('/api/balance', methods=['GET'])
@require_kalshi
def get_balance():
    """Get Kalshi account balance."""
    try:
        data = g.kalshi_api.get_balance()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets', methods=['GET'])
@require_kalshi
def get_markets():
    """Get NFL prop markets."""
    try:
        props = get_nfl_props(g.kalshi_api)
        return jsonify(props)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions', methods=['GET'])
@require_kalshi
def get_positions():
    """Get current positions."""
    try:
        data = g.kalshi_api.get_positions()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/order', methods=['POST'])
@require_kalshi
def place_order():
    """
    Place an order.

    POST body:
    {
        "ticker": "KXSB-26-SEA",
        "side": "yes",
        "count": 10,
        "price": 68
    }
    """
    try:
        data = request.json

        ticker = data.get('ticker')
        side = data.get('side')  # "yes" or "no"
        count = data.get('count', 1)
        price = data.get('price')  # Price in cents

        if not all([ticker, side, price]):
            return jsonify({'error': 'Missing required fields: ticker, side, price'}), 400

        # Place the order (action is always 'buy' for new positions)
        if side == 'yes':
            result = g.kalshi_api.create_order(
                ticker=ticker,
                side='yes',
                action='buy',
                type='limit',
                count=count,
                yes_price=price
            )
        else:
            result = g.kalshi_api.create_order(
                ticker=ticker,
                side='no',
                action='buy',
                type='limit',
                count=count,
                no_price=price
            )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/orders', methods=['GET'])
@require_kalshi
def get_orders():
    """Get open orders."""
    try:
        data = g.kalshi_api.get_orders()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/order/<order_id>', methods=['DELETE'])
@require_kalshi
def cancel_order(order_id):
    """Cancel an order."""
    try:
        result = g.kalshi_api.cancel_order(order_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


# ============================================================================
# Database Initialization
# ============================================================================

@app.cli.command('init-db')
def init_db_command():
    """Initialize the database tables."""
    init_db()
    print('Database initialized.')


# Initialize database tables on startup
try:
    init_db()
    print("Database tables initialized.")
except Exception as e:
    print(f"Database init error: {e}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'

    print("Starting Kalshi Wagers API server...")
    print(f"Mode: {'production' if not debug else 'development'}")
    print(f"\nServer running on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
