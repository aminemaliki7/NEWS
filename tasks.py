# Import this FIRST to set up the broker
import dramatiq_app

import dramatiq
import asyncio
import os
import redis
import json
import tempfile
import time
from tts import generate_simple_tts
from gnews_client import GNewsClient

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@dramatiq.actor(store_results=True, max_retries=3)
def generate_tts_task(text, voice_id, speed=1.0, depth=1, task_id=None):
    """Background TTS generation task"""
    try:
        print(f"=== TTS TASK STARTED ===")
        print(f"Task ID: {task_id}")
        print(f"Text: '{text[:50]}...'")
        print(f"Voice ID: {voice_id}")
        
        # Clean up text
        import re
        text = re.sub(r'<[^>]*?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        if not text:
            raise ValueError("Empty text after cleaning")
        
        # Create temporary file for script
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp:
            temp.write(text)
            script_path = temp.name
        
        print(f"Created temp script: {script_path}")
        
        # Generate filename and ensure static/audio exists
        filename = f"tts_{task_id or int(time.time())}.mp3"
        output_dir = os.path.join(os.getcwd(), "static", "audio")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)
        
        print(f"Output path: {output_path}")
        
        # Run the async TTS function
        def run_tts():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    generate_simple_tts(script_path, output_path, voice_id, speed, depth)
                )
            finally:
                loop.close()
        
        result = run_tts()
        print(f"TTS completed: {result}")
        
        # Clean up temp file
        try:
            os.unlink(script_path)
        except:
            pass
        
        # Check if file was created
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Audio file was not created at {output_path}")
        
        file_size = os.path.getsize(output_path)
        print(f"Generated audio file: {filename}, size: {file_size} bytes")
        
        result_data = {
            'status': 'completed',
            'audio_path': output_path,
            'filename': filename,
            'audio_url': f"/static/audio/{filename}",
            'file_size': file_size
        }
        
        # Cache result in Redis
        if task_id:
            cache_key = f"tts:{task_id}"
            redis_client.setex(cache_key, 21600, json.dumps(result_data))
        
        return result_data
        
    except Exception as e:
        error_msg = str(e)
        print(f"TTS Task Error: {error_msg}")
        import traceback
        traceback.print_exc()
        raise

@dramatiq.actor(store_results=True)
def fetch_article_content_task(url):
    """Background article content fetching"""
    try:
        # Check cache first
        cache_key = f"article:{hash(url)}"
        cached_content = redis_client.get(cache_key)
        
        if cached_content:
            return json.loads(cached_content)
        
        # Fetch content
        gnews_client = GNewsClient()
        content = gnews_client.fetch_article_content(url)
        
        # Cache for 1 hour
        redis_client.setex(cache_key, 21600, json.dumps(content))
        
        return content
        
    except Exception as e:
        error_msg = str(e)
        print(f"Article fetch error: {error_msg}")
        raise

@dramatiq.actor(store_results=True)
def cache_news_task(category='general', language='en'):
    """Background news caching task"""
    try:
        cache_key = f"news:{category}:{language}"
        
        # Fetch fresh news
        gnews_client = GNewsClient()
        results = gnews_client.get_top_headlines(category=category, language=language)
        
        # Cache for 15 minutes
        redis_client.setex(cache_key, 21600, json.dumps(results))
        
        return {
            'status': 'cached',
            'category': category,
            'language': language,
            'articles_count': len(results.get('articles', []))
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"News cache error: {error_msg}")
        raise