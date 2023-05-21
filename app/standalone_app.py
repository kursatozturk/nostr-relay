from asyncio import sleep
from contextlib import asynccontextmanager
from cache.core import get_redis_connection

from db.core import connect_db_pool
from dotenv import load_dotenv
from fastapi import FastAPI
from ws import nostr


@asynccontextmanager
async def fastapi_lifespan(app: FastAPI):
    # load the .env to configure db connections
    load_dotenv("db/.env")
    load_dotenv("cache/.env")
    # cache does not guarantee the race condition will not occur
    connect_db_pool()  # call it once to populate the cache
    get_redis_connection()
    #  so all of the calls will be fetching same pool connection
    yield
    # close the pool of connections
    # print("WHAT!")
    # pool = connect_db_pool()
    # Somehow, async_asgi_client.TestClient closes the event loop
    # before FastApi websocket endpoint to clean up
    await sleep(2)
    # await pool.close()


app = FastAPI(lifespan=fastapi_lifespan)
app.include_router(nostr)
