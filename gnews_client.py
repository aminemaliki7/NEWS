import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GNewsClient:
    """Client for interacting with the GNews API (with multi-key failover)"""

    def __init__(self):
        self.api_keys = [
            os.getenv(f'GNEWS_API_KEY_{i}') for i in range(1, 9)
        ]

        if not any(self.api_keys):
            raise ValueError("No GNEWS_API_KEY_X set in .env")

        self.api_index = 0
        self.base_url = "https://gnews.io/api/v4"

    def get_top_headlines(self, category=None, language="any", country="any", max_results=10, query=None):
        endpoint = f"{self.base_url}/top-headlines"

        params = {"max": max_results}

        if language != "any":
            params["lang"] = language
        if country != "any":
            params["country"] = country
        if category and category != "all":
            params["topic"] = category
        if query:
            params["q"] = query

        return self._make_request_with_retry(endpoint, params)

    def search_news(self, query, language="en", country="any", max_results=10, from_date=None, to_date=None):
        endpoint = f"{self.base_url}/search"

        params = {"q": query, "max": max_results}
        if language != "any":
            params["lang"] = language
        if country != "any":
            params["country"] = country
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date

        return self._make_request_with_retry(endpoint, params)

    def _make_request_with_retry(self, endpoint, params):
        MAX_RETRIES = len(self.api_keys)

        for _ in range(MAX_RETRIES):
            current_token = self.api_keys[self.api_index]
            if not current_token:
                print(f"[GNews] Skipping empty key at index {self.api_index + 1}")
                self.api_index = (self.api_index + 1) % MAX_RETRIES
                continue

            params["token"] = current_token

            try:
                response = requests.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.HTTPError as e:
                print(f"[GNews] API key {self.api_index + 1} failed: {e}")
                if response.status_code in [401, 403, 429]:
                    self.api_index = (self.api_index + 1) % MAX_RETRIES
                    continue
                break
            except requests.exceptions.RequestException as e:
                print(f"[GNews] Request error: {e}")
                break

        return {"articles": [], "error": "Unable to load articles at the moment."}

    def fetch_article_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '').lower()
            if 'application/json' in content_type:
                json_data = response.json()
                return {
                    "title": self._extract_title_from_json(json_data),
                    "content": self._extract_text_from_json(json_data),
                    "url": url,
                    "extraction_time": datetime.now().isoformat()
                }

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.title.string if soup.title else "Unknown Title"
            content = self._extract_content_with_multiple_strategies(soup)

            if not content or len(content) < 100:
                paragraphs = soup.find_all('p')
                content = '\n\n'.join([p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 40])

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
            print(f"[GNews] Error extracting article content: {e}")
            return {
                "title": "Content Extraction Failed",
                "content": "Unable to extract content from this article.",
                "url": url,
                "error": "Content extraction failed. Please try again."
            }

    def _extract_content_with_multiple_strategies(self, soup):
        selectors = [
            'article', '.article-body', '.article-content', '.story-body', '.story-content', '.entry-content',
            '.post-content', '.content', '.main-content', '#article-body', '.article__body', '.article__content',
            '.story__body', '.story__content', '.post__content', '.news-article', '.news-content', '.page-content',
            '.rich-text', '.article-text', '.article-main', '.main-article', '.article-body-content'
        ]

        for selector in selectors:
            try:
                elements = soup.select(selector) if selector.startswith('.') or selector.startswith('#') else soup.find_all(selector)
                for element in elements:
                    paragraphs = element.find_all('p')
                    content = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(content) > 200:
                        return content
            except Exception as e:
                print(f"Error in selector {selector}: {e}")
                continue

        paragraphs_by_parent = {}
        for p in soup.find_all('p'):
            parent = p.parent
            paragraphs_by_parent.setdefault(parent, []).append(p)

        if paragraphs_by_parent:
            main_parent = max(paragraphs_by_parent, key=lambda x: len(paragraphs_by_parent[x]))
            paragraphs = paragraphs_by_parent[main_parent]
            return '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

        return ""

    def _extract_text_from_json(self, json_data):
        return json_data.get('content') or json_data.get('article', {}).get('body', "")

    def _extract_title_from_json(self, json_data):
        return json_data.get('title') or json_data.get('article', {}).get('title', "Article Title")

# Example usage
if __name__ == "__main__":
    client = GNewsClient()
    news = client.get_top_headlines(category="technology", language="en", country="us", max_results=5)

    if "articles" in news:
        for article in news["articles"]:
            print(f"Title: {article['title']}")
            print(f"Source: {article['source']['name']}")
            print(f"URL: {article['url']}")
            print("---")
    else:
        print("Error fetching news")
        print(news.get("error", "Unknown error"))
