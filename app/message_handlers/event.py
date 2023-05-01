from events.crud import write_event
from events.data import Event
from pydantic import ValidationError
from utils.errors import InvalidMessageError, ErrorTypes


async def handle_received_event(event_dict: dict):
    # TODO: for the event with kind: 0,
    #       update existing record if any
    try:
        event = Event(**event_dict)
    except ValidationError as exc:
        raise InvalidMessageError(
            "Invalid", error_type=ErrorTypes.validation_error, encapsulated_exc=exc
        )
    await write_event(event=event)
    # TODO: Look up the active filters
    #       Send out if the event is fit any of filters
