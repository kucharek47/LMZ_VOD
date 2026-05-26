import os
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_port = int(os.getenv("REDIS_PORT", 6379))

redis_db = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)