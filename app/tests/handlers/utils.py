import json
from asyncio import Barrier

import standalone_app
from async_asgi_testclient import TestClient
from cache.crud import listen_on_key
from events.data import Event
from events.enums import MessageTypes
from events.typings import EventNostrDict
from message_handlers.event import NEW_EVENT_KEY
from pydantic import ValidationError
from tests.events.utils import assert_two_events_same


async def event_listener(*expected_events: Event):
    events_by_id = {event.id: event for event in expected_events}
    async with listen_on_key(NEW_EVENT_KEY) as listener:
        async for event_as_str in listener:
            if event_as_str["type"] == "message":
                event_nostr: EventNostrDict = json.loads(event_as_str["data"])
                try:
                    event = Event(**event_nostr)  # type: ignore
                    if expected_event := events_by_id.pop(event.id):
                        assert_two_events_same(event, expected_event)
                        print(event, expected_event)
                    else:
                        assert False, "Received an Unexpected Event"
                except ValidationError as err:
                    print(err)
                    print(event_nostr)
                    assert False, "Invalid data received!"
            if not events_by_id:
                break

async def listen_new_events(barrier: Barrier, subscription_id: str, event_filter: dict, expected_new_event_count: int) -> list[EventNostrDict]:
    recv_events: list[EventNostrDict] = []
    async with TestClient(standalone_app.app) as client:
        async with client.websocket_connect("/") as ws:
            await ws.send_json(
                [
                    MessageTypes.Req.value,
                    subscription_id,
                    event_filter,
                ]
            )
            # Consume the stored events
            while True:
                [msg_t, *t] = await ws.receive_json()
                if msg_t == MessageTypes.Eose.value:
                    break
            trials = 0
            await barrier.wait()
            while len(recv_events) < expected_new_event_count:
                try:
                    [msg_t, *rest] = await ws.receive_json()
                    trials = 0
                    if msg_t == MessageTypes.Event.value:
                        sb_id, event_det = rest
                        assert msg_t == MessageTypes.Event.value and sb_id == subscription_id, "SubscriptionId Error"
                        recv_events.append(event_det)
                    elif msg_t == MessageTypes.Eose.value:
                        (sb_id,) = rest
                        assert sb_id == subscription_id
                        break
                    else:
                        assert False, "Invalid Message Received"
                except Exception as e:
                    trials += 1
                    if trials == 5:
                        print(e)
                        assert False, "Exception Loop!"
                        break
    return recv_events
