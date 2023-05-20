from asyncio import ALL_COMPLETED, create_task, sleep, wait

import pytest
from cache.crud import add_vals_to_set, broadcast, fetch_vals, listen_on_key


@pytest.mark.asyncio
async def test_caching() -> None:
    key = "test-key"
    vals: list[int | str] = [1, 2, 3, 4, "test-1", "test-2"]
    str_vals = set(map(str, vals))
    await add_vals_to_set(key, *vals)
    ret_vals = await fetch_vals(key)
    assert not str_vals.difference(ret_vals), "Returned Values Are Different!"


@pytest.mark.asyncio
async def test_pubsub() -> None:
    key = "test-key2"
    exit_signal = "exit"

    async def broadcaster_task() -> set[str]:
        vals = set(map(str, [1, 2, 3, 4, "test-1", "test-2"]))
        for val in vals:
            await sleep(0.1)
            await broadcast(key, val)
        await broadcast(key, exit_signal)
        return vals

    async def listener_task() -> set[str]:
        async with listen_on_key(key) as listener:
            catched_vals: set[str] = set()
            async for value in listener:
                if value["data"] == exit_signal:
                    break
                if value["type"] == "message":
                    catched_vals.add(value["data"])
        return catched_vals

    listener = create_task(listener_task())
    broadcasters = [create_task(broadcaster_task()) for _ in range(50)]
    finished, _ = await wait((*broadcasters, listener), return_when=ALL_COMPLETED)
    *broadcasted_vals_list, listened_vals = (task.result() for task in finished)
    assert not any(
        broadcasted_vals.symmetric_difference(listened_vals)
        for broadcasted_vals in broadcasted_vals_list
    ), "Broadcasted Values Are Different from Listened ones!"
