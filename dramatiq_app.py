import dramatiq
import redis
import os
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from dotenv import load_dotenv

load_dotenv()

# Configure Redis broker
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_broker = RedisBroker(url=redis_url)

# Configure results backend
result_backend = RedisBackend(url=redis_url)
redis_broker.add_middleware(Results(backend=result_backend))

# Set the broker
dramatiq.set_broker(redis_broker)

# Export for easy importing
broker = redis_broker