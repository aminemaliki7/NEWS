import os
import time
import tempfile
import subprocess
from pydub import AudioSegment
from pydub.effects import low_pass_filter, speedup, normalize, compress_dynamic_range

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Generate TTS audio from a script file using edge-tts.
    Includes enhancements like speed adjustment, bass depth, fade, normalization,
    dynamic compression, silence cleanup, and start padding to preserve first syllables.

    Args:
        script_file (str): Path to the input text script file
        output_audio (str): Path to the final MP3 output
        voice_id (str): Edge-TTS voice ID
        speed (float): Speed factor for the voice (1.0 = normal)
        depth (int): Depth effect level (1 = none, 2+ = more bass and filtering)

    Returns:
        str: Final path to generated audio file
    """
    print(f"Generating voice with {voice_id}, speed={speed}, depth={depth}")
    print(f"Output will be saved to: {output_audio}")

    # Read the content
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # Fix bad sentence endings (e.g., "selon")
    for bad_end in ['selon', 'according to', 'according']:
        if content.lower().endswith(bad_end):
            content = content.rsplit(' ', 1)[0] + '.'

    # Setup temp directories
    temp_dir = os.path.join(tempfile.gettempdir(), "tts_generator")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)

    try:
        from edge_tts import Communicate
        base_audio_path = os.path.join(temp_dir, f"base_{int(time.time())}.mp3")

        # Generate raw audio
        communicate = Communicate(content, voice_id)
        await communicate.save(base_audio_path)

        if not os.path.exists(base_audio_path) or os.path.getsize(base_audio_path) == 0:
            raise Exception("Base audio file generation failed")

        print(f"Base audio created: {base_audio_path} ({os.path.getsize(base_audio_path)} bytes)")
        audio = AudioSegment.from_file(base_audio_path)

        # Apply speed manually
        if speed != 1.0:
            print(f"Applying playback speed: {speed}")
            audio = speedup(audio, playback_speed=speed)

        # Apply depth effects
        if depth > 1:
            cutoff = 18000 - (depth * 3000)
            print(f"Applying low-pass filter at {cutoff}Hz")
            audio = low_pass_filter(audio, cutoff)

            bass_boost = (depth - 1) * 3
            if bass_boost > 0:
                print(f"Boosting bass +{bass_boost}dB")
                bass = audio.low_pass_filter(300) + bass_boost
                audio = audio.overlay(bass)

            fade = min(200, len(audio) // 20)
            audio = audio.fade_in(fade).fade_out(fade)

        # Enhance audio quality
        print("Normalizing volume")
        audio = normalize(audio)

        print("Applying dynamic range compression")
        audio = compress_dynamic_range(audio)

        print("Trimming silence")
        audio = audio.strip_silence(silence_len=200, silence_thresh=-40)

        # Add 300ms padding at start
        print("Adding 300ms silence at the beginning")
        padding_start = AudioSegment.silent(duration=300)
        audio = padding_start + audio

        # Export final file
        print(f"Exporting final audio to: {output_audio}")
        audio.export(output_audio, format="mp3", bitrate="192k")

        if not os.path.exists(output_audio) or os.path.getsize(output_audio) == 0:
            raise Exception("Final audio file is empty")

        print(f"✅ Final audio created: {output_audio} ({os.path.getsize(output_audio)} bytes)")

        # Clean up
        try:
            os.remove(base_audio_path)
            print(f"Temp file removed: {base_audio_path}")
        except Exception as e:
            print(f"Warning: Temp cleanup failed: {e}")

        return output_audio

    except ImportError:
        print("Installing edge-tts...")
        subprocess.call(["pip", "install", "edge-tts"])
        return await generate_simple_tts(script_file, output_audio, voice_id, speed, depth)

    except Exception as e:
        print(f"❌ TTS generation error: {e}")
        try:
            print(f"Creating fallback silent audio: {output_audio}")
            AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
            return output_audio
        except Exception as fallback_error:
            print(f"Fallback audio failed: {fallback_error}")
            raise e
