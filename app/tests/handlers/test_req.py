from asyncio import Barrier, create_task
import pytest
from events.data import Event
from events.enums import MessageTypes
from events.filters import Filters

import standalone_app
from async_asgi_testclient import TestClient
from tests.events.utils import assert_two_events_same, generate_event
from tests.handlers.utils import listen_new_events


@pytest.mark.asyncio
async def test_req_handler() -> None:
    event1 = generate_event()
    event2 = generate_event()
    f1 = Filters(
        ids=[event1.id[:10], event2.id[:15]],
        since=min(event1.created_at, event2.created_at) - 10,
        until=max(event1.created_at, event2.created_at) + 10,
        kinds=[event1.kind, event2.kind],
        authors=[event1.pubkey[:10], event2.pubkey[:20]],
    )
    barrier = Barrier(2)
    listener_task = create_task(
        listen_new_events(
            barrier=barrier, subscription_id="rsfsvovkaglckuzrhdasmfnzbalnkkgf", event_filter=f1.dict(), expected_new_event_count=2
        ),
        name="Listener",
    )
    await barrier.wait()  # Let the listener consumes existing events

    async with TestClient(standalone_app.app) as client:
        async with client.websocket_connect("/") as ws:
            await ws.send_json([MessageTypes.Event.value, event1.nostr_dict])
            await ws.send_json([MessageTypes.Event.value, event2.nostr_dict])

    await listener_task
    new_events = listener_task.result()

    sorted_new_events = sorted(map(lambda e: Event(**e), new_events), key=lambda e: e.id)  # type: ignore
    sorted_events = sorted([event1, event2], key=lambda e: e.id)
    assert len(sorted_events) == len(sorted_new_events), "Event Counts Are Not Matching!"
    for e1, e2 in zip(sorted_events, sorted_new_events):
        assert_two_events_same(e1, e2)
