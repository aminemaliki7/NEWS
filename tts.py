import os
import time
import tempfile
import shutil
from io import BytesIO
from edge_tts import Communicate
from pydub import AudioSegment

# Try to import Redis client, fallback gracefully if not available
try:
    from redis_client import redis_client
    REDIS_AVAILABLE = True
except ImportError:
    print("[TTS] Redis client not available, running without cache")
    REDIS_AVAILABLE = False
    redis_client = None

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Optimized file-based TTS generation using edge-tts.
    Adds silence at the beginning for cleaner start.
    NOW WITH REDIS CACHING! 🚀
    """
    
    # Read the script content
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Clean up bad endings
    for bad_end in ['according to', 'selon']:
        if content.lower().endswith(bad_end):
            content = content.rsplit(' ', 1)[0] + '.'
    
    # 🚀 CHECK CACHE FIRST (if Redis available)
    if REDIS_AVAILABLE:
        cached_audio_path = redis_client.get_cached_tts_audio_path(content, voice_id, speed)
        if cached_audio_path and os.path.exists(cached_audio_path):
            # Copy cached file to output location
            try:
                shutil.copy2(cached_audio_path, output_audio)
                print(f"[TTS] 🎯 Cache HIT: Using cached audio for {voice_id}")
                return output_audio
            except Exception as e:
                print(f"[TTS] Error copying cached file: {e}")
                # Continue to generate new audio
    
    print(f"[TTS] ❌ Cache MISS: Generating new audio for {voice_id}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    
    # Create temporary file for edge-tts output
    temp_path = os.path.join(tempfile.gettempdir(), f"base_{int(time.time())}.mp3")
    
    try:
        # Generate TTS audio
        communicate = Communicate(content, voice_id)
        await communicate.save(temp_path)
        
        # Add 500ms silence before playback
        audio = AudioSegment.silent(duration=500) + AudioSegment.from_file(temp_path)
        audio.export(output_audio, format="mp3", bitrate="192k")
        
        # Clean up temp file
        os.remove(temp_path)
        
        # 💾 CACHE THE RESULT (if Redis available)
        if REDIS_AVAILABLE:
            redis_client.cache_tts_audio_path(content, voice_id, speed, output_audio)
        
        print(f"[TTS] ✅ Generated and cached audio: {output_audio}")
        return output_audio
        
    except Exception as e:
        print(f"TTS Error: {e}")
        # Generate silent audio as fallback
        AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
        return output_audio

async def generate_simple_tts_in_memory(text, voice_id, speed=1.0, depth=1):
    """
    Optimized in-memory TTS generation using edge-tts.
    Adds 500ms silence at the start.
    Returns MP3 as BytesIO buffer.
    NOW WITH REDIS CACHING! 🚀
    """
    
    # Clean up bad endings
    for bad_end in ['according to', 'selon']:
        if text.lower().endswith(bad_end):
            text = text.rsplit(' ', 1)[0] + '.'
    
    # 🚀 CHECK CACHE FIRST (if Redis available)
    if REDIS_AVAILABLE:
        cached_audio_path = redis_client.get_cached_tts_audio_path(text, voice_id, speed)
        if cached_audio_path and os.path.exists(cached_audio_path):
            try:
                # Load cached file into memory
                with open(cached_audio_path, 'rb') as f:
                    audio_data = f.read()
                
                output_buffer = BytesIO(audio_data)
                output_buffer.seek(0)
                
                print(f"[TTS] 🎯 In-memory cache HIT: Using cached audio for {voice_id}")
                return output_buffer
            except Exception as e:
                print(f"[TTS] Error loading cached file: {e}")
                # Continue to generate new audio
    
    print(f"[TTS] ❌ In-memory cache MISS: Generating new audio for {voice_id}")
    
    try:
        # Configure speech rate
        rate = f"{int((speed - 1) * 100)}%" if speed != 1.0 else "0%"
        
        # Generate TTS audio
        communicate = Communicate(
            text=text,
            voice=voice_id,
            rate=rate,
            volume="+0%"
        )
        
        # Stream audio data
        raw_audio = BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                raw_audio.write(chunk["data"])
        raw_audio.seek(0)
        
        # Add 500ms silence at start
        tts_audio = AudioSegment.from_file(raw_audio, format="mp3")
        final_audio = AudioSegment.silent(duration=500) + tts_audio
        
        # Export to buffer
        output_buffer = BytesIO()
        final_audio.export(output_buffer, format="mp3", bitrate="192k")
        output_buffer.seek(0)
        
        # 💾 CACHE THE RESULT (if Redis available)
        # For in-memory generation, we can save to a temp file for caching
        if REDIS_AVAILABLE:
            try:
                # Create a temporary file to cache the audio
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
                
                # Reset buffer position
                output_buffer.seek(0)
                
                print(f"[TTS] ✅ Generated and cached in-memory audio")
            except Exception as e:
                print(f"[TTS] Warning: Could not cache in-memory audio: {e}")
        
        return output_buffer
        
    except Exception as e:
        print(f"TTS In-Memory Error: {e}")
        # Return silent audio as fallback
        silent_audio = AudioSegment.silent(duration=3000)
        output_buffer = BytesIO()
        silent_audio.export(output_buffer, format="mp3")
        output_buffer.seek(0)
        return output_buffer