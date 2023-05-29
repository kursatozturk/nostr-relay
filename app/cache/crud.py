from collections import deque
from contextlib import asynccontextmanager
from typing import AsyncIterator, Sequence, TypedDict

from cache.core import get_redis_connection

from .typings import CacherConnectionType

async def delete_key(*keys: str) -> None:
    r = get_redis_connection()
    await r.delete(*keys)

async def add_vals_to_set(key: str, *val: str) -> None:
    r = get_redis_connection()
    added = await r.sadd(key, *val)
    while added < len(val):
        added += await r.sadd(key, *val[added:])


async def fetch_vals(name: str) -> Sequence[str]:
    r = get_redis_connection()
    cur, vals = await r.sscan(name=name)
    values: deque[str] = deque(vals)
    while cur:
        cur, _vals = await r.sscan(cursor=cur, name=name)
        values.extend(_vals)
    return values


class RedisResponse(TypedDict):
    type: str
    pattern: str | None
    channel: str
    data: str


@asynccontextmanager
async def listen_on_key(key: str, *, r_conn: CacherConnectionType | None = None) -> AsyncIterator[AsyncIterator[RedisResponse]]:
    r = r_conn or get_redis_connection()
    ps = r.pubsub()
    try:
        await ps.subscribe(key)
        yield ps.listen()
    finally:
        await ps.unsubscribe(key)
        await ps.close()


async def broadcast(key: str, value: str, *, r_conn: CacherConnectionType | None = None):
    r = r_conn or get_redis_connection()
    await r.publish(key, value)
