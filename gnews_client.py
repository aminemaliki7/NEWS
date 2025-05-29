import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GNewsClient:
    """Client for interacting with the GNews API"""
    
    def __init__(self):
        self.api_key = os.getenv('GNEWS_API_KEY')
        if not self.api_key:
            raise ValueError("GNEWS_API_KEY not found in environment variables")
        
        self.base_url = "https://gnews.io/api/v4"
    
    def get_top_headlines(self, category=None, language="en", country="us", max_results=10, query=None):
        """
        Fetch top headlines from GNews
        
        Args:
            category (str): News category (general, world, nation, business, technology, entertainment, sports, science, health)
            language (str): 2-letter language code
            country (str): 2-letter country code
            max_results (int): Maximum number of results to return (1-100)
            query (str): Optional search query
            
        Returns:
            dict: JSON response from the API
        """
        endpoint = f"{self.base_url}/top-headlines"
        params = {
            "token": self.api_key,
            "lang": language,
            "country": country,
            "max": max_results
        }
        
        if category and category != "all":
            params["topic"] = category
            
        if query:
            params["q"] = query
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()  # Raise exception for error status codes
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching top headlines: {e}")
            return {"articles": [], "error": str(e)}
    
    def search_news(self, query, language="en", country="us", max_results=10, from_date=None, to_date=None):
        """
        Search for news articles
        
        Args:
            query (str): Search query
            language (str): 2-letter language code
            country (str): 2-letter country code
            max_results (int): Maximum number of results to return (1-100)
            from_date (str): Start date in YYYY-MM-DD format
            to_date (str): End date in YYYY-MM-DD format
            
        Returns:
            dict: JSON response from the API
        """
        endpoint = f"{self.base_url}/search"
        params = {
            "token": self.api_key,
            "q": query,
            "lang": language,
            "country": country,
            "max": max_results
        }
        
        if from_date:
            params["from"] = from_date
            
        if to_date:
            params["to"] = to_date
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching news: {e}")
            return {"articles": [], "error": str(e)}

    def fetch_article_content(self, url):
        """
        Fetch and extract content from a news article
        
        Args:
            url (str): URL of the article
            
        Returns:
            dict: Article content with title, text, and metadata
        """
        try:
            # Set user agent and headers to avoid 406 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Make the request with proper headers
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # For development: print response details to debug
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            # Handle different content types
            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                print("Received JSON content - extracting text from JSON")
                # Handle JSON content (some sites return JSON)
                json_data = response.json()
                # Extract relevant parts (this is site-specific)
                article_text = self._extract_text_from_json(json_data)
                return {
                    "title": self._extract_title_from_json(json_data),
                    "content": article_text,
                    "url": url,
                    "extraction_time": datetime.now().isoformat()
                }
            
            # Very simple content extraction - this is a placeholder
            # For production, use newspaper3k or a similar library
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else "Unknown Title"
            
            # Try multiple content extraction strategies
            content = self._extract_content_with_multiple_strategies(soup)
            
            if not content or len(content) < 100:  # If content is too short, it's probably not the actual article
                print(f"Content too short ({len(content)} chars), fallback to generic extraction")
                # Fallback to a very generic approach - get all paragraphs from the page
                paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40])
            
            # If all else fails, provide a useful message
            if not content or len(content) < 100:
                return {
                    "title": title,
                    "content": "This article's content couldn't be extracted automatically. Please visit the original article at " + url,
                    "url": url,
                    "extraction_error": "Content extraction failed"
                }
            
            return {
                "title": title,
                "content": content,
                "url": url,
                "extraction_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"Error extracting article content: {e}")
            return {
                "title": "Content Extraction Failed",
                "content": f"Unable to extract content from {url}. Error: {str(e)}",
                "url": url,
                "error": str(e)
            }
    
    def _extract_content_with_multiple_strategies(self, soup):
        """
        Try multiple approaches to extract the article content
        
        Args:
            soup (BeautifulSoup): Parsed HTML
            
        Returns:
            str: Extracted content
        """
        content = ""
        
        # Strategy 1: Look for article body by common class names
        article_selectors = [
            'article', 
            '.article-body', 
            '.article-content',
            '.story-body',
            '.story-content', 
            '.entry-content',
            '.post-content',
            '.content',
            '.main-content',
            '#article-body',
            '.article__body',
            '.article__content',
            '.story__body',
            '.story__content',
            '.post__content',
            '.news-article',
            '.news-content',
            '.page-content',
            '.rich-text',
            '.article-text',
            '.article-main',
            '.main-article',
            '.article-body-content'
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
                    # Extract paragraphs from the first matching element
                    for element in elements:
                        paragraphs = element.find_all('p')
                        if paragraphs:
                            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
                            if len(content) > 200:  # If we got substantial content, use it
                                return content
            except Exception as e:
                print(f"Error in selector {selector}: {e}")
                continue
        
        # Strategy 2: Look for main content area
        main_selectors = ['main', '#main', '.main', 'article']
        for selector in main_selectors:
            try:
                if selector.startswith('.') or selector.startswith('#'):
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    paragraphs = element.find_all('p')
                    if paragraphs:
                        content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
                        if len(content) > 200:
                            return content
            except Exception:
                continue
                
        # Strategy 3: Find the div with the most paragraphs
        paragraphs_by_parent = {}
        for p in soup.find_all('p'):
            parent = p.parent
            if parent not in paragraphs_by_parent:
                paragraphs_by_parent[parent] = []
            paragraphs_by_parent[parent].append(p)
        
        if paragraphs_by_parent:
            # Sort parents by number of paragraphs
            sorted_parents = sorted(paragraphs_by_parent.keys(), 
                                    key=lambda x: len(paragraphs_by_parent[x]), 
                                    reverse=True)
            
            # Get the parent with the most paragraphs
            main_parent = sorted_parents[0]
            paragraphs = paragraphs_by_parent[main_parent]
            
            # Extract text from these paragraphs
            content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 0])
            
        return content
    
    def _extract_text_from_json(self, json_data):
        """
        Extract text from JSON response (site-specific, needs customization)
        
        Args:
            json_data (dict): JSON data from the response
            
        Returns:
            str: Extracted text
        """
        # This is highly site-specific and needs customization
        # Example:
        if 'content' in json_data:
            return json_data['content']
        elif 'article' in json_data and 'body' in json_data['article']:
            return json_data['article']['body']
        
        # If we can't extract, return empty string
        return ""
    
    def _extract_title_from_json(self, json_data):
        """
        Extract title from JSON response
        
        Args:
            json_data (dict): JSON data from the response
            
        Returns:
            str: Extracted title
        """
        # This is highly site-specific
        if 'title' in json_data:
            return json_data['title']
        elif 'article' in json_data and 'title' in json_data['article']:
            return json_data['article']['title']
        
        return "Article Title"


# Example usage
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