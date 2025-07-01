import requests
import time

# Test with a very simple text first
response = requests.post('http://localhost:5000/api/news/summary-audio-async', 
                        json={
                            "description": "Hello world test",
                            "voice_id": "en-CA-LiamNeural",
                            "speed": 1.0
                        })

if response.status_code == 200:
    task_info = response.json()
    task_id = task_info['task_id']
    print(f"✅ Task started: {task_id}")
    
    # Check status more frequently
    for i in range(60):  # Wait up to 60 seconds
        status_response = requests.get(f'http://localhost:5000/api/task-status/{task_id}')
        status = status_response.json()
        
        print(f"[{i+1:2d}] State: {status['state']:10} | Progress: {status.get('progress', 0):3d}% | Message: {status.get('message', 'N/A')}")
        
        if status['state'] == 'SUCCESS':
            print(f"✅ SUCCESS! Audio: {status['result']['audio_url']}")
            break
        elif status['state'] == 'FAILURE':
            print(f"❌ FAILURE! Error: {status.get('error')}")
            break
        
        time.sleep(2)  # Check every 2 seconds
else:
    print(f"❌ Request failed: {response.text}")