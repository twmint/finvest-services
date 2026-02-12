import time
import json
import random
import requests
import requests_cache
from bs4 import BeautifulSoup

url = "https://finance.yahoo.com/markets/"

RETRY_DELAY = 2 # seconds
RETRYABLE_STATUS_CODES = {
    408, # Request Timeout
    429, # Too Many Requests
    500, # Internal Server Error
    502, # Bad Gateway
    503, # Service Unavailable
    504, # Gateway Timeout
    520, # Cloudflare Unknown Error
    521, # Cloudflare Web Server Is Down
    522, # Cloudflare Connection Timed Out
    523, # Cloudflare Origin Is Unreachable
    524, # Cloudflare A Timeout Occurred
}

with open('user_agents.json', 'r') as f:
    USER_AGENTS = json.load(f)["user_agents"]

HEADERS = { 
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
          }

class Scraper:
    def __init__(self, cache_expire: int = 10):
        self._session = requests_cache.CachedSession(
            cache_name = 'response_cache',
            expire_after = cache_expire,
            allowable_codes=[200]
        )
        
    def get_headers(self):
        return {**HEADERS, "User-Agent": random.choice(USER_AGENTS)}

    def get(self, url, retry=2):
        for attempt in range(retry + 1):
            try:
                response = self._session.get(url, headers = self.get_headers())
                return response
            except requests.exceptions.RequestException as e:
                if hasattr(e, "response") and e.response is not None:
                    status_code = e.response.status_code
                    if status_code in RETRYABLE_STATUS_CODES and attempt < retry:
                        print(f"Retrying after {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        print(f"code: {e.response.status_code}, text: {e.response.text}")
                else:
                    if attempt < retry:
                        print(f"Network error: {str(e)}. Retrying after {RETRY_DELAY} seconds...")
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        print(f"Network error after {retry} retries: {str(e)}")
                        return None
    
    def get_soup(self, url):
        res = self.get(url)
        if res is None:
            return None
        soup = BeautifulSoup(res.text, "html.parser")
        return soup

    def clear_cache(self):
        self._session.cache.clear()
