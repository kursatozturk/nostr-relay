import os
from functools import cache

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool, ConnectionPool


def __get_db_pool(
    *, user: str, host: str, password: str, db_name: str, app_name: str = "nostr-relay"
):
    """
    Creates a pool connection and returns it with the given credentials
    """
    conninfo = (
        f'postgresql://{user}:{password}@{host}/{db_name}?application_name="{app_name}"'
    )
    return AsyncConnectionPool(conninfo=conninfo)


@cache
def get_nostr_db_pool():
    """
    Returns the connection pool
    It caches the pool object to not to initiate
    multiple connection pool to the postgresql server;
    But accomplishing to not relying on a global state.
    If pool needs to re-initiate, please use get_db_pool.cache_clear()
    """
    return __get_db_pool(
        user=os.getenv("user"),
        host=os.getenv("host"),
        password=os.getenv("password"),
        db_name=os.getenv("db"),
    )


async def _get_async_connection():
    """
    Use with caution!
    This is intended for one time running background tasks. Do not use it
    in API functions!
    """
    user = os.getenv("user")
    host = os.getenv("host")
    password = os.getenv("password")
    db_name = os.getenv("db")
    app_name = "nostr-relay"
    return await AsyncConnection.connect(
        f'postgresql://{user}:{password}@{host}/{db_name}?application_name="{app_name}"',
    )


async def close_pool():
    cached_pool = get_nostr_db_pool()
    get_nostr_db_pool.cache_clear()
    await cached_pool.close()
