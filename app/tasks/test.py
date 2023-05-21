import timeit
from asyncio import ALL_COMPLETED, CancelledError, create_task, sleep, wait

from utils.tools import surpress_exc_coroutine

GLOBAL_CONTEXT = {}

async def c1():
    try:
        s = timeit.timeit()
        await c2()
        return 'c1'
    except CancelledError:
        f = timeit.timeit()
        GLOBAL_CONTEXT['c1'] = f'TOOK {f - s} seconds!'
    finally:
        f = timeit.timeit()
        GLOBAL_CONTEXT['c1'] = f'TOOK {f - s} seconds!'
        GLOBAL_CONTEXT['c1-finally'] = 'WHAT THE HELL!'


async def c2():
    await sleep(1)
    return 'c2'

async def test():
    task1 = create_task(c1(), name='c1')
    otasks = []
    # for i in range(25):
    #     task2 = create_task(c2(), name='c2')
    #     otasks.append(task2)
    def callback(c):
        print(f'Callback! {c}')
        # b = create_task(canceller_barrier.wait())
        otasks.append(create_task(c2()))
    task1.add_done_callback(callback)
    # await canceller_barrier.wait()
    print('Neler Oluyor Hayatta!')
    task1.cancel()
    await surpress_exc_coroutine(task1, CancelledError)
    print('Cancelled task1: ', otasks)
    finished_tasks, _ = await wait(otasks, return_when=ALL_COMPLETED)
    print([t.result() for t in finished_tasks])
    print(GLOBAL_CONTEXT)
