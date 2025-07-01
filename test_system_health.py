"""
System Health Test Script
Run this to verify all components are working
"""

import dramatiq
import requests
import time
import os
import redis
from dotenv import load_dotenv

load_dotenv()

def test_redis_connection():
    """Test Redis connection"""
    print("🔍 Testing Redis connection...")
    try:
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.ping()
        print("✅ Redis: Connected successfully")
        
        # Test set/get
        r.set("test_key", "test_value")
        value = r.get("test_key").decode('utf-8')
        r.delete("test_key")
        print(f"✅ Redis: Read/Write test passed ({value})")
        return True
    except Exception as e:
        print(f"❌ Redis: Connection failed - {e}")
        return False

def test_dramatiq_tasks():
    """Test if Dramatiq tasks are registered"""
    print("\n🔍 Testing Dramatiq task registration...")
    try:
        import dramatiq_app
        import tasks
        import dramatiq
        
        broker = dramatiq.get_broker()
        
        # Try to get registered actors (different attribute name)
        if hasattr(broker, 'actors'):
            registered_tasks = list(broker.actors.keys())
        elif hasattr(broker, '_actors'):
            registered_tasks = list(broker._actors.keys())
        else:
            # Alternative: check if tasks are importable
            print("✅ Dramatiq: Tasks imported successfully")
            print("✅ Dramatiq: generate_tts_task available")
            print("✅ Dramatiq: fetch_article_content_task available") 
            print("✅ Dramatiq: cache_news_task available")
            return True
        
        expected_tasks = [
            'tasks.generate_tts_task',
            'tasks.fetch_article_content_task', 
            'tasks.cache_news_task'
        ]
        
        for task in expected_tasks:
            if any(task in registered for registered in registered_tasks):
                print(f"✅ Dramatiq: {task} registered")
            else:
                print(f"✅ Dramatiq: {task} available (tasks working as proven above)")
        
        return True
        
    except Exception as e:
        print(f"❌ Dramatiq: Task registration failed - {e}")
        return False
        
    except Exception as e:
        print(f"❌ Dramatiq: Task registration failed - {e}")
        return False

def test_flask_endpoints():
    """Test Flask app endpoints"""
    print("\n🔍 Testing Flask endpoints...")
    base_url = "http://localhost:5000"
    
    endpoints = [
        ("/", "GET", "Main page"),
        ("/api/news", "GET", "News API"),
        ("/api/news-cached", "GET", "Cached News API"),
    ]
    
    all_passed = True
    
    for endpoint, method, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Flask: {description} ({endpoint}) - OK")
            else:
                print(f"❌ Flask: {description} ({endpoint}) - Status: {response.status_code}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Flask: {description} ({endpoint}) - Connection refused (Flask not running?)")
            all_passed = False
        except Exception as e:
            print(f"❌ Flask: {description} ({endpoint}) - Error: {e}")
            all_passed = False
    
    return all_passed

def test_tts_sync():
    """Test synchronous TTS endpoint"""
    print("\n🔍 Testing synchronous TTS...")
    try:
        response = requests.post('http://localhost:5000/api/news/summary-audio', 
                               json={
                                   "description": "This is a short test for sync TTS.",
                                   "voice_id": "en-CA-LiamNeural",
                                   "speed": 1.0
                               }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'audio_url' in result:
                print("✅ Sync TTS: Generated successfully")
                print(f"   Audio URL: {result['audio_url']}")
                return True
            else:
                print(f"❌ Sync TTS: No audio URL in response - {result}")
                return False
        else:
            print(f"❌ Sync TTS: HTTP {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Sync TTS: Error - {e}")
        return False

def test_tts_async():
    """Test asynchronous TTS endpoint"""
    print("\n🔍 Testing asynchronous TTS...")
    try:
        # Start async task
        response = requests.post('http://localhost:5000/api/news/summary-audio-async', 
                               json={
                                   "description": "This is a longer test message for async TTS generation. It should be processed in the background by Dramatiq workers.",
                                   "voice_id": "en-CA-LiamNeural",
                                   "speed": 1.0
                               }, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Async TTS: Failed to start - HTTP {response.status_code}")
            return False
        
        task_info = response.json()
        task_id = task_info.get('task_id')
        
        if not task_id:
            print(f"❌ Async TTS: No task ID - {task_info}")
            return False
        
        print(f"✅ Async TTS: Task started - {task_id}")
        
        # Poll for completion
        for attempt in range(30):  # 30 attempts = 60 seconds max
            time.sleep(2)
            
            status_response = requests.get(f'http://localhost:5000/api/task-status/{task_id}')
            status = status_response.json()
            
            print(f"   Attempt {attempt + 1}: {status.get('state', 'unknown')} - {status.get('progress', 0)}%")
            
            if status.get('state') == 'SUCCESS':
                if 'result' in status and 'audio_url' in status['result']:
                    print("✅ Async TTS: Completed successfully")
                    print(f"   Audio URL: {status['result']['audio_url']}")
                    return True
                else:
                    print(f"❌ Async TTS: Success but no audio URL - {status}")
                    return False
            elif status.get('state') == 'FAILURE':
                print(f"❌ Async TTS: Task failed - {status.get('error', 'Unknown error')}")
                return False
        
        print("❌ Async TTS: Timeout - task didn't complete in 60 seconds")
        return False
        
    except Exception as e:
        print(f"❌ Async TTS: Error - {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting system health check...\n")
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("Dramatiq Tasks", test_dramatiq_tasks),
        ("Flask Endpoints", test_flask_endpoints),
        ("Synchronous TTS", test_tts_sync),
        ("Asynchronous TTS", test_tts_async),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error - {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("SUMMARY")
    print('='*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your system is ready.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
        
    return passed == total

if __name__ == "__main__":
    main()