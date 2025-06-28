import requests
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# RECURSION PROTECTION
sys.setrecursionlimit(1000)  # Reduce recursion limit to catch issues early

# Try to import Redis client, fallback gracefully if not available
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
    print("[GNews] ✅ Redis client imported successfully")
except ImportError:
    print("[GNews] ❌ Redis client not available, running without cache")
    REDIS_AVAILABLE = False
    redis_client = None
except Exception as e:
    print(f"[GNews] ❌ Redis client error: {e}, running without cache")
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
        
        # Filter out None/empty keys
        self.api_keys = [key for key in self.api_keys if key and key.strip()]
        
        if not self.api_keys:
            print("[GNews] ⚠️ No valid API keys found, using fallback mode")
            self.api_keys = ["fallback_key"]  # Prevent empty list
        
        print(f"[GNews] 📊 Loaded {len(self.api_keys)} API keys")
        
        self.api_index = 0
        self.base_url = "https://gnews.io/api/v4"
        self.request_count = 0  # Track requests to prevent loops
        self.max_requests_per_method = 3  # Prevent infinite retries
    
    def _get_next_available_key(self):
        """Get the next available API key with safety checks"""
        if not self.api_keys:
            return None, -1
            
        current_key = self.api_keys[self.api_index % len(self.api_keys)]
        
        # Simple rotation without Redis dependency for now
        return current_key, self.api_index
    
    def _safe_cache_check(self, cache_method, *args):
        """Safely check cache with error handling"""
        if not REDIS_AVAILABLE or not redis_client:
            return None
            
        try:
            return getattr(redis_client, cache_method)(*args)
        except AttributeError:
            print(f"[GNews] ⚠️ Redis method {cache_method} not found")
            return None
        except Exception as e:
            print(f"[GNews] ⚠️ Cache check error: {e}")
            return None
    
    def _safe_cache_set(self, cache_method, *args):
        """Safely set cache with error handling"""
        if not REDIS_AVAILABLE or not redis_client:
            return False
            
        try:
            getattr(redis_client, cache_method)(*args)
            return True
        except AttributeError:
            print(f"[GNews] ⚠️ Redis method {cache_method} not found")
            return False
        except Exception as e:
            print(f"[GNews] ⚠️ Cache set error: {e}")
            return False
    
    def get_top_headlines(self, category=None, language="en", country="us", max_results=10, query=None):
        """Get top headlines with recursion protection"""
        
        # RECURSION PROTECTION
        if hasattr(self, '_getting_headlines') and self._getting_headlines:
            print("[GNews] 🚨 Recursion detected in get_top_headlines, returning fallback")
            return self._get_fallback_articles()
        
        self._getting_headlines = True
        
        try:
            return self._get_headlines_internal(category, language, country, max_results, query)
        finally:
            self._getting_headlines = False
    
    def _get_headlines_internal(self, category, language, country, max_results, query):
        """Internal method for getting headlines"""
        
        # 🚀 CHECK CACHE FIRST (with safety)
        cached_articles = self._safe_cache_check('get_cached_news_headlines', category or "general", language, country)
        if cached_articles:
            print("[GNews] 🎯 Cache HIT for headlines")
            return {"articles": cached_articles}
        
        print("[GNews] ❌ Cache MISS for headlines")
        
        # 📡 FETCH FROM API
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
        
        # LIMIT RETRIES TO PREVENT INFINITE LOOPS
        MAX_RETRIES = min(3, len(self.api_keys))  # Max 3 retries
        
        for attempt in range(MAX_RETRIES):
            current_token, key_index = self._get_next_available_key()
            
            if not current_token or current_token == "fallback_key":
                print(f"[GNews] ⚠️ No valid API key available, using fallback")
                return self._get_fallback_articles()
            
            params["token"] = current_token
            
            try:
                print(f"[GNews] 📡 Trying API request {attempt + 1}/{MAX_RETRIES} with key {key_index + 1}")
                
                response = requests.get(endpoint, params=params, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                articles = result.get('articles', [])
                
                # 💾 SAFE CACHE SET
                self._safe_cache_set('cache_news_headlines', 
                                   category or "general", language, country, articles, 900)
                
                print(f"[GNews] ✅ API success with key {key_index + 1}, got {len(articles)} articles")
                return result
            
            except requests.exceptions.HTTPError as e:
                print(f"[GNews] ❌ API key {key_index + 1} failed: {e}")
                
                if hasattr(response, 'status_code') and response.status_code in [401, 403, 429]:
                    # Move to next key
                    self.api_index = (self.api_index + 1) % len(self.api_keys)
                    continue
                else:
                    break
            
            except requests.exceptions.RequestException as e:
                print(f"[GNews] ❌ Request error: {e}")
                break
            
            except Exception as e:
                print(f"[GNews] ❌ Unexpected error: {e}")
                break
        
        # If all retries fail, return fallback
        print("[GNews] 🔄 All API attempts failed, using fallback articles")
        return self._get_fallback_articles()
    
    def search_news(self, query, language="en", country="us", max_results=10, from_date=None, to_date=None):
        """Search news with recursion protection"""
        
        # RECURSION PROTECTION
        if hasattr(self, '_searching_news') and self._searching_news:
            print("[GNews] 🚨 Recursion detected in search_news, returning fallback")
            return self._get_fallback_articles()
        
        self._searching_news = True
        
        try:
            return self._search_news_internal(query, language, country, max_results, from_date, to_date)
        finally:
            self._searching_news = False
    
    def _search_news_internal(self, query, language, country, max_results, from_date, to_date):
        """Internal method for searching news"""
        
        # 🚀 CHECK CACHE FIRST (with safety)
        cached_articles = self._safe_cache_check('get_cached_news_search', query, language, country)
        if cached_articles:
            print("[GNews] 🎯 Cache HIT for search")
            return {"articles": cached_articles}
        
        print("[GNews] ❌ Cache MISS for search")
        
        # 📡 FETCH FROM API
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
        
        # LIMIT RETRIES TO PREVENT INFINITE LOOPS
        MAX_RETRIES = min(3, len(self.api_keys))
        
        for attempt in range(MAX_RETRIES):
            current_token, key_index = self._get_next_available_key()
            
            if not current_token or current_token == "fallback_key":
                print(f"[GNews] ⚠️ No valid API key available for search")
                return self._get_fallback_articles()
            
            params["token"] = current_token
            
            try:
                print(f"[GNews] 📡 Search attempt {attempt + 1}/{MAX_RETRIES} with key {key_index + 1}")
                
                response = requests.get(endpoint, params=params, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                articles = result.get('articles', [])
                
                # 💾 SAFE CACHE SET
                self._safe_cache_set('cache_news_search', 
                                   query, language, country, articles, 1800)
                
                print(f"[GNews] ✅ Search success with key {key_index + 1}, got {len(articles)} articles")
                return result
            
            except requests.exceptions.HTTPError as e:
                print(f"[GNews] ❌ Search API key {key_index + 1} failed: {e}")
                self.api_index = (self.api_index + 1) % len(self.api_keys)
                continue
            
            except Exception as e:
                print(f"[GNews] ❌ Search error: {e}")
                break
        
        return self._get_fallback_articles()
    
    def fetch_article_content(self, url):
        """Fetch article content with recursion protection"""
        
        # RECURSION PROTECTION
        if hasattr(self, '_fetching_content') and self._fetching_content:
            print("[GNews] 🚨 Recursion detected in fetch_article_content")
            return {
                "title": "Content Fetch Error",
                "content": "Unable to fetch content due to recursion protection.",
                "url": url,
                "error": "Recursion prevented"
            }
        
        self._fetching_content = True
        
        try:
            return self._fetch_content_internal(url)
        finally:
            self._fetching_content = False
    
    def _fetch_content_internal(self, url):
        """Internal method for fetching content"""
        
        # 🚀 CHECK CACHE FIRST (with safety)
        cached_content = self._safe_cache_check('get_cached_article_content', url)
        if cached_content:
            print("[GNews] 🎯 Cache HIT for article content")
            return cached_content
        
        print("[GNews] ❌ Cache MISS for article content")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'application/json' in content_type:
                json_data = response.json()
                result = {
                    "title": self._extract_title_from_json(json_data),
                    "content": self._extract_text_from_json(json_data),
                    "url": url,
                    "extraction_time": datetime.now().isoformat()
                }
            else:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    title = soup.title.string if soup.title else "Unknown Title"
                    content = self._extract_content_simple(soup)
                    
                    result = {
                        "title": title,
                        "content": content if content and len(content) > 100 else "Content extraction was limited. Please visit the original article.",
                        "url": url,
                        "extraction_time": datetime.now().isoformat()
                    }
                except ImportError:
                    result = {
                        "title": "Content Extraction Unavailable",
                        "content": "BeautifulSoup not available for content extraction. Please visit the original article.",
                        "url": url,
                        "error": "Missing dependency"
                    }
            
            # 💾 SAFE CACHE SET
            self._safe_cache_set('cache_article_content', url, result, 86400)
            
            return result
        
        except Exception as e:
            print(f"[GNews] ❌ Content extraction error: {e}")
            return {
                "title": "Content Extraction Failed",
                "content": "Unable to extract content from this article. Please visit the original source.",
                "url": url,
                "error": str(e)
            }
    
    def _extract_content_simple(self, soup):
        """Simple content extraction to avoid recursion"""
        try:
            # Try main content areas first
            for selector in ['article', '.article-body', '.content', '.post-content']:
                element = soup.select_one(selector)
                if element:
                    paragraphs = element.find_all('p')
                    if paragraphs:
                        content = '\n\n'.join([p.get_text().strip() for p in paragraphs[:10]])  # Limit to 10 paragraphs
                        if len(content) > 200:
                            return content
            
            # Fallback: get all paragraphs
            paragraphs = soup.find_all('p')[:15]  # Limit to 15 paragraphs
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40])
            
            return content
        
        except Exception as e:
            print(f"[GNews] Content extraction error: {e}")
            return "Content extraction failed."
    
    def _extract_text_from_json(self, json_data):
        """Extract text from JSON response"""
        if isinstance(json_data, dict):
            if 'content' in json_data:
                return json_data['content']
            elif 'article' in json_data and isinstance(json_data['article'], dict):
                if 'body' in json_data['article']:
                    return json_data['article']['body']
        return "Content not found in JSON response."
    
    def _extract_title_from_json(self, json_data):
        """Extract title from JSON response"""
        if isinstance(json_data, dict):
            if 'title' in json_data:
                return json_data['title']
            elif 'article' in json_data and isinstance(json_data['article'], dict):
                if 'title' in json_data['article']:
                    return json_data['article']['title']
        return "Article Title"
    
    def _get_fallback_articles(self):
        """Return fallback articles when API fails"""
        return {
            "articles": [
                {
                    "title": "Sample Technology News",
                    "description": "This is a sample article displayed when the news API is temporarily unavailable. The system is designed to gracefully handle API limitations.",
                    "url": "https://example.com/tech-news",
                    "image": "https://placehold.co/400x300/0066cc/ffffff?text=Tech+News",
                    "publishedAt": datetime.now().isoformat(),
                    "source": {"name": "NewsNap System"}
                },
                {
                    "title": "Business Update",
                    "description": "Another sample article to demonstrate the fallback system functionality. Your app continues to work even when external APIs have issues.",
                    "url": "https://example.com/business-news",
                    "image": "https://placehold.co/400x300/ff6600/ffffff?text=Business",
                    "publishedAt": datetime.now().isoformat(),
                    "source": {"name": "NewsNap System"}
                },
                {
                    "title": "Health & Science",
                    "description": "The third sample article shows how the system maintains user experience during API outages or rate limiting situations.",
                    "url": "https://example.com/health-news",
                    "image": "https://placehold.co/400x300/00cc66/ffffff?text=Health",
                    "publishedAt": datetime.now().isoformat(),
                    "source": {"name": "NewsNap System"}
                }
            ],
            "fallback": True,
            "message": "Displaying sample articles due to API limitations"
        }

# Prevent recursion in module import
if __name__ == "__main__":
    print("GNews Client - Testing Mode")
    try:
        client = GNewsClient()
        print(f"Initialized with {len(client.api_keys)} API keys")
        
        # Test with fallback
        news = client.get_top_headlines(category="technology", max_results=3)
        print(f"Got {len(news.get('articles', []))} articles")
        
        for article in news.get("articles", [])[:2]:
            print(f"- {article.get('title', 'No title')}")
        
    except Exception as e:
        print(f"Test error: {e}")
else:
    print("[GNews] 🚀 GNews Client module loaded successfully")