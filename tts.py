import os
import time
import tempfile
import shutil
from io import BytesIO
from edge_tts import Communicate
from pydub import AudioSegment

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Optimized file-based TTS generation using edge-tts.
    Adds silence at the beginning for cleaner start.
    """
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    for bad_end in ['according to', 'selon']:
        if content.lower().endswith(bad_end):
            content = content.rsplit(' ', 1)[0] + '.'

    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    temp_path = os.path.join(tempfile.gettempdir(), f"base_{int(time.time())}.mp3")

    try:
        communicate = Communicate(content, voice_id)
        await communicate.save(temp_path)

        # Add 500ms silence before playback
        audio = AudioSegment.silent(duration=500) + AudioSegment.from_file(temp_path)
        audio.export(output_audio, format="mp3", bitrate="192k")
        os.remove(temp_path)
        return output_audio

    except Exception as e:
        print(f"TTS Error: {e}")
        AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
        return output_audio


async def generate_simple_tts_in_memory(text, voice_id, speed=1.0, depth=1):
    """
    Optimized in-memory TTS generation using edge-tts.
    Adds 500ms silence at the start.
    Returns MP3 as BytesIO buffer.
    """
    rate = f"{int((speed - 1) * 100)}%" if speed != 1.0 else "0%"
    communicate = Communicate(
        text=text,
        voice=voice_id,
        rate=rate,
        volume="+0%"
    )

    raw_audio = BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            raw_audio.write(chunk["data"])
    raw_audio.seek(0)

    # Add 500ms silence at start
    tts_audio = AudioSegment.from_file(raw_audio, format="mp3")
    final_audio = AudioSegment.silent(duration=500) + tts_audio

    output_buffer = BytesIO()
    final_audio.export(output_buffer, format="mp3", bitrate="192k")
    output_buffer.seek(0)
    return output_buffer
