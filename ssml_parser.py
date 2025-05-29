import re
from xml.etree import ElementTree as ET
from pydub import AudioSegment
import asyncio
import os
import tempfile
from edge_tts import Communicate

async def synthesize_fragment(text, voice_id="en-US-GuyNeural"):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"frag_{abs(hash(text))}.mp3")
    communicate = Communicate(text.strip(), voice_id)
    await communicate.save(file_path)
    return AudioSegment.from_file(file_path)

def parse_time_to_ms(time_str):
    if time_str.endswith("ms"):
        return int(time_str[:-2])
    elif time_str.endswith("s"):
        return int(float(time_str[:-1]) * 1000)
    return 0

async def parse_ssml_to_audio(ssml_content, voice_id="en-US-GuyNeural"):
    audio_segments = []

    try:
        root = ET.fromstring(ssml_content)
        assert root.tag == "speak"
    except ET.ParseError:
        print("Invalid SSML")
        return None

    async def process_element(elem):
        if elem.tag == "break":
            duration = parse_time_to_ms(elem.attrib.get("time", "500ms"))
            return AudioSegment.silent(duration=duration)

        elif elem.tag == "prosody":
            rate = elem.attrib.get("rate", "medium")
            inner_text = ''.join(elem.itertext()).strip()
            speed = {
                "x-slow": 0.6,
                "slow": 0.8,
                "medium": 1.0,
                "fast": 1.2,
                "x-fast": 1.5
            }.get(rate, 1.0)
            audio = await synthesize_fragment(inner_text, voice_id)
            if speed != 1.0:
                audio = audio._spawn(audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed)}).set_frame_rate(audio.frame_rate)
            return audio

        elif elem.tag in {"emphasis", "say-as"}:
            text = ''.join(elem.itertext()).strip()
            return await synthesize_fragment(text, voice_id)

        else:
            text = ''.join(elem.itertext()).strip()
            return await synthesize_fragment(text, voice_id)

    for node in root:
        seg = await process_element(node)
        if seg:
            audio_segments.append(seg)

    return sum(audio_segments) if audio_segments else None