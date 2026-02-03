#!/usr/bin/env python3
"""
Backend server for placing Kalshi wagers.
Supports multi-user authentication - each user connects their own Kalshi account.
Run with: python3 wagers_server.py
"""

import os
import tempfile
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from kalshi_api import KalshiAPI, get_nfl_props

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
CORS(app, supports_credentials=True)  # Allow requests with cookies


def get_user_api():
    """Get KalshiAPI instance for the current session user, or fall back to .env credentials."""
    if 'kalshi_api_key' in session and 'kalshi_private_key' in session:
        # Session-based credentials (logged in via modal)
        temp_key_file = tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False)
        temp_key_file.write(session['kalshi_private_key'])
        temp_key_file.close()

        try:
            return KalshiAPI(
                use_demo=False,
                api_key_id=session['kalshi_api_key'],
                private_key_path=temp_key_file.name
            )
        finally:
            os.unlink(temp_key_file.name)

    # Fall back to .env credentials if available
    if default_api:
        return default_api

    return None


# Initialize default API client from .env (if credentials are configured)
default_api = None
try:
    _api = KalshiAPI(use_demo=False)
    if _api.private_key and _api.api_key_id:
        default_api = _api
        print(f"Default credentials loaded from .env")
except Exception:
    pass


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate with Kalshi credentials.

    POST body:
    {
        "api_key": "your-kalshi-api-key-id",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\n..."
    }
    """
    try:
        data = request.json
        api_key = data.get('api_key')
        private_key = data.get('private_key')

        if not api_key or not private_key:
            return jsonify({'error': 'Missing api_key or private_key'}), 400

        # Store in session
        session['kalshi_api_key'] = api_key
        session['kalshi_private_key'] = private_key

        # Verify credentials by fetching balance
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Failed to initialize API'}), 500

        balance_data = api.get_balance()

        return jsonify({
            'success': True,
            'balance': balance_data.get('balance', 0)
        })

    except Exception as e:
        # Clear session on failed login
        session.pop('kalshi_api_key', None)
        session.pop('kalshi_private_key', None)
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 401


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session credentials."""
    session.pop('kalshi_api_key', None)
    session.pop('kalshi_private_key', None)
    return jsonify({'success': True})


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    """Check if user is authenticated."""
    is_authenticated = ('kalshi_api_key' in session and 'kalshi_private_key' in session) or default_api is not None
    return jsonify({'authenticated': is_authenticated})


@app.route('/api/balance', methods=['GET'])
def get_balance():
    """Get account balance."""
    try:
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        data = api.get_balance()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/markets', methods=['GET'])
def get_markets():
    """Get NFL prop markets."""
    try:
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        props = get_nfl_props(api)
        return jsonify(props)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions."""
    try:
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        data = api.get_positions()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/order', methods=['POST'])
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
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        data = request.json

        ticker = data.get('ticker')
        side = data.get('side')  # "yes" or "no"
        count = data.get('count', 1)
        price = data.get('price')  # Price in cents

        if not all([ticker, side, price]):
            return jsonify({'error': 'Missing required fields: ticker, side, price'}), 400

        # Place the order (action is always 'buy' for new positions)
        if side == 'yes':
            result = api.create_order(
                ticker=ticker,
                side='yes',
                action='buy',
                type='limit',
                count=count,
                yes_price=price
            )
        else:
            result = api.create_order(
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
def get_orders():
    """Get open orders."""
    try:
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        data = api.get_orders()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/order/<order_id>', methods=['DELETE'])
def cancel_order(order_id):
    """Cancel an order."""
    try:
        api = get_user_api()
        if not api:
            return jsonify({'error': 'Not authenticated'}), 401

        result = api.cancel_order(order_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Kalshi Wagers API server...")
    print("Multi-user mode: Users authenticate with their own Kalshi credentials")
    print("\nEndpoints:")
    print("  POST /api/auth/login  - Login with Kalshi API key + private key")
    print("  POST /api/auth/logout - Logout")
    print("  GET  /api/auth/status - Check authentication status")
    print("  GET  /api/balance     - Get account balance")
    print("  GET  /api/markets     - Get NFL prop markets")
    print("  GET  /api/positions   - Get current positions")
    print("  GET  /api/orders      - Get open orders")
    print("  POST /api/order       - Place an order")
    print("  DEL  /api/order/:id   - Cancel an order")
    print("\nServer running on http://localhost:5001")
    app.run(port=5001, debug=True)
