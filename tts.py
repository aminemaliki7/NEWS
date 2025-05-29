import os
import time
import tempfile
import subprocess
from pydub import AudioSegment
from pydub.effects import low_pass_filter, speedup
from ssml_parser import parse_ssml_to_audio

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1, is_ssml=False):
    """
    Generate TTS audio from a script file.
    Supports SSML processing and audio effects.
    
    Args:
        script_file (str): Path to the text or SSML script file
        output_audio (str): Output .mp3 file path
        voice_id (str): Voice ID to use (compatible with edge-tts)
        speed (float): Playback speed factor
        depth (int): Depth effect level (1 = none)
        is_ssml (bool): If True, treat input as SSML

    Returns:
        str: Path to the generated audio file
    """
    print(f"Generating voice with {voice_id}, speed={speed}, depth={depth}, SSML={is_ssml}")

    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()

    temp_dir = os.path.join(tempfile.gettempdir(), "tts_generator")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        if is_ssml:
            # 🧠 Custom SSML parsing + synthesis with edge-tts
            audio = await parse_ssml_to_audio(content, voice_id)
            if audio:
                final_path = os.path.join(temp_dir, f"ssml_final_{int(time.time())}.mp3")
                audio.export(final_path, format="mp3", bitrate="192k")
                return final_path
            else:
                raise Exception("SSML parsing failed or returned no audio")

        # ✅ Standard text TTS using edge-tts Python API
        from edge_tts import Communicate
        base_audio_path = os.path.join(temp_dir, f"base_{int(time.time())}.mp3")
        communicate = Communicate(content.strip(), voice_id)

        if speed != 1.0:
            rate_pct = int((1.0 / speed) * 100)
            communicate.rate = f"{rate_pct}%"
            print(f"Set edge-tts rate to {rate_pct}%")

        await communicate.save(base_audio_path)

        if not os.path.exists(base_audio_path) or os.path.getsize(base_audio_path) == 0:
            raise Exception("Audio file generation failed")

        audio = AudioSegment.from_file(base_audio_path)

        # 🎚️ Extra speedup/slowdown for dramatic effect
        if speed < 0.8 or speed > 1.2:
            factor = 0.85 if speed < 0.8 else 1.15
            audio = speedup(audio, playback_speed=factor)
            print(f"Applied secondary speed factor: {factor}")

        # 🎚️ Depth filter
        if depth > 1:
            cutoff = 18000 - (depth * 3000)
            print(f"Applying low-pass filter at {cutoff}Hz")
            audio = low_pass_filter(audio, cutoff)

            bass_boost_db = (depth - 1) * 3
            if bass_boost_db > 0:
                print(f"Boosting bass +{bass_boost_db}dB")
                bass = audio.low_pass_filter(300) + bass_boost_db
                audio = audio.overlay(bass)

            fade = min(200, len(audio) // 20)
            audio = audio.fade_in(fade).fade_out(fade)

        final_path = os.path.join(temp_dir, f"final_{int(time.time())}.mp3")
        audio.export(final_path, format="mp3", bitrate="192k")
        return final_path

    except ImportError:
        print("Installing edge-tts...")
        subprocess.call(["pip", "install", "edge-tts"])
        return await generate_simple_tts(script_file, output_audio, voice_id, speed, depth, is_ssml)

    except Exception as e:
        print(f"TTS generation error: {e}")
        fallback_path = os.path.join(temp_dir, f"silent_{int(time.time())}.mp3")
        AudioSegment.silent(duration=3000).export(fallback_path, format="mp3")
        return fallback_path
