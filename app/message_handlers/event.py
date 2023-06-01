import json
from cache.crud import broadcast
from common.tools import surpress_exc_coroutine
from events.crud import delete_contact_list, delete_old_metadata, write_event
from events.data import Event
from pydantic import ValidationError
from common.errors import InvalidMessageError, ErrorTypes
from events.typings import EventNostrDict
from psycopg.errors import UniqueViolation

NEW_EVENT_KEY = "events"


async def handle_received_event(event_dict: EventNostrDict) -> Event:
    # TODO: for the event with kind: 0,
    #       update existing record if any
    try:
        event = Event(**event_dict)  # type: ignore
    except ValidationError as exc:
        raise InvalidMessageError("Invalid", error_type=ErrorTypes.validation_error, encapsulated_exc=exc)
    if event.is_metadata:
        # It will try to delete old metadata entries
        await delete_old_metadata(event.pubkey)
    if event.is_contact_list:
        await delete_contact_list(event.pubkey)
    await surpress_exc_coroutine(write_event(event=event), UniqueViolation)
    await broadcast(NEW_EVENT_KEY, json.dumps(event.nostr_dict))
    return event
