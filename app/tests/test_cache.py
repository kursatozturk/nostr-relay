from asyncio import ALL_COMPLETED, create_task, wait

import pytest
import pytest_asyncio
from cache.core import get_redis_connection
from utils.tools import flat_list
from cache.crud import add_vals_to_set, broadcast, fetch_vals, listen_on_key
from asyncio.locks import Barrier


@pytest.mark.asyncio
async def test_caching() -> None:
    key = "test-key"
    vals: list[int | str] = [1, 2, 3, 4, "test-1", "test-2"]
    str_vals = set(map(str, vals))
    await add_vals_to_set(key, *vals)
    ret_vals = await fetch_vals(key)
    assert not str_vals.difference(ret_vals), "Returned Values Are Different!"


@pytest_asyncio.fixture
async def cacher_connector():
    try:
        r = get_redis_connection()
        yield r
    finally:
        await r.close()


@pytest.mark.asyncio
async def test_pubsub(cacher_connector) -> None:
    exit_signal = "exit"
    key_count = 10
    listener_per_key = 50
    listener_barrier = Barrier(
        key_count * listener_per_key + 1  # + 1 is for this function
    )  #                                    to continue creating producers

    async def broadcaster_task(key: str) -> set[str]:
        r_conn = get_redis_connection()
        vals = set(map(str, [1, 2, 3, 4, "test-1", "test-2"]))
        for val in vals:
            await broadcast(key, val, r_conn=r_conn)
        await broadcast(key, exit_signal, r_conn=r_conn)
        return vals

    async def listener_task(key: str) -> set[str]:
        r_conn = get_redis_connection()
        async with listen_on_key(key, r_conn=r_conn) as listener:
            catched_vals: set[str] = set()
            async with listener_barrier:
                async for value in listener:
                    if value["data"] == exit_signal:
                        break
                    if value["type"] == "message":
                        catched_vals.add(value["data"])
        return catched_vals

    keys = [f"test-key-{i}" for i in range(key_count)]
    listener = flat_list(
        [
            [create_task(listener_task(k), name=f"listener[{k}]_{i}") for k in keys]
            for i in range(listener_per_key)
        ]
    )
    # To make sure the all listeners started listening before broadcast!
    await listener_barrier.wait()
    broadcasters = [
        create_task(broadcaster_task(k), name=f"producer[{k}]") for k in keys
    ]
    finished, _ = await wait((*broadcasters, *listener), return_when=ALL_COMPLETED)
    broadcasted_vals_list = [
        task.result() for task in finished if task.get_name().startswith("listener")
    ]
    listened_vals_list = [
        task.result() for task in finished if task.get_name().startswith("producer")
    ]
    print(broadcasted_vals_list)
    print(listened_vals_list)
    assert not any(
        broadcasted_vals.symmetric_difference(listened_vals)
        for broadcasted_vals in broadcasted_vals_list
        for listened_vals in listened_vals_list
    ), "Broadcasted Values Are Different from Listened ones!"
