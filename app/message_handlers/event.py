import json
from cache.crud import broadcast
from common.tools import surpress_exc_coroutine
from events.crud import delete_event_by_kind_pubkey, delete_events, fetch_event_by_kind_pubkey, write_event
from events.data import CONTACT_LIST_KIND, METADATA_KIND, Event
from pydantic import ValidationError
from common.errors import InvalidMessageError, ErrorTypes
from events.typings import EventNostrDict
from psycopg.errors import UniqueViolation

from tags.data.e_tag import E_Tag

NEW_EVENT_KEY = "events"


async def handle_received_event(event_dict: EventNostrDict) -> None:
    try:
        event = Event(**event_dict)  # type: ignore
    except ValidationError as exc:
        raise InvalidMessageError("Validation Error", error_type=ErrorTypes.validation_error, encapsulated_exc=exc)
    if event.is_event_deletion:
        await delete_events(event.pubkey, [t.event_id for t in event.tags if isinstance(t, E_Tag)])
    elif event.is_metadata:
        # It will try to delete old metadata entries
        existing_event = await fetch_event_by_kind_pubkey(METADATA_KIND, event.pubkey)
        if existing_event and existing_event["created_at"] >= event.created_at:
            return
        await delete_event_by_kind_pubkey(METADATA_KIND, event.pubkey)
    elif event.is_contact_list:
        existing_event = await fetch_event_by_kind_pubkey(CONTACT_LIST_KIND, event.pubkey)
        if existing_event and existing_event["created_at"] >= event.created_at:
            return
        await delete_event_by_kind_pubkey(CONTACT_LIST_KIND, event.pubkey)
    elif event.is_replaceable_event:
        existing_event = await fetch_event_by_kind_pubkey(event.kind, event.pubkey)
        if existing_event and existing_event["created_at"] >= event.created_at:
            return
        await delete_event_by_kind_pubkey(event.kind, event.pubkey)

    if event.should_store_event:
        await surpress_exc_coroutine(write_event(event=event), UniqueViolation)
    await broadcast(NEW_EVENT_KEY, json.dumps(event.nostr_dict))
    return None
