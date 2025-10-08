#!/usr/bin/env python3
"""
Twitter/X Tweet Data Extractor

Combined script for fetching and extracting tweet content and user information
from Twitter/X API responses. Supports both TweetDetail and TweetResultByRestId 
GraphQL endpoints.
"""

import json
import os
import sys
import requests
from datetime import datetime
from typing import Dict, Any, Optional


class TwitterExtractor:
    """Combined Twitter API client and data extractor."""
    
    def __init__(self, output_dir: str = "output", settings_dir: str = "settings"):
        """Initialize extractor with directories."""
        self.output_dir = output_dir
        self.settings_dir = settings_dir
        self.config = self._load_config()
        
        # Get auth tokens from config
        self.auth_token = self.config["auth"]["auth_token"]
        self.csrf_token = self.config["auth"]["csrf_token"]
        
        self.ensure_output_dir()
        self._setup_headers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from settings file."""
        config_path = os.path.join(self.settings_dir, "config.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            sys.exit(1)
    
    def ensure_output_dir(self):
        """Create output directory if it doesn't exist."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _setup_headers(self):
        """Setup headers and cookies from config."""
        self.headers = self.config["headers"].copy()
        self.headers["x-csrf-token"] = self.csrf_token
        
        self.cookies = {
            'auth_token': self.auth_token,
            'ct0': self.csrf_token,
        }
    
    def fetch_tweet_detail(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Fetch tweet data using TweetDetail GraphQL endpoint."""
        url = self.config["api_endpoints"]["tweet_detail"]
        
        variables = self.config["tweet_detail_variables"].copy()
        variables["focalTweetId"] = tweet_id
        
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(self.config["tweet_detail_features"]),
            'fieldToggles': json.dumps(self.config["tweet_detail_field_toggles"])
        }
        
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching tweet detail: {e}")
            return None
    
    def fetch_tweet_result(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Fetch tweet data using TweetResultByRestId GraphQL endpoint."""
        url = self.config["api_endpoints"]["tweet_result"]
        
        variables = self.config["tweet_result_variables"].copy()
        variables["tweetId"] = tweet_id
        
        params = {
            'variables': json.dumps(variables),
            'features': json.dumps(self.config["tweet_result_features"]),
            'fieldToggles': json.dumps(self.config["tweet_result_field_toggles"])
        }
        
        try:
            response = requests.get(url, headers=self.headers, cookies=self.cookies, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching tweet result: {e}")
            return None
    
    def extract_from_tweet_detail(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract data from TweetDetail API response."""
        try:
            instructions = response_data['data']['threaded_conversation_with_injections_v2']['instructions']
            
            # Find entries
            entries = None
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    break
            
            if not entries:
                return None
            
            # Find focal tweet
            focal_tweet = None
            for entry in entries:
                if 'tweet-' in entry.get('entryId', ''):
                    content = entry.get('content', {})
                    item_content = content.get('itemContent', {})
                    tweet_results = item_content.get('tweet_results', {})
                    result = tweet_results.get('result', {})
                    
                    if result.get('__typename') == 'Tweet':
                        focal_tweet = result
                        break
            
            if not focal_tweet:
                return None
            
            return self._extract_tweet_data(focal_tweet)
            
        except Exception as e:
            print(f"Error extracting from TweetDetail: {e}")
            return None
    
    def extract_from_tweet_result(self, response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract data from TweetResultByRestId API response."""
        try:
            tweet_result = response_data['data']['tweetResult']
            if tweet_result.get('result', {}).get('__typename') == 'Tweet':
                return self._extract_tweet_data(tweet_result['result'])
            return None
            
        except Exception as e:
            print(f"Error extracting from TweetResult: {e}")
            return None
    
    def _extract_tweet_data(self, tweet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tweet and user data from tweet object."""
        legacy = tweet_data.get('legacy', {})
        core = tweet_data.get('core', {})
        user_results = core.get('user_results', {})
        user_result = user_results.get('result', {})
        user_legacy = user_result.get('legacy', {})
        
        # Extract tweet information
        tweet_info = {
            'tweet_id': tweet_data.get('rest_id'),
            'text': legacy.get('full_text', ''),
            'created_at': legacy.get('created_at', ''),
            'retweet_count': legacy.get('retweet_count', 0),
            'favorite_count': legacy.get('favorite_count', 0),
            'reply_count': legacy.get('reply_count', 0),
            'quote_count': legacy.get('quote_count', 0),
            'bookmark_count': legacy.get('bookmark_count', 0),
            'views': tweet_data.get('views', {}).get('count'),
            'lang': legacy.get('lang', ''),
            'source': legacy.get('source', ''),
        }
        
        # Extract media if present
        media_list = legacy.get('extended_entities', {}).get('media', [])
        tweet_info['media'] = []
        for media in media_list:
            tweet_info['media'].append({
                'type': media.get('type'),
                'url': media.get('media_url_https'),
                'display_url': media.get('display_url'),
            })
        
        # Extract user information
        user_info = {
            'user_id': user_result.get('rest_id'),
            'screen_name': user_legacy.get('screen_name', ''),
            'name': user_legacy.get('name', ''),
            'description': user_legacy.get('description', ''),
            'location': user_legacy.get('location', ''),
            'followers_count': user_legacy.get('followers_count', 0),
            'friends_count': user_legacy.get('friends_count', 0),
            'statuses_count': user_legacy.get('statuses_count', 0),
            'created_at': user_legacy.get('created_at', ''),
            'verified': user_legacy.get('verified', False),
            'is_blue_verified': user_result.get('is_blue_verified', False),
            'profile_image_url': user_legacy.get('profile_image_url_https', ''),
            'profile_banner_url': user_legacy.get('profile_banner_url', ''),
            'url': user_legacy.get('url', ''),
        }
        
        return {
            'extracted_at': datetime.now().isoformat(),
            'tweet': tweet_info,
            'user': user_info,
        }
    
    def save_response(self, data: Dict[str, Any], filename: str):
        """Save API response to file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Response saved to: {filepath}")
    
    def save_extracted_data(self, data: Dict[str, Any], filename: str):
        """Save extracted data to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Extracted data saved to: {filepath}")
    
    def fetch_and_extract(self, tweet_id: str, save_raw: bool = True, save_extracted: bool = True) -> Optional[Dict[str, Any]]:
        """Fetch tweet data and extract structured information."""
        print(f"Fetching tweet {tweet_id}...")
        
        # Try TweetDetail first (more comprehensive)
        api_data = self.fetch_tweet_detail(tweet_id)
        extracted_data = None
        
        if api_data:
            if save_raw:
                self.save_response(api_data, f"tweet_detail_{tweet_id}.json")
            
            extracted_data = self.extract_from_tweet_detail(api_data)
        
        # If TweetDetail fails, try TweetResult
        if not extracted_data:
            print("TweetDetail failed, trying TweetResult...")
            api_data = self.fetch_tweet_result(tweet_id)
            
            if api_data:
                if save_raw:
                    self.save_response(api_data, f"tweet_result_{tweet_id}.json")
                
                extracted_data = self.extract_from_tweet_result(api_data)
        
        if extracted_data:
            if save_extracted:
                self.save_extracted_data(extracted_data, f"extracted_{tweet_id}.json")
            
            return extracted_data
        else:
            print("Failed to fetch and extract tweet data")
            return None
    
    def extract_from_file(self, input_file: str, output_filename: str):
        """Extract data from saved API response file."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                response_data = json.load(f)
            
            # Try TweetDetail format first
            extracted_data = self.extract_from_tweet_detail(response_data)
            
            # If that fails, try TweetResult format
            if not extracted_data:
                extracted_data = self.extract_from_tweet_result(response_data)
            
            if extracted_data:
                self.save_extracted_data(extracted_data, output_filename)
                return extracted_data
            else:
                print("Could not extract data from response")
                return None
                
        except Exception as e:
            print(f"Error processing file {input_file}: {e}")
            return None


def main():
    """Main function to run the extractor."""
    extractor = TwitterExtractor()
    
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        # Extract mode: process existing file
        if len(sys.argv) != 4:
            print("Usage: python twitter_extractor.py extract <input_file> <output_filename>")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_filename = sys.argv[3]
        
        if not os.path.exists(input_file):
            print(f"Input file not found: {input_file}")
            sys.exit(1)
        
        result = extractor.extract_from_file(input_file, output_filename)
        
        if result:
            print("Extraction completed successfully")
            print(f"Tweet: @{result['user']['screen_name']} - {result['tweet']['text'][:100]}...")
            print(f"User: {result['user']['name']} ({result['user']['followers_count']:,} followers)")
        else:
            print("Extraction failed")
            sys.exit(1)
    
    else:
        # Fetch mode: get tweet from API
        # Use tweet ID from command line arg OR from config
        if len(sys.argv) > 1:
            tweet_id = sys.argv[1]
        else:
            tweet_id = extractor.config.get("default_tweet_id")
            if not tweet_id:
                print("Usage: python twitter_extractor.py [tweet_id]")
                print("       python twitter_extractor.py extract <input_file> <output_filename>")
                print()
                print("Examples:")
                print("  python twitter_extractor.py 1975583212085932341")
                print("  python twitter_extractor.py  # uses default_tweet_id from config.json")
                print("  python twitter_extractor.py extract output/tweet_detail_123.json extracted_123.json")
                print()
                print("Note: Authentication tokens and default tweet ID are loaded from settings/config.json")
                sys.exit(1)
        
        print(f"Using tweet ID: {tweet_id}")
        result = extractor.fetch_and_extract(tweet_id)
        
        if result:
            print("Fetch and extraction completed successfully")
            print(f"Tweet: @{result['user']['screen_name']} - {result['tweet']['text'][:100]}...")
            print(f"User: {result['user']['name']} ({result['user']['followers_count']:,} followers)")
            print(f"Engagement: {result['tweet']['favorite_count']:,} likes, {result['tweet']['retweet_count']:,} retweets")
        else:
            print("Failed to fetch and extract tweet data")
            sys.exit(1)


if __name__ == "__main__":
    main()
