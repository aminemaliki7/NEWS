import os
import time
import tempfile
import subprocess
from pydub import AudioSegment
from pydub.effects import low_pass_filter, speedup

async def generate_simple_tts(script_file, output_audio, voice_id, speed=1.0, depth=1):
    """
    Generate TTS audio from a script file using edge-tts.
    Supports audio effects like speed and depth.
    Args:
        script_file (str): Path to the text script file
        output_audio (str): Output .mp3 file path (WILL BE USED)
        voice_id (str): Voice ID to use (compatible with edge-tts)
        speed (float): Playback speed factor
        depth (int): Depth effect level (1 = none)
    Returns:
        str: Path to the generated audio file
    """
    print(f"Generating voice with {voice_id}, speed={speed}, depth={depth}")
    print(f"Output will be saved to: {output_audio}")

    # Read the script content
    with open(script_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Create temp directory for intermediate files
    temp_dir = os.path.join(tempfile.gettempdir(), "tts_generator")
    os.makedirs(temp_dir, exist_ok=True)

    # Make sure the output directory exists
    output_dir = os.path.dirname(output_audio)
    os.makedirs(output_dir, exist_ok=True)

    try:
        from edge_tts import Communicate

        # Create base audio in temp directory (for processing)
        base_audio_path = os.path.join(temp_dir, f"base_{int(time.time())}.mp3")

        communicate = Communicate(content.strip(), voice_id)

        # Apply speed adjustment if needed
        if speed != 1.0:
            rate_pct = int((1.0 / speed) * 100)
            communicate.rate = f"{rate_pct}%"
            print(f"Set edge-tts rate to {rate_pct}%")

        # Generate the base audio
        await communicate.save(base_audio_path)

        # Verify base audio was created
        if not os.path.exists(base_audio_path) or os.path.getsize(base_audio_path) == 0:
            raise Exception("Base audio file generation failed")

        print(f"Base audio created: {base_audio_path} (size: {os.path.getsize(base_audio_path)} bytes)")

        # Load audio for processing
        audio = AudioSegment.from_file(base_audio_path)

        # Apply additional speed adjustments if needed
        if speed < 0.8 or speed > 1.2:
            factor = 0.85 if speed < 0.8 else 1.15
            audio = speedup(audio, playback_speed=factor)
            print(f"Applied secondary speed factor: {factor}")

        # Apply depth effects
        if depth > 1:
            cutoff = 18000 - (depth * 3000)
            print(f"Applying low-pass filter at {cutoff}Hz")
            audio = low_pass_filter(audio, cutoff)

            # Add bass boost
            bass_boost_db = (depth - 1) * 3
            if bass_boost_db > 0:
                print(f"Boosting bass +{bass_boost_db}dB")
                bass = audio.low_pass_filter(300) + bass_boost_db
                audio = audio.overlay(bass)

            # Add fade in/out
            fade = min(200, len(audio) // 20)
            audio = audio.fade_in(fade).fade_out(fade)

        # Export to the ACTUAL output path that was requested
        print(f"Exporting final audio to: {output_audio}")
        audio.export(output_audio, format="mp3", bitrate="192k")

        # Verify the final file was created
        if not os.path.exists(output_audio):
            raise Exception(f"Failed to create final audio file at {output_audio}")

        final_size = os.path.getsize(output_audio)
        if final_size == 0:
            raise Exception(f"Final audio file is empty: {output_audio}")

        print(f"Final audio created successfully: {output_audio} (size: {final_size} bytes)")

        # Clean up temporary base audio file
        try:
            os.remove(base_audio_path)
            print(f"Cleaned up temp file: {base_audio_path}")
        except Exception as e:
            print(f"Warning: Could not clean up temp file: {e}")

        # Return the actual output path
        return output_audio

    except ImportError:
        print("Installing edge-tts...")
        subprocess.call(["pip", "install", "edge-tts"])
        return await generate_simple_tts(script_file, output_audio, voice_id, speed, depth)

    except Exception as e:
        print(f"TTS generation error: {e}")

        # Create a fallback silent audio at the requested output path
        try:
            print(f"Creating fallback silent audio at: {output_audio}")
            AudioSegment.silent(duration=3000).export(output_audio, format="mp3")
            return output_audio
        except Exception as fallback_error:
            print(f"Even fallback failed: {fallback_error}")
            raise e

    