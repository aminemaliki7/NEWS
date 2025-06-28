import os
import time
import tempfile
import shutil
import asyncio
from io import BytesIO
from edge_tts import Communicate
from pydub import AudioSegment
import aiofiles
from concurrent.futures import ThreadPoolExecutor

# Try to import Redis client, fallback gracefully if not available
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    print("[TTS] Redis client not available, running without cache")
    REDIS_AVAILABLE = False
    redis_client = None

# ==================== CONCURRENCY CONTROL ====================
# Limit concurrent TTS generations to prevent resource exhaustion
TTS_SEMAPHORE = asyncio.Semaphore(3)  # Max 3 simultaneous TTS generations
AUDIO_PROCESSING_EXECUTOR = ThreadPoolExecutor(max_workers=2)  # Dedicated thread pool for audio processing

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Fully optimized async TTS generation with proper concurrency control.
    🚀 ASYNC + THREADING + CACHING + SEMAPHORE PROTECTION
    """
    
    # 🚧 CONCURRENCY CONTROL: Limit simultaneous TTS generations
    async with TTS_SEMAPHORE:
        return await _generate_tts_internal(script_file, output_audio, voice_id, speed, depth)

async def _generate_tts_internal(script_file, output_audio, voice_id, speed, depth):
    """Internal TTS generation with full async support"""
    
    # 📖 READ FILE ASYNC (non-blocking)
    async with aiofiles.open(script_file, 'r', encoding='utf-8') as f:
        content = await f.read()
        content = content.strip()
    
    # Clean up bad endings
    for bad_end in ['according to', 'selon']:
        if content.lower().endswith(bad_end):
            content = content.rsplit(' ', 1)[0] + '.'
    
    # 🚀 CHECK CACHE FIRST (if Redis available)
    if REDIS_AVAILABLE:
        # Make cache check async
        cached_audio_path = await asyncio.get_event_loop().run_in_executor(
            None, redis_client.get_cached_tts_audio_path, content, voice_id, speed
        )
        
        if cached_audio_path and os.path.exists(cached_audio_path):
            try:
                # ASYNC FILE COPY
                await asyncio.get_event_loop().run_in_executor(
                    None, shutil.copy2, cached_audio_path, output_audio
                )
                print(f"[TTS] 🎯 Cache HIT: Using cached audio for {voice_id}")
                return output_audio
            except Exception as e:
                print(f"[TTS] Error copying cached file: {e}")
    
    print(f"[TTS] ❌ Cache MISS: Generating new audio for {voice_id}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    
    # Create temporary file for edge-tts output
    temp_path = os.path.join(tempfile.gettempdir(), f"base_{int(time.time())}_{os.getpid()}.mp3")
    
    try:
        # ✅ ASYNC TTS GENERATION (already properly async)
        communicate = Communicate(content, voice_id)
        await communicate.save(temp_path)
        
        # 🎵 ASYNC AUDIO PROCESSING (move CPU-intensive work to thread pool)
        final_audio_path = await _process_audio_async(temp_path, output_audio)
        
        # 🗑️ ASYNC CLEANUP
        await asyncio.get_event_loop().run_in_executor(None, os.remove, temp_path)
        
        # 💾 ASYNC CACHE THE RESULT (if Redis available)
        if REDIS_AVAILABLE:
            await asyncio.get_event_loop().run_in_executor(
                None, redis_client.cache_tts_audio_path, content, voice_id, speed, output_audio
            )
        
        print(f"[TTS] ✅ Generated and cached audio: {output_audio}")
        return output_audio
        
    except Exception as e:
        print(f"TTS Error: {e}")
        # Generate silent audio as fallback (also async)
        await _generate_silent_fallback_async(output_audio)
        return output_audio

async def _process_audio_async(temp_path, output_audio):
    """
    Process audio in a separate thread to avoid blocking the event loop.
    This is the key optimization! 🚀
    """
    def _audio_processing_task():
        # CPU-intensive work runs in thread pool
        audio = AudioSegment.silent(duration=500) + AudioSegment.from_file(temp_path)
        audio.export(output_audio, format="mp3", bitrate="192k")
        return output_audio
    
    # Execute CPU-intensive audio processing in dedicated thread pool
    return await asyncio.get_event_loop().run_in_executor(
        AUDIO_PROCESSING_EXECUTOR, _audio_processing_task
    )

async def _generate_silent_fallback_async(output_audio):
    """Generate silent audio fallback asynchronously"""
    def _silent_task():
        AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
    
    await asyncio.get_event_loop().run_in_executor(
        AUDIO_PROCESSING_EXECUTOR, _silent_task
    )

async def generate_simple_tts_in_memory(text, voice_id, speed=1.0, depth=1):
    """
    Fully optimized in-memory TTS generation with proper async support.
    🚀 ASYNC + THREADING + CACHING + SEMAPHORE PROTECTION
    """
    
    # 🚧 CONCURRENCY CONTROL: Limit simultaneous TTS generations
    async with TTS_SEMAPHORE:
        return await _generate_tts_in_memory_internal(text, voice_id, speed, depth)

async def _generate_tts_in_memory_internal(text, voice_id, speed, depth):
    """Internal in-memory TTS generation with full async support"""
    
    # Clean up bad endings
    for bad_end in ['according to', 'selon']:
        if text.lower().endswith(bad_end):
            text = text.rsplit(' ', 1)[0] + '.'
    
    # 🚀 ASYNC CACHE CHECK
    if REDIS_AVAILABLE:
        cached_audio_path = await asyncio.get_event_loop().run_in_executor(
            None, redis_client.get_cached_tts_audio_path, text, voice_id, speed
        )
        
        if cached_audio_path and os.path.exists(cached_audio_path):
            try:
                # ASYNC FILE READ
                async with aiofiles.open(cached_audio_path, 'rb') as f:
                    audio_data = await f.read()
                
                output_buffer = BytesIO(audio_data)
                output_buffer.seek(0)
                
                print(f"[TTS] 🎯 In-memory cache HIT: Using cached audio for {voice_id}")
                return output_buffer
            except Exception as e:
                print(f"[TTS] Error loading cached file: {e}")
    
    print(f"[TTS] ❌ In-memory cache MISS: Generating new audio for {voice_id}")
    
    try:
        # Configure speech rate
        rate = f"{int((speed - 1) * 100)}%" if speed != 1.0 else "0%"
        
        # ✅ ASYNC TTS GENERATION
        communicate = Communicate(
            text=text,
            voice=voice_id,
            rate=rate,
            volume="+0%"
        )
        
        # Stream audio data (already async)
        raw_audio = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                raw_audio.write(chunk["data"])
        raw_audio.seek(0)
        
        # 🎵 ASYNC AUDIO PROCESSING
        output_buffer = await _process_audio_in_memory_async(raw_audio)
        
        # 💾 ASYNC CACHE THE RESULT
        if REDIS_AVAILABLE:
            await _cache_in_memory_audio_async(output_buffer, text, voice_id, speed)
        
        return output_buffer
        
    except Exception as e:
        print(f"TTS In-Memory Error: {e}")
        # Return silent audio as fallback (async)
        return await _generate_silent_buffer_async()

async def _process_audio_in_memory_async(raw_audio):
    """Process audio in memory using thread pool"""
    def _audio_task():
        # CPU-intensive work in thread pool
        tts_audio = AudioSegment.from_file(raw_audio, format="mp3")
        final_audio = AudioSegment.silent(duration=500) + tts_audio
        
        output_buffer = BytesIO()
        final_audio.export(output_buffer, format="mp3", bitrate="192k")
        output_buffer.seek(0)
        return output_buffer
    
    return await asyncio.get_event_loop().run_in_executor(
        AUDIO_PROCESSING_EXECUTOR, _audio_task
    )

async def _cache_in_memory_audio_async(output_buffer, text, voice_id, speed):
    """Cache in-memory audio asynchronously"""
    def _cache_task():
        try:
            cache_dir = os.path.join(tempfile.gettempdir(), "tts_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            cache_filename = f"tts_{int(time.time())}_{hash(text + voice_id + str(speed)) % 1000000}.mp3"
            cache_path = os.path.join(cache_dir, cache_filename)
            
            # Save audio to cache file
            with open(cache_path, 'wb') as f:
                output_buffer.seek(0)
                f.write(output_buffer.read())
            
            # Cache the file path
            redis_client.cache_tts_audio_path(text, voice_id, speed, cache_path)
            output_buffer.seek(0)  # Reset position
            
            print(f"[TTS] ✅ Generated and cached in-memory audio")
        except Exception as e:
            print(f"[TTS] Warning: Could not cache in-memory audio: {e}")
    
    await asyncio.get_event_loop().run_in_executor(None, _cache_task)

async def _generate_silent_buffer_async():
    """Generate silent audio buffer asynchronously"""
    def _silent_task():
        silent_audio = AudioSegment.silent(duration=3000)
        output_buffer = BytesIO()
        silent_audio.export(output_buffer, format="mp3")
        output_buffer.seek(0)
        return output_buffer
    
    return await asyncio.get_event_loop().run_in_executor(
        AUDIO_PROCESSING_EXECUTOR, _silent_task
    )

# ==================== MONITORING AND STATS ====================
def get_tts_stats():
    """Get current TTS performance statistics"""
    return {
        "active_generations": TTS_SEMAPHORE._value,
        "max_concurrent": 3,
        "audio_processing_threads": AUDIO_PROCESSING_EXECUTOR._threads,
        "redis_available": REDIS_AVAILABLE
    }

# ==================== GRACEFUL SHUTDOWN ====================
async def shutdown_tts_service():
    """Gracefully shutdown TTS service"""
    print("[TTS] Shutting down audio processing threads...")
    AUDIO_PROCESSING_EXECUTOR.shutdown(wait=True)
    print("[TTS] TTS service shutdown complete")

if __name__ == "__main__":
    print("🚀 Optimized Async TTS Module Loaded!")
    print(f"📊 Max concurrent TTS: {3}")
    print(f"🧵 Audio processing threads: {AUDIO_PROCESSING_EXECUTOR._max_workers}")
    print(f"💾 Redis caching: {'✅ Available' if REDIS_AVAILABLE else '❌ Disabled'}")