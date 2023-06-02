from asyncio import create_task, wait_for
import pytest
from events.crud import fetch_event
from events.data import Event
from events.enums import MessageTypes
from message_handlers.event import handle_received_event

from tests.events.utils import assert_two_events_same, generate_event
from tests.handlers.utils import event_listener

# from fastapi.testclient import TestClient
from async_asgi_testclient import TestClient
import standalone_app


@pytest.mark.asyncio
async def test_event_handler():
    event = generate_event()
    task = create_task(event_listener(event))
    await handle_received_event(event.nostr_dict)
    await wait_for(task, timeout=1)
    stored_event_dict = await fetch_event(event.id)
    stored_event = Event(**stored_event_dict)  # type: ignore
    assert_two_events_same(event, stored_event)

    ephemeral_event = generate_event(kind=20001)
    await handle_received_event(ephemeral_event.nostr_dict)
    stored_event = await fetch_event(ephemeral_event.id)
    assert not stored_event


@pytest.mark.asyncio
async def test_ws_event_handler():
    client_count = 4
    event_per_client = 4
    generated_events: list[Event] = []
    recv_events: list[Event] = []
    for _ in range(client_count):
        async with TestClient(standalone_app.app) as client:
            events = [generate_event() for _ in range(event_per_client)]
            generated_events.extend(events)
            async with client.websocket_connect("/") as ws:
                # Send Out the events
                for event in events:
                    await ws.send_json([MessageTypes.Event.value, event.nostr_dict])

    event_filter = {"ids": [e.id for e in generated_events]}
    async with TestClient(standalone_app.app) as client:
        async with client.websocket_connect("/") as ws:
            # a separate connection to behave as if independent client
            subscription_id = "asudhptxapidsioixlhgxsqjhzsxjdei"
            await ws.send_json([MessageTypes.Req.value, subscription_id, event_filter])

            while True:
                [msg_t, *rest] = await ws.receive_json()
                if msg_t == MessageTypes.Event.value:
                    sb_id, event_det = rest
                    assert msg_t == MessageTypes.Event.value and sb_id == subscription_id
                    recv_events.append(Event(**event_det))
                elif msg_t == MessageTypes.Eose.value:
                    (sb_id,) = rest
                    print("EOSE RECEIVED")
                    assert sb_id == subscription_id
                    break
                else:
                    assert False, "Invalid Message Received"

    sorted_events = sorted(generated_events, key=lambda e: e.id)
    sorted_recv_events = sorted(recv_events, key=lambda e: e.id)
    print(sorted_events, len(sorted_events))
    print(sorted_recv_events, len(sorted_recv_events))
    assert len(sorted_events) == len(sorted_recv_events), "Received events does not have same count as created events!"
    for e1, e2 in zip(sorted_events, sorted_recv_events):
        assert_two_events_same(e1, e2)
