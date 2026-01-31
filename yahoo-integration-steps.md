# Yahoo Fantasy Sports API Integration Guide

This guide walks you through setting up access to the Yahoo Fantasy Sports API to pull league data for the Warrior Poets application.

---

## Prerequisites

- A Yahoo account (the league commissioner account is recommended)
- Access to your Yahoo Fantasy Football league

---

## Step 1: Create a Yahoo Developer Account

1. Go to [Yahoo Developer Network](https://developer.yahoo.com/)
2. Sign in with your Yahoo account
3. Accept the Developer Terms of Service if prompted

---

## Step 2: Register Your Application

1. Navigate to [Create an App](https://developer.yahoo.com/apps/create/)
2. Fill in the application details:
   - **Application Name**: `Warrior Poets Stats` (or your preferred name)
   - **Application Type**: Select **Web Application**
   - **Description**: Brief description of your app
   - **Home Page URL**: Your website URL (can be `http://localhost:8000` for development)
   - **Redirect URI(s)**: Add your callback URL, e.g.:
     - For development: `https://localhost:8000/callback` or `oob` (out-of-band)
     - For production: `https://yourdomain.com/callback`
   - **API Permissions**:
     - Check **Fantasy Sports**
     - Select **Read** (or **Read/Write** if you need to make changes)

3. Click **Create App**

4. **Save your credentials** (you'll need these):
   - **Consumer Key** (also called Client ID)
   - **Consumer Secret** (also called Client Secret)

> **Important**: Keep your Consumer Secret confidential. Never commit it to public repositories.

---

## Step 3: Find Your League Key

Your league key is required to fetch league-specific data. The format is:

```
{game_key}.l.{league_id}
```

### To find your league ID:

1. Go to [Yahoo Fantasy Football](https://football.fantasysports.yahoo.com/)
2. Navigate to your league
3. Look at the URL - it will contain your league ID:
   ```
   https://football.fantasysports.yahoo.com/f1/123456
   ```
   In this example, `123456` is your league ID.

### Game Keys by Season:

| Season | Game Key |
|--------|----------|
| 2025   | 449      |
| 2024   | 423      |
| 2023   | 414      |
| 2022   | 406      |
| 2021   | 399      |
| 2020   | 390      |
| 2019   | 380      |
| 2018   | 371      |
| 2017   | 359      |
| 2016   | 348      |
| 2015   | 331      |
| 2014   | 314      |
| 2013   | 273      |
| 2012   | 242      |
| 2011   | 223      |
| 2010   | 199      |
| 2009   | 147      |

**Example**: For the 2024 season with league ID 123456, your league key would be: `423.l.123456`

---

## Step 4: OAuth 2.0 Authentication Flow

Yahoo uses OAuth 2.0 for API authentication. Here's the flow:

### 4a. Request Authorization

Direct users to Yahoo's authorization URL:

```
https://api.login.yahoo.com/oauth2/request_auth
  ?client_id=YOUR_CONSUMER_KEY
  &redirect_uri=YOUR_REDIRECT_URI
  &response_type=code
  &state=random_state_string
```

**Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | Your Consumer Key |
| `redirect_uri` | Yes | Must match what you registered |
| `response_type` | Yes | Must be `code` |
| `state` | Recommended | Random string to prevent CSRF |

### 4b. User Grants Permission

The user will see Yahoo's authorization page and grant permission. After approval, Yahoo redirects to your `redirect_uri` with an authorization code:

```
https://yoursite.com/callback?code=AUTHORIZATION_CODE&state=your_state
```

### 4c. Exchange Code for Access Token

Make a POST request to get your access token:

```
POST https://api.login.yahoo.com/oauth2/get_token
```

**Headers:**
```
Authorization: Basic {base64_encode(client_id:client_secret)}
Content-Type: application/x-www-form-urlencoded
```

**Body:**
```
grant_type=authorization_code
&code=AUTHORIZATION_CODE
&redirect_uri=YOUR_REDIRECT_URI
```

**Response:**
```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "refresh_token": "YOUR_REFRESH_TOKEN",
  "expires_in": 3600,
  "token_type": "bearer",
  "xoauth_yahoo_guid": "USER_GUID"
}
```

### 4d. Refresh Tokens

Access tokens expire after 1 hour. Use the refresh token to get a new one:

```
POST https://api.login.yahoo.com/oauth2/get_token
```

**Headers:**
```
Authorization: Basic {base64_encode(client_id:client_secret)}
Content-Type: application/x-www-form-urlencoded
```

**Body:**
```
grant_type=refresh_token
&refresh_token=YOUR_REFRESH_TOKEN
```

---

## Step 5: Make API Requests

### Base URL
```
https://fantasysports.yahooapis.com/fantasy/v2/
```

### Authentication Header
Include your access token in all requests:
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

### Useful Endpoints

| Endpoint | Description |
|----------|-------------|
| `/league/{league_key}` | League metadata |
| `/league/{league_key}/settings` | League settings and rules |
| `/league/{league_key}/standings` | Current standings |
| `/league/{league_key}/scoreboard` | Weekly matchups and scores |
| `/league/{league_key}/teams` | All teams in the league |
| `/team/{team_key}/roster` | Team roster |
| `/team/{team_key}/matchups` | Team's matchup history |
| `/league/{league_key}/players` | Available players |

### Response Format

By default, responses are XML. To get JSON, add the `format` parameter:

```
/league/{league_key}/standings?format=json
```

### Example Request

```bash
curl -X GET \
  "https://fantasysports.yahooapis.com/fantasy/v2/league/423.l.123456/standings?format=json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Step 6: Data You Can Retrieve

### League Data
- League name, settings, scoring rules
- Number of teams, roster positions
- Trade and waiver settings

### Standings
- Team records (wins, losses, ties)
- Points for/against
- Playoff standings

### Weekly Scores
- Matchup results by week
- Individual team scores
- Head-to-head records

### Team Rosters
- Player names and positions
- Weekly starting lineups
- Bench players

### Historical Data
- Access past seasons by using the appropriate game key
- Pull historical standings and matchups

---

## Recommended Libraries

### Node.js
```bash
npm install yahoo-fantasy
```

Documentation: [yahoo-fantasy on npm](https://www.npmjs.com/package/yahoo-fantasy)

### Python
```bash
pip install yahoo_oauth yahoo_fantasy_api
```

### PHP
Use the [OAuth extension](https://www.php.net/manual/en/book.oauth.php) or a library like [league/oauth2-client](https://github.com/thephpleague/oauth2-client)

---

## Rate Limits

Yahoo does not publish explicit rate limits, but best practices:
- Cache responses when possible
- Avoid making requests more than once per minute for the same data
- Batch requests where possible using sub-resources

---

## Troubleshooting

### Common Issues

1. **"Invalid redirect URI"**
   - Ensure your redirect URI exactly matches what's registered in your app settings

2. **"Consumer key invalid"**
   - Double-check your Consumer Key
   - Ensure your app has Fantasy Sports permissions enabled

3. **"Token expired"**
   - Use your refresh token to get a new access token
   - Refresh tokens can also expire if unused for extended periods

4. **"Private league"**
   - You can only access private league data if the authenticated user is a member

---

## Resources

- [Yahoo Fantasy Sports API Documentation](https://developer.yahoo.com/fantasysports/guide/)
- [Yahoo OAuth 2.0 Guide](https://developer.yahoo.com/oauth2/guide/)
- [Yahoo Developer Apps Dashboard](https://developer.yahoo.com/apps/)
- [yahoo-fantasy npm package](https://www.npmjs.com/package/yahoo-fantasy)
- [Yahoo Fantasy API Demo (GitHub)](https://github.com/smock514/yahoo-fantasy-api-demo)
