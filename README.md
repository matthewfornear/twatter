# Twitter/X Tweet Data Extractor

A Python toolkit for extracting tweet content and user information from Twitter/X API responses.

## What It Does

This project extracts structured data from Twitter/X tweets including:
- Tweet text, timestamps, and engagement metrics
- User profile information (name, bio, follower count, etc.)
- Media attachments and metadata
- Verification status and account details

## How It Works

The extraction process uses Twitter's GraphQL API endpoints that are called when viewing tweets in a browser. The project uses a single combined script that handles both fetching and extracting data.

### Main Script (`script/twitter_extractor.py`)
Combined API client and data extractor that:
- Makes authenticated requests to Twitter's GraphQL endpoints
- Handles both `TweetDetail` and `TweetResultByRestId` formats
- Extracts structured tweet and user information
- Saves both raw and processed data to JSON files

### Configuration (`settings/config.json`)
Contains all API endpoints, headers, and request parameters:
- API endpoint URLs
- Request headers and features
- GraphQL variables and field toggles

## Setup Requirements

### Authentication Tokens
You need to add your authentication tokens to the configuration file:

1. **Auth Token** - Found in browser cookies as `auth_token`
2. **CSRF Token** - Found in browser cookies as `ct0`

### How to Get Tokens
1. Open Twitter/X in your browser and log in
2. Open Developer Tools (F12)
3. Go to Application/Storage tab
4. Find Cookies for x.com
5. Copy the values for `auth_token` and `ct0`

### Configure Authentication
Edit `settings/config.json` and update the auth section:
```json
{
  "auth": {
    "auth_token": "your_auth_token_here",
    "csrf_token": "your_csrf_token_here"
  },
  ...
}
```

Optional: Set a default tweet ID to use when running the script without arguments:
```json
{
  "default_tweet_id": "1975583212085932341",
  ...
}
```

### Installation
```bash
pip install -r script/requirements.txt
```

## Usage

### Fetch and Extract Tweet Data
```bash
python script/twitter_extractor.py [tweet_id]
```

Examples:
```bash
python script/twitter_extractor.py 1975583212085932341  # specific tweet
python script/twitter_extractor.py                     # uses default_tweet_id from config
```

This creates two files in the `output/` directory:
- Raw API response (e.g., `tweet_detail_1975583212085932341.json`)
- Extracted structured data (e.g., `extracted_1975583212085932341.json`)

### Extract from Existing File
```bash
python script/twitter_extractor.py extract <input_file> <output_filename>
```

Example:
```bash
python script/twitter_extractor.py extract output/tweet_detail_123.json extracted_123.json
```

This processes an existing API response file and creates extracted data.

## Output Structure

The extracted data includes:

**Tweet Information:**
- ID, text, creation timestamp
- Engagement metrics (likes, retweets, replies, views)
- Media attachments
- Language and source

**User Information:**
- User ID, screen name, display name
- Bio/description and location
- Follower/following counts
- Verification status
- Profile and banner images
- Account creation date

## File Structure

```
/
├── script/
│   ├── twitter_extractor.py  # Combined fetch and extract script
│   └── requirements.txt      # Python dependencies
├── settings/
│   └── config.json          # API configuration and headers
├── output/                  # Directory for generated files
└── README.md               # This file
```

## API Endpoints Used

The project targets two Twitter GraphQL endpoints:

1. **TweetDetail** (`JgryuItLZQ9V56vHjGIWWw`) - Comprehensive tweet data with conversation context
2. **TweetResultByRestId** (`URPP6YZ5eDCjdVMSREn4gg`) - Single tweet data

These endpoints are called automatically when viewing tweets in a browser and contain all the necessary data for extraction.

## Error Handling

- Invalid authentication tokens will cause API requests to fail
- Missing tweet IDs will return empty responses
- Network errors are handled with appropriate error messages
- Malformed responses are caught during parsing

## Limitations

- Requires valid Twitter/X authentication tokens
- Tokens expire and need periodic refresh
- Rate limits may apply based on Twitter's policies
- Private/protected tweets may not be accessible

## Disclaimer

This project is intended for educational purposes only. It demonstrates how to interact with Twitter/X GraphQL APIs and parse structured data from API responses.

Users are responsible for ensuring their use of this tool complies with:
- Twitter/X Terms of Service
- Twitter/X Developer Agreement and Policy
- Applicable data protection and privacy laws
- Rate limiting and API usage guidelines

The authors of this project assume no liability for misuse or any violations of Twitter/X's terms of service. Use responsibly and respect Twitter/X's platform rules and policies.
