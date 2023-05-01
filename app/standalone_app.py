from contextlib import asynccontextmanager

from db.core import get_nostr_db_pool
from dotenv import load_dotenv
from fastapi import FastAPI
from ws import nostr


@asynccontextmanager
async def fastapi_lifespan(_: FastAPI):
    # load the .env to configure db connections
    load_dotenv("db/.env")
    # cache does not guarantee the race condition will not occur
    # get_nostr_db_pool()  # call it once to populate the cache
    #  so all of the calls will be fetching same pool connection
    yield
    # close the pool of connections
    # pool = get_nostr_db_pool()
    # pool.close()


app = FastAPI(lifespan=fastapi_lifespan)
app.include_router(nostr)
