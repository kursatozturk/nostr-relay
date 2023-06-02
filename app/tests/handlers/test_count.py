from typing import cast
import pytest
from events.crud import write_event
from events.enums import MessageTypes
from events.filters import Filters
from message_handlers.count import handle_received_count

from tests.events.utils import generate_event
from tests.handlers.utils import MockAsyncSenderWebsocket


@pytest.mark.asyncio
async def test_req_handler() -> None:
    event_count = 50
    events = [generate_event() for _ in range(event_count)]
    f1 = Filters(
        ids=[event.id[:15] for event in events[: event_count // 2]],
        since=min(event.created_at for event in events) - 10,
        until=max(event.created_at for event in events) + 10,
        kinds=[event.kind for event in events],
        authors=[event.pubkey[:10] for event in events],
    )
    f2 = Filters(
        ids=[event.id[:15] for event in events],
    )
    for event in events:
        await write_event(event)
    mocked_ws = MockAsyncSenderWebsocket()
    subscription_id = "jyiasmdwqouetsvjnsjdqxnfkqeprofa"

    await handle_received_count(mocked_ws, subscription_id, [f1, f2])

    data = cast(list[list[str | dict[str, int]]], mocked_ws.get_data())
    assert len(data) == 1, f"There should be only one message but found{len(data)}"
    print(data)
    [counter] = data
    msg_t, subs_id, count_data = cast(tuple[str, str, dict[str, int]], counter)
    assert msg_t == MessageTypes.Count.value, f"Message Type Mismatch, Expected {MessageTypes.Count.value} Found, {msg_t}"
    assert count_data["count"] == event_count
