from events.crud import fetch_event
from events.data import Filters
from utils.errors import ErrorTypes, InvalidMessageError


async def handle_received_req(filters_dict: dict):
    """
        Caution: This function is a mock implementation
        The implementation of this function waits the design to
        allow usage of the NIPs as modular as possible
    """
    # TODO: Implement the function
    fs = Filters(**filters_dict)

    if fs.ids is None or len(fs.ids) != 1:
        raise InvalidMessageError(
            "Filters Are Not Implemented!", error_type=ErrorTypes.not_implemented
        )

    event_id = fs.ids[0]
    event = await fetch_event(event_id)
    if event is None:
        raise InvalidMessageError("Event Not Found", error_type=ErrorTypes.not_found)
    return event
