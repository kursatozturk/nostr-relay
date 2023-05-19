import os

import redis.asyncio as aredis
from functools import cache


@cache
def connect_to_redis() -> aredis.Redis:
    host = os.getenv("redis_host", "")
    port = os.getenv("redis_port", "")
    return aredis.Redis(host=host, port=int(port), decode_responses=True)
