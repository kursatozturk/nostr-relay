import os

import redis.asyncio as aredis

from .typings import CacherConnectionType


def connect_to_redis() -> CacherConnectionType:
    host = os.getenv("redis_host", "")
    port = os.getenv("redis_port", "")
    return aredis.Redis(host=host, port=int(port), decode_responses=True)
