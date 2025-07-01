import asyncio
from tts import generate_simple_tts
import tempfile
import os

async def test_tts():
    # Create test script
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp:
        temp.write("Hello world, this is a test message!")
        script_path = temp.name
    
    # Use absolute path and ensure directory exists
    output_dir = os.path.join(os.getcwd(), "static", "audio")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "test_output.mp3")
    
    print(f"Script path: {script_path}")
    print(f"Output path: {output_path}")
    print(f"Output dir exists: {os.path.exists(output_dir)}")
    
    try:
        result = await generate_simple_tts(script_path, output_path, "en-CA-LiamNeural", 1.0, 1)
        print(f"TTS Success: {result}")
        print(f"File exists: {os.path.exists(output_path)}")
        if os.path.exists(output_path):
            print(f"File size: {os.path.getsize(output_path)} bytes")
    except Exception as e:
        print(f"TTS Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        try:
            os.unlink(script_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
        except:
            pass

# Run test
asyncio.run(test_tts())