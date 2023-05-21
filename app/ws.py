from typing import Any
from events.enums import MessageTypes
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from message_handlers.event import handle_received_event
from message_handlers.req import handle_received_req, create_listener
from utils.errors import InvalidMessageError
from asyncio import Task, create_task

nostr = APIRouter()

INVALID_MESSAGE = {"Error": "invalid_message"}


@nostr.websocket("/nostr", name="Nostr Ws")
async def nostr_server(websocket: WebSocket) -> Any:
    await websocket.accept()
    bg_tasks: list[Task] = []
    try:
        while True:
            data = await websocket.receive_json()
            try:
                match data:
                    case [MessageTypes.Event.value, event_dict]:
                        await handle_received_event(event_dict)
                    case [
                        MessageTypes.Req.value,
                        str() as subscription_id,
                        *filters_dicts,
                    ]:
                        events, filters = await handle_received_req(*filters_dicts)
                        for event in events:
                            await websocket.send_json(
                                [
                                    MessageTypes.Event.value,
                                    subscription_id,
                                    event.nostr_dict,
                                ]
                            )
                        await websocket.send_json(
                            [MessageTypes.Eose.value, subscription_id]
                        )
                        task = create_task(
                            create_listener(*filters, ws=websocket, subscription_id=subscription_id)
                        )
                        bg_tasks.append(task)

                    case [MessageTypes.Close.value, str() as subscription_id]:
                        await websocket.send_json({"subscription_id": subscription_id})
                    case _:
                        await websocket.send_json(INVALID_MESSAGE)

            except InvalidMessageError as e:
                # This is only for testing purposes
                # When the implementation finishes
                # and I start to polish the codebase
                # This will be removed as this behavior is not compatible
                # with the nostr client
                await websocket.send_json([f"details: {e!r}||{e!s}"])
                break
    except WebSocketDisconnect:
        await websocket.close()
    finally:
        for task in bg_tasks:
            task.cancel()
