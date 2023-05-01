from events.coms import MessageTypes
from events.crud import fetch_event
from events.data import Event, Filters
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from message_handlers.event import handle_received_event
from pydantic import ValidationError
from utils.errors import InvalidMessageError

nostr = APIRouter()

INVALID_MESSAGE = {"Error": "invalid_message"}


@nostr.websocket("/nostr", name="Nostr Ws")
async def nostr_server(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            try:
                match data:
                    case [MessageTypes.Event.value, dict() as event_dict]:
                        await handle_received_event(event_dict)
                    case [
                        MessageTypes.Req.value,
                        str() as subscription_id,
                        dict() as fltrs_dict,
                    ]:
                        try:
                            filters = Filters(**fltrs_dict)
                            if len(filters.ids or []) != 1:
                                await websocket.send_json(
                                    {"Error": "Not (yet) Supported OP!"}
                                )
                                continue
                            event_id = filters.ids[0]
                            event = await fetch_event(event_id)
                            await websocket.send_json([event.nostr_dict])
                            continue
                        except ValidationError:
                            await websocket.send_json(INVALID_MESSAGE)
                            continue

                    case [MessageTypes.Close.value, str() as subscription_id]:
                        await websocket.send_json({"subscription_id": subscription_id})
                    case _:
                        await websocket.send_json(INVALID_MESSAGE)

            except InvalidMessageError as e:
                await websocket.send_json(INVALID_MESSAGE)
                pass
    except WebSocketDisconnect:
        await websocket.close()
