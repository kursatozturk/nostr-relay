from typing import TypeAlias

import redis.asyncio as aredis

CacherConnectionType: TypeAlias = aredis.Redis
