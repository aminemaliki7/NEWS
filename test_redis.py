import redis
import os
from dotenv import load_dotenv

load_dotenv()

try:
    r = redis.from_url('redis://localhost:6379/0')
    r.ping()
    print("✅ Redis connection successful!")
    
    # Test set/get
    r.set("test_key", "Hello Redis!")
    value = r.get("test_key").decode('utf-8')
    print(f"✅ Test value: {value}")
    
    # Test expiration
    r.setex("temp_key", 10, "This expires in 10 seconds")
    print("✅ Set expiring key")
    
except redis.ConnectionError:
    print("❌ Redis connection failed!")
except Exception as e:
    print(f"❌ Error: {e}")