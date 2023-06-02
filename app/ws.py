from asyncio import ALL_COMPLETED, CancelledError, Task, create_task, wait
from typing import Awaitable

from events.enums import MessageTypes
from events.filters import Filters
from fastapi import WebSocket, WebSocketDisconnect
from message_handlers.count import handle_received_count
from message_handlers.event import handle_received_event
from message_handlers.req import create_listener, handle_received_req
from common.tools import surpress_exc_coroutine


EVENT_HANDLER_PREFIX = "EVENT-HANDLER"
REQ_HANDLER_PREFIX = "REQ-HANDLER"
COUNT_HANDLER_PREFIX = "COUNT-HANDLER"
EVENT_LISTENER_PREFIX = "EVENT-LISTENER"


def get_event_handler_task_name(event_id: str) -> str:
    return f"{EVENT_HANDLER_PREFIX}-[{event_id}]"


def get_req_handler_task_name(subs_id: str) -> str:
    return f"{REQ_HANDLER_PREFIX}-[{subs_id}]"


def get_count_handler_task_name(subs_id: str) -> str:
    return f"{COUNT_HANDLER_PREFIX}-[{subs_id}]"


def get_filter_listener_task_name(subs_id: str) -> str:
    return f"{EVENT_LISTENER_PREFIX}-[{subs_id}]"


async def nostr_server(websocket: WebSocket) -> None:
    await websocket.accept()
    bg_tasks: dict[str, Task] = {}
    filter_listener_task: Task | None = None
    try:
        while True:
            data = await websocket.receive_json()
            print(f"RECEIVED DATA: {data}")
            match data:
                case [MessageTypes.Event.value, dict() as event_dict]:
                    # await handle_received_event(event_dict)
                    if event_id := event_dict.get("id"):
                        task_name = get_event_handler_task_name(event_id=event_id)
                        event_task = create_task(handle_received_event(event_dict), name=task_name)  # type: ignore
                        bg_tasks.setdefault(task_name, event_task)

                case [MessageTypes.Req.value, str() as subs_id, *f_dicts]:
                    filters = [Filters(**filters_dict) for filters_dict in f_dicts]
                    handler_task_name = get_req_handler_task_name(subs_id=subs_id)
                    filter_listener_task_name = get_filter_listener_task_name(subs_id=subs_id)
                    # Make sure There is no ongoing process
                    # If there is pending task, cancel it and wait until it finishes
                    if old_handler_task := bg_tasks.get(handler_task_name, None):
                        old_handler_task.cancel("New Req Received!")
                        await surpress_exc_coroutine(old_handler_task, CancelledError)
                    if old_listener_task := bg_tasks.get(filter_listener_task_name, None):
                        old_listener_task.cancel("New Req Received!")
                        await surpress_exc_coroutine(old_listener_task, CancelledError)

                    # Create new tasks
                    handler_task = create_task(
                        handle_received_req(websocket, subs_id, filters),
                        name=handler_task_name,
                    )
                    filter_listener_task = create_task(
                        create_listener(*filters, ws=websocket, subscription_id=subs_id),
                        name=filter_listener_task_name,
                    )
                    # register them in the tasks dict to not to be garbage-collected
                    # and to cancel them gracefully when connection closed
                    bg_tasks.setdefault(handler_task_name, handler_task)
                    bg_tasks.setdefault(filter_listener_task_name, filter_listener_task)

                case [MessageTypes.Count.value, str() as subs_id, *f_dicts]:
                    filters = [Filters(**filter_dict) for filter_dict in f_dicts]
                    task_name = get_count_handler_task_name(subs_id)
                    counter_task = create_task(handle_received_count(websocket, subs_id, filters), name=task_name)
                    bg_tasks.setdefault(task_name, counter_task)

                case [MessageTypes.Close.value, str() as subs_id]:
                    break
                case _:
                    await websocket.send_json(
                        [
                            MessageTypes.Notice.value,
                            {"error": "Invalid Message! Closing the connection."},
                        ]
                    )
                    break
    except WebSocketDisconnect:
        pass
        # await websocket.close()
    except Exception as e:
        print("-----" * 100)
        print(e)
        print("-----" * 100)
    finally:
        await surpress_exc_coroutine(websocket.close(), BaseException)
        await_for: list[Awaitable] = []
        for tname, task in bg_tasks.items():
            if tname.startswith(EVENT_HANDLER_PREFIX):
                # Data Persister Tasks, wait until they are finished successfuly
                await_for.append(task)
            else:
                # Client Interacting Tasks, cancel them.
                task.cancel("Connection Exited")
                await_for.append(create_task(surpress_exc_coroutine(task, CancelledError)))
        if await_for:
            await wait(await_for, return_when=ALL_COMPLETED)
