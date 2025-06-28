import redis
import json
import hashlib
import os
import time
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisClient:
    """Redis client for caching news, TTS, and content processing"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
            max_connections=50
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connection successful")
        except redis.ConnectionError:
            logger.error("❌ Redis connection failed - running without cache")
            self.redis_client = None
    
    def is_available(self):
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def generate_key_hash(self, *args):
        """Generate a consistent hash for cache keys"""
        key_string = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_string.encode()).hexdigest()[:12]
    
    # ==================== NEWS CACHING ====================
    
    def cache_news_headlines(self, category, language, country, articles, ttl=900):
        """Cache news headlines (15 min TTL)"""
        if not self.is_available():
            return False
        
        try:
            key = f"news:headlines:{category}:{language}:{country}"
            data = {
                'articles': articles,
                'cached_at': time.time()
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            logger.info(f"📰 Cached headlines: {key} ({len(articles)} articles)")
            return True
        except Exception as e:
            logger.error(f"Error caching headlines: {e}")
            return False
    
    def get_cached_news_headlines(self, category, language, country):
        """Get cached news headlines"""
        if not self.is_available():
            return None
        
        try:
            key = f"news:headlines:{category}:{language}:{country}"
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                logger.info(f"🎯 Cache HIT: {key} ({len(data['articles'])} articles)")
                return data['articles']
            logger.info(f"❌ Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting cached headlines: {e}")
            return None
    
    def cache_news_search(self, query, language, country, articles, ttl=1800):
        """Cache news search results (30 min TTL)"""
        if not self.is_available():
            return False
        
        try:
            query_hash = self.generate_key_hash(query.lower())
            key = f"news:search:{query_hash}:{language}:{country}"
            data = {
                'articles': articles,
                'query': query,
                'cached_at': time.time()
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            logger.info(f"🔍 Cached search: '{query}' -> {len(articles)} articles")
            return True
        except Exception as e:
            logger.error(f"Error caching search: {e}")
            return False
    
    def get_cached_news_search(self, query, language, country):
        """Get cached news search results"""
        if not self.is_available():
            return None
        
        try:
            query_hash = self.generate_key_hash(query.lower())
            key = f"news:search:{query_hash}:{language}:{country}"
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                logger.info(f"🎯 Search cache HIT: '{query}' ({len(data['articles'])} articles)")
                return data['articles']
            logger.info(f"❌ Search cache MISS: '{query}'")
            return None
        except Exception as e:
            logger.error(f"Error getting cached search: {e}")
            return None
    
    # ==================== ARTICLE CONTENT CACHING ====================
    
    def cache_article_content(self, url, content_data, ttl=86400):
        """Cache extracted article content (24 hour TTL)"""
        if not self.is_available():
            return False
        
        try:
            url_hash = self.generate_key_hash(url)
            key = f"article:content:{url_hash}"
            data = {
                **content_data,
                'url': url,
                'cached_at': time.time()
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            logger.info(f"📄 Cached article: {url[:60]}...")
            return True
        except Exception as e:
            logger.error(f"Error caching article content: {e}")
            return False
    
    def get_cached_article_content(self, url):
        """Get cached article content"""
        if not self.is_available():
            return None
        
        try:
            url_hash = self.generate_key_hash(url)
            key = f"article:content:{url_hash}"
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                logger.info(f"🎯 Article cache HIT: {url[:60]}...")
                return data
            logger.info(f"❌ Article cache MISS: {url[:60]}...")
            return None
        except Exception as e:
            logger.error(f"Error getting cached article: {e}")
            return None
    
    # ==================== CONTENT OPTIMIZATION CACHING ====================
    
    def cache_optimized_content(self, original_content, word_limit, include_intro, include_outro, optimized_text, ttl=86400):
        """Cache optimized content (24 hour TTL)"""
        if not self.is_available():
            return False
        
        try:
            content_hash = self.generate_key_hash(original_content)
            params_hash = self.generate_key_hash(word_limit, include_intro, include_outro)
            key = f"content:optimized:{content_hash}:{params_hash}"
            
            data = {
                'optimized_text': optimized_text,
                'params': {
                    'word_limit': word_limit,
                    'include_intro': include_intro,
                    'include_outro': include_outro
                },
                'cached_at': time.time()
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            logger.info(f"✨ Cached optimized content: {len(original_content)} -> {len(optimized_text)} chars")
            return True
        except Exception as e:
            logger.error(f"Error caching optimized content: {e}")
            return False
    
    def get_cached_optimized_content(self, original_content, word_limit, include_intro, include_outro):
        """Get cached optimized content"""
        if not self.is_available():
            return None
        
        try:
            content_hash = self.generate_key_hash(original_content)
            params_hash = self.generate_key_hash(word_limit, include_intro, include_outro)
            key = f"content:optimized:{content_hash}:{params_hash}"
            
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                logger.info(f"🎯 Optimized content cache HIT")
                return data['optimized_text']
            logger.info(f"❌ Optimized content cache MISS")
            return None
        except Exception as e:
            logger.error(f"Error getting cached optimized content: {e}")
            return None
    
    # ==================== TTS AUDIO CACHING ====================
    
    def cache_tts_audio_path(self, text, voice_id, speed, audio_path, ttl=604800):
        """Cache TTS audio file path (7 days TTL)"""
        if not self.is_available():
            return False
        
        try:
            text_hash = self.generate_key_hash(text)
            params_hash = self.generate_key_hash(voice_id, speed)
            key = f"tts:audio:{text_hash}:{params_hash}"
            
            data = {
                'audio_path': audio_path,
                'text_preview': text[:100],
                'voice_id': voice_id,
                'speed': speed,
                'cached_at': time.time()
            }
            self.redis_client.setex(key, ttl, json.dumps(data))
            logger.info(f"🎵 Cached TTS audio: {voice_id} - {text[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Error caching TTS audio: {e}")
            return False
    
    def get_cached_tts_audio_path(self, text, voice_id, speed):
        """Get cached TTS audio file path"""
        if not self.is_available():
            return None
        
        try:
            text_hash = self.generate_key_hash(text)
            params_hash = self.generate_key_hash(voice_id, speed)
            key = f"tts:audio:{text_hash}:{params_hash}"
            
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                # Verify file still exists
                if os.path.exists(data['audio_path']):
                    logger.info(f"🎯 TTS cache HIT: {voice_id} - {text[:30]}...")
                    return data['audio_path']
            logger.info(f"❌ TTS cache MISS: {voice_id} - {text[:30]}...")
            return None
        except Exception as e:
            logger.error(f"Error getting cached TTS audio: {e}")
            return None