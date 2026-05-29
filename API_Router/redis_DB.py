import redis.asyncio as redis
import os

adres_redis = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

baza_redis = redis.from_url(
    adres_redis,
    encoding="utf-8",
    decode_responses=True,
    socket_timeout=2.0
)