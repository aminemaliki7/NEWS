# tasks.py
import asyncio
import os
from celery_app import celery
from tts import generate_simple_tts

@celery.task(bind=True)
def generate_tts_task(self, script_path, output_path, voice_id, speed=1.0, depth=1):
    """
    Celery task to generate TTS audio using edge-tts.
    Runs asynchronously inside an event loop.
    """
    try:
        # Ensure output folder exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_simple_tts(script_path, output_path, voice_id, speed, depth))

        return output_path
    except Exception as e:
        self.retry(exc=e, countdown=5, max_retries=3)
        raise
