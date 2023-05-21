import json

from cache.crud import listen_on_key
from events.crud import filter_events
from events.data import Event
from events.enums import MessageTypes
from events.filters import EventFilterer, Filters
from events.typings import EventNostrDict
from fastapi import WebSocket
from pydantic import ValidationError
from utils.errors import ErrorTypes, InvalidMessageError

NEW_EVENT_KEY = "events"


async def create_listener(
    *filters: Filters, ws: WebSocket, subscription_id: str
) -> None:
    event_filterer = EventFilterer(*filters)
    async with listen_on_key(NEW_EVENT_KEY) as listener:
        print(listener)
        async for event_str in listener:
            print(event_str, flush=True)
            if event_str["type"] == "message":
                event: EventNostrDict = json.loads(event_str["data"])
                if event_filterer.test_event(event):
                    print('Tested! sending')
                    await ws.send_json([MessageTypes.Event.value, subscription_id, event])


async def handle_received_req(*filters_dicts: dict) -> tuple[list[Event], list[Filters]]:
    try:
        filters = [Filters(**filters_dict) for filters_dict in filters_dicts]
        events = await filter_events(*filters)
        return events, filters
    except ValidationError as exc:
        raise InvalidMessageError(
            "Invalid Filters!",
            error_type=ErrorTypes.validation_error,
            encapsulated_exc=exc,
        )
