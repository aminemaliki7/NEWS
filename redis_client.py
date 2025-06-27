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
                else:
                    # File was deleted, remove from cache
                    self.redis_client.delete(key)
                    logger.info(f"🗑️ TTS cache cleanup: file missing")
            logger.info(f"❌ TTS cache MISS: {voice_id} - {text[:30]}...")
            return None
        except Exception as e:
            logger.error(f"Error getting cached TTS audio: {e}")
            return None
    
    # ==================== API KEY MANAGEMENT ====================
    
    def track_api_key_usage(self, key_index, endpoint='gnews'):
        """Track API key usage"""
        if not self.is_available():
            return
        
        try:
            current_hour = int(time.time() // 3600)
            key = f"api:usage:{endpoint}:{key_index}:{current_hour}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, 3600)  # Expire after 1 hour
        except Exception as e:
            logger.error(f"Error tracking API usage: {e}")
    
    def get_api_key_usage(self, key_index, endpoint='gnews'):
        """Get current hour's API key usage"""
        if not self.is_available():
            return 0
        
        try:
            current_hour = int(time.time() // 3600)
            key = f"api:usage:{endpoint}:{key_index}:{current_hour}"
            usage = self.redis_client.get(key)
            return int(usage) if usage else 0
        except Exception as e:
            logger.error(f"Error getting API usage: {e}")
            return 0
    
    def mark_api_key_failed(self, key_index, endpoint='gnews', cooldown_seconds=3600):
        """Mark API key as failed with cooldown"""
        if not self.is_available():
            return
        
        try:
            key = f"api:failed:{endpoint}:{key_index}"
            self.redis_client.setex(key, cooldown_seconds, "failed")
            logger.warning(f"🚫 API key {key_index + 1} marked as failed for {cooldown_seconds}s")
        except Exception as e:
            logger.error(f"Error marking API key failed: {e}")
    
    def is_api_key_available(self, key_index, endpoint='gnews'):
        """Check if API key is available (not in cooldown)"""
        if not self.is_available():
            return True  # Default to available if Redis is down
        
        try:
            key = f"api:failed:{endpoint}:{key_index}"
            return not self.redis_client.exists(key)
        except Exception as e:
            logger.error(f"Error checking API key availability: {e}")
            return True
    
    # ==================== CACHE STATISTICS ====================
    
    def get_cache_stats(self):
        """Get cache statistics"""
        if not self.is_available():
            return {"status": "Redis unavailable"}
        
        try:
            info = self.redis_client.info()
            stats = {
                'status': 'connected',
                'redis_version': info.get('redis_version'),
                'used_memory_human': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            if hits + misses > 0:
                stats['hit_rate'] = round((hits / (hits + misses)) * 100, 2)
            else:
                stats['hit_rate'] = 0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": f"Error: {e}"}
    
    def clear_cache(self, pattern=None):
        """Clear cache (use with caution!)"""
        if not self.is_available():
            return False
        
        try:
            if pattern:
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"🗑️ Cleared {len(keys)} keys matching {pattern}")
                    return len(keys)
            else:
                self.redis_client.flushdb()
                logger.info("🗑️ Cleared entire cache database")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

# Global Redis client instance
redis_client = RedisClient()