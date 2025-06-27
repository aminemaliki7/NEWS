import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Redis client, fallback gracefully if not available
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    print("[GNews] Redis client not available, running without cache")
    REDIS_AVAILABLE = False
    redis_client = None

class GNewsClient:
    """Client for interacting with the GNews API with Redis caching and smart key management"""
    
    def __init__(self):
        # Load 8 API keys from .env
        self.api_keys = [
            os.getenv('GNEWS_API_KEY_1'),
            os.getenv('GNEWS_API_KEY_2'),
            os.getenv('GNEWS_API_KEY_3'),
            os.getenv('GNEWS_API_KEY_4'),
            os.getenv('GNEWS_API_KEY_5'),
            os.getenv('GNEWS_API_KEY_6'),
            os.getenv('GNEWS_API_KEY_7'),
            os.getenv('GNEWS_API_KEY_8')
        ]
        
        if not any(self.api_keys):
            raise ValueError("No GNEWS_API_KEY_X set in .env")
        
        self.api_index = 0
        self.base_url = "https://gnews.io/api/v4"
    
    def _get_next_available_key(self):
        """Get the next available API key (not in cooldown)"""
        for _ in range(len(self.api_keys)):
            current_key = self.api_keys[self.api_index]
            
            if current_key and (not REDIS_AVAILABLE or redis_client.is_api_key_available(self.api_index)):
                return current_key, self.api_index
            
            # Move to next key
            self.api_index = (self.api_index + 1) % len(self.api_keys)
        
        # If all keys are in cooldown, return the current one anyway
        return self.api_keys[self.api_index], self.api_index
    
    def get_top_headlines(self, category=None, language="en", country="us", max_results=10, query=None):
        """Get top headlines with Redis caching"""
        
        # 🚀 CHECK CACHE FIRST (if Redis available)
        if REDIS_AVAILABLE:
            cached_articles = redis_client.get_cached_news_headlines(category or "general", language, country)
            if cached_articles:
                return {"articles": cached_articles}
        
        # 📡 CACHE MISS - Fetch from API
        endpoint = f"{self.base_url}/top-headlines"
        
        params = {
            "lang": language,
            "country": country,
            "max": max_results
        }
        
        if category and category != "all":
            params["topic"] = category
        
        if query:
            params["q"] = query
        
        MAX_RETRIES = len(self.api_keys)
        
        for attempt in range(MAX_RETRIES):
            current_token, key_index = self._get_next_available_key()
            
            if not current_token:
                print(f"[GNews] Skipping empty key at index {key_index + 1}")
                self.api_index = (self.api_index + 1) % MAX_RETRIES
                continue
            
            params["token"] = current_token
            
            try:
                # Track API usage (if Redis available)
                if REDIS_AVAILABLE:
                    redis_client.track_api_key_usage(key_index, 'gnews')
                
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                
                result = response.json()
                articles = result.get('articles', [])
                
                # 💾 CACHE THE RESULT (if Redis available)
                if REDIS_AVAILABLE:
                    redis_client.cache_news_headlines(
                        category or "general", 
                        language, 
                        country, 
                        articles,
                        ttl=900  # 15 minutes
                    )
                
                print(f"[GNews] ✅ API success with key {key_index + 1}")
                return result
            
            except requests.exceptions.HTTPError as e:
                print(f"[GNews] API key {key_index + 1} failed: {e}")
                
                if response.status_code in [401, 403, 429]:
                    # Mark key as failed and move to next (if Redis available)
                    if REDIS_AVAILABLE:
                        redis_client.mark_api_key_failed(key_index, 'gnews', cooldown_seconds=3600)
                    self.api_index = (self.api_index + 1) % MAX_RETRIES
                    continue
                else:
                    # For other HTTP errors, break and return generic failure
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"[GNews] Request error: {e}")
                break
        
        # If all retries fail
        return {
            "articles": [],
            "error": "Unable to load articles at the moment."
        }
    
    def search_news(self, query, language="en", country="us", max_results=10, from_date=None, to_date=None):
        """Search news with Redis caching"""
        
        # 🚀 CHECK CACHE FIRST (if Redis available)
        if REDIS_AVAILABLE:
            cached_articles = redis_client.get_cached_news_search(query, language, country)
            if cached_articles:
                return {"articles": cached_articles}
        
        # 📡 CACHE MISS - Fetch from API
        endpoint = f"{self.base_url}/search"
        
        params = {
            "q": query,
            "lang": language,
            "country": country,
            "max": max_results
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        MAX_RETRIES = len(self.api_keys)
        
        for attempt in range(MAX_RETRIES):
            current_token, key_index = self._get_next_available_key()
            
            if not current_token:
                print(f"[GNews] Skipping empty key at index {key_index + 1}")
                self.api_index = (self.api_index + 1) % MAX_RETRIES
                continue
            
            params["token"] = current_token
            
            try:
                # Track API usage (if Redis available)
                if REDIS_AVAILABLE:
                    redis_client.track_api_key_usage(key_index, 'gnews')
                
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                
                result = response.json()
                articles = result.get('articles', [])
                
                # 💾 CACHE THE RESULT (if Redis available)
                if REDIS_AVAILABLE:
                    redis_client.cache_news_search(
                        query,
                        language,
                        country,
                        articles,
                        ttl=1800  # 30 minutes
                    )
                
                print(f"[GNews] ✅ Search success with key {key_index + 1}")
                return result
            
            except requests.exceptions.HTTPError as e:
                print(f"[GNews] API key {key_index + 1} failed: {e}")
                
                if response.status_code in [401, 403, 429]:
                    if REDIS_AVAILABLE:
                        redis_client.mark_api_key_failed(key_index, 'gnews', cooldown_seconds=3600)
                    self.api_index = (self.api_index + 1) % MAX_RETRIES
                    continue
                else:
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"[GNews] Request error: {e}")
                break
        
        return {
            "articles": [],
            "error": "Unable to load articles at the moment."
        }
    
    def fetch_article_content(self, url):
        """Fetch article content with Redis caching"""
        
        # 🚀 CHECK CACHE FIRST (if Redis available)
        if REDIS_AVAILABLE:
            cached_content = redis_client.get_cached_article_content(url)
            if cached_content:
                return cached_content
        
        # 📡 CACHE MISS - Fetch from web
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                json_data = response.json()
                article_text = self._extract_text_from_json(json_data)
                result = {
                    "title": self._extract_title_from_json(json_data),
                    "content": article_text,
                    "url": url,
                    "extraction_time": datetime.now().isoformat()
                }
            else:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                title = soup.title.string if soup.title else "Unknown Title"
                content = self._extract_content_with_multiple_strategies(soup)
                
                if not content or len(content) < 100:
                    paragraphs = soup.find_all('p')
                    content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40])
                
                if not content or len(content) < 100:
                    result = {
                        "title": title,
                        "content": "This article's content couldn't be extracted automatically. Please visit the original article at " + url,
                        "url": url,
                        "extraction_error": "Content extraction failed"
                    }
                else:
                    result = {
                        "title": title,
                        "content": content,
                        "url": url,
                        "extraction_time": datetime.now().isoformat()
                    }
            
            # 💾 CACHE THE RESULT (if Redis available)
            if REDIS_AVAILABLE:
                redis_client.cache_article_content(url, result, ttl=86400)  # 24 hours
            
            return result
        
        except Exception as e:
            print(f"[GNews] Error extracting article content: {e}")
            return {
                "title": "Content Extraction Failed",
                "content": "Unable to extract content from this article.",
                "url": url,
                "error": "Content extraction failed. Please try again."
            }
    
    def _extract_content_with_multiple_strategies(self, soup):
        content = ""
        
        article_selectors = [
            'article', '.article-body', '.article-content', '.story-body', '.story-content', '.entry-content',
            '.post-content', '.content', '.main-content', '#article-body', '.article__body', '.article__content',
            '.story__body', '.story__content', '.post__content', '.news-article', '.news-content', '.page-content',
            '.rich-text', '.article-text', '.article-main', '.main-article', '.article-body-content'
        ]
        
        for selector in article_selectors:
            try:
                if selector.startswith('.'):
                    elements = soup.select(selector)
                elif selector.startswith('#'):
                    element = soup.select_one(selector)
                    elements = [element] if element else []
                else:
                    elements = soup.find_all(selector)
                
                if elements:
                    for element in elements:
                        paragraphs = element.find_all('p')
                        if paragraphs:
                            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
                            if len(content) > 200:
                                return content
            except Exception as e:
                print(f"Error in selector {selector}: {e}")
                continue
        
        paragraphs_by_parent = {}
        for p in soup.find_all('p'):
            parent = p.parent
            if parent not in paragraphs_by_parent:
                paragraphs_by_parent[parent] = []
            paragraphs_by_parent[parent].append(p)
        
        if paragraphs_by_parent:
            sorted_parents = sorted(paragraphs_by_parent.keys(), 
                                    key=lambda x: len(paragraphs_by_parent[x]), 
                                    reverse=True)
            main_parent = sorted_parents[0]
            paragraphs = paragraphs_by_parent[main_parent]
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
        
        return content
    
    def _extract_text_from_json(self, json_data):
        if 'content' in json_data:
            return json_data['content']
        elif 'article' in json_data and 'body' in json_data['article']:
            return json_data['article']['body']
        return ""
    
    def _extract_title_from_json(self, json_data):
        if 'title' in json_data:
            return json_data['title']
        elif 'article' in json_data and 'title' in json_data['article']:
            return json_data['article']['title']
        return "Article Title"

# Example usage (for testing, not part of the deployed app)
if __name__ == "__main__":
    client = GNewsClient()
    news = client.get_top_headlines(category="technology", language="en", max_results=5)
    
    if "articles" in news:
        for article in news["articles"]:
            print(f"Title: {article['title']}")
            print(f"Source: {article['source']['name']}")
            print(f"URL: {article['url']}")
            print("---")
    else:
        print("Error fetching news")
        print(news.get("error", "Unknown error"))