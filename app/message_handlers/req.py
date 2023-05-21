import json
from asyncio import CancelledError

from cache.core import get_redis_connection
from cache.crud import listen_on_key
from events.crud import filter_events
from events.enums import MessageTypes
from events.filters import EventFilterer, Filters
from events.typings import EventNostrDict
from fastapi import WebSocket
from pydantic import ValidationError
from utils.errors import ErrorTypes, InvalidMessageError

NEW_EVENT_KEY = "events"


async def create_listener(*filters: Filters, ws: WebSocket, subscription_id: str) -> None:
    event_filterer = EventFilterer(*filters)
    r_conn = get_redis_connection()
    async with listen_on_key(NEW_EVENT_KEY, r_conn=r_conn) as listener:
        async for event_str in listener:
            if event_str["type"] == "message":
                event: EventNostrDict = json.loads(event_str["data"])
                if event_filterer.test_event(event):
                    await ws.send_json([MessageTypes.Event.value, subscription_id, event])
    await r_conn.close()


async def handle_received_req(ws: WebSocket, subs_id: str, filters: list[Filters]) -> None:
    try:
        # filters = [Filters(**filters_dict) for filters_dict in filters_dicts]
        events = await filter_events(*filters)
        for event in events:
            await ws.send_json(
                [
                    MessageTypes.Event.value,
                    subs_id,
                    event.nostr_dict,
                ]
            )
        await ws.send_json([MessageTypes.Eose.value, subs_id])

        # return events, filters
    except ValidationError as exc:
        raise InvalidMessageError(
            "Invalid Filters!",
            error_type=ErrorTypes.validation_error,
            encapsulated_exc=exc,
        )
    except CancelledError as cancel:
        print(cancel)
        print("AAAAAAAAAAAAAAAAAAAAAAAAAA" * 100)
        pass
