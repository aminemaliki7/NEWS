import os
import time
import tempfile
from edge_tts import Communicate
from pydub import AudioSegment

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Fast TTS generation using edge-tts and pydub.

    Only reads the script and saves the MP3 without extra processing.
    """
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Minimal fix for bad endings
    for bad_end in ['according to', 'selon']:
        if content.lower().endswith(bad_end):
            content = content.rsplit(' ', 1)[0] + '.'

    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    temp_path = os.path.join(tempfile.gettempdir(), f"base_{int(time.time())}.mp3")

    try:
        # Generate MP3 using edge-tts
        communicate = Communicate(content, voice_id)
        await communicate.save(temp_path)

        # Just copy it to the output
        audio = AudioSegment.from_file(temp_path)
        audio.export(output_audio, format="mp3", bitrate="192k")

        os.remove(temp_path)
        return output_audio

    except Exception as e:
        # On failure, return silent 3s fallback
        print(f"TTS Error: {e}")
        AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
        return output_audio
