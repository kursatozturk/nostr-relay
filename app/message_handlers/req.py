from db.query import (
    PLACE_HOLDER,
    construct_in_clause,
    construct_lte_gte_clause,
    construct_prefix_clause,
)
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

    filters = []
    values: list[str | int | float] = []
    if fs.ids:
        id_filter = construct_prefix_clause("id", prefix_count=len(fs.ids))
        filters.append(id_filter)
        values.extend(fs.ids)

    if fs.authors:
        author_filter = construct_prefix_clause("pubkey", prefix_count=len(fs.authors))
        filters.append(author_filter)
        values.extend(fs.authors)

    if fs.kinds:
        kind_filter = construct_in_clause("kind", value_count=len(fs.kinds))
        filters.append(kind_filter)
        values.extend(map(str, fs.kinds))

    if fs.since or fs.until:
        btwn_filter = construct_lte_gte_clause(
            "created_at",
            gte=PLACE_HOLDER if fs.since else None,
            lte=PLACE_HOLDER if fs.until else None
        )
        filters.append(btwn_filter)
        if fs.since:
            values.append(fs.since)
        if fs.until:
            values.append(fs.until)


    # event_id = fs.ids[0]
    # event = await fetch_event(event_id)
    # if event is None:
    #     raise InvalidMessageError("Event Not Found", error_type=ErrorTypes.not_found)
    # return event
