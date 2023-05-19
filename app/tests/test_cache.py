import base64
from asyncio import ALL_COMPLETED, create_task, sleep, wait, wait_for, get_event_loop
from datetime import datetime
from random import choice, choices, randbytes, randint
from typing import Any

import pytest
import standalone_app
from cache.core import connect_to_redis
from cache.crud import add_vals_to_set, broadcast, fetch_vals, listen_on_key
from events.data import Event
from events.enums import MessageTypes
from events.typings import EventNostrDict
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_caching() -> None:
    key = "test-key"
    vals: list[int | str] = [1, 2, 3, 4, "test-1", "test-2"]
    str_vals = set(map(str, vals))
    await add_vals_to_set(key, *vals)
    ret_vals = await fetch_vals(key)
    assert not str_vals.difference(ret_vals), "Returned Values Are Different!"


@pytest.mark.asyncio
async def test_pubsub() -> None:
    key = "test-key2"
    exit_signal = "exit"

    async def broadcaster_task() -> set[str]:
        vals = set(map(str, [1, 2, 3, 4, "test-1", "test-2"]))
        for val in vals:
            await sleep(0.1)
            await broadcast(key, val)
        await broadcast(key, exit_signal)
        return vals

    async def listener_task() -> set[str]:
        async with listen_on_key(key) as listener:
            catched_vals: set[str] = set()
            async for value in listener:
                if value["data"] == exit_signal:
                    break
                if value["type"] == "message":
                    catched_vals.add(value["data"])
        return catched_vals

    listener = create_task(listener_task())
    broadcaster = create_task(broadcaster_task())
    finished, _ = await wait((broadcaster, listener), return_when=ALL_COMPLETED)
    broadcasted_vals, listened_vals = (task.result() for task in finished)
    print(broadcasted_vals.symmetric_difference(listened_vals))
    assert not broadcasted_vals.symmetric_difference(
        listened_vals
    ), "Broadcasted Values Are Different from Listened ones!"


@pytest.mark.asyncio
async def test_new_event_catcher() -> None:
    tagged_ids: list[str] = [
        "eab9c7fb4b34cb2f3fb1d5e30744bc2b",
        "88e4485952df3b5e783dcbb5a6e78e87",
        "gsgxsqcmgfqkawugzzcewyrhjqtbhaid",
        "axroedqxfanffqjniyjfrkococabogfq",
        "11bbfc8a353fbe5bcf79710fcd876a84",
        "989999sadkasjdj128e382jas9ds99d9",
        "omg56t48awudwg4h48llt62xdjlb0h9w",
        "4wzq8hzlvojq0hqthwgnpr0otfdg5oi1",
        "d5o13keqmav1qqc3lhif8j6jngh11ihh",
    ]

    client = TestClient(standalone_app.app)
    subscription_id = "ekb0AqlmrufGCHoSFldWIG3E0CJIpsSji4vxmO4WkCFk7P1N"
    filtered_e_tag = "kyadiln6qqcmqbfhgd0hisjjl9y1c9er"
    filtered_p_tag = "ickkeebk1uu50sp3q2nin3y2cvyazsa8"
    pubkey = base64.urlsafe_b64encode(randbytes(32)).decode()[:32]
    event_count = 1

    async def produce_new_events() -> list[EventNostrDict]:
        events: list[EventNostrDict] = [
            {
                "id": randbytes(16).hex(),
                "pubkey": pubkey,
                "created_at": randint(
                    int(datetime.now().timestamp()) - 10000000,
                    int(datetime.now().timestamp()),
                ),
                "kind": choice([1, 2]),
                "tags": [
                    ("#e", filtered_e_tag, "asdla"),
                    ("#p", filtered_p_tag, "nostr-er-relay-co.co"),
                    ("#e", choice(tagged_ids), "nostr-relay.co"),
                    ("#p", choice(tagged_ids), "carpenter-co.co"),
                    ("#e", choice(tagged_ids), "", "root"),
                    ("#p", choice(tagged_ids), "ws://nostr-tr.pub/v2"),
                ],
                "content": "BJnEKLP7jPWr2V4uvvX24EgXvWArugLX6nFpk2SWC244Oq5FgQlEFl51yH6Pgz1ScePv9rpQ9wvDHnQF98Is"
                "VNJuKX6JW2IipZrP7BkUtYYtAZvZqRukWGzFGb3vZf22Nw4j7iIUJgHq0Z0OV3gQlOoSakd6wa4gKuFascSYvYE9IKRwG2VS"
                "tbQAhEMT6xM9oJcwvrmCVgW9IAzVGzEojT5ZHCwq8yQ3jvGTd5Tf7qSVSz7Wb1roJ9HNYWSKQ2e7OIFY5O3WkYm2SX5qtZ9a"
                "3y66ZHb0Kmg3rovMNAzOFOd7GTYchojk0rP6pXZTB4NbmYulQOxA1rr7mct2ul9rBhWgNZe8aGXa1KAMZL4E2SviNHnYZoy"
                "kw0gNQuQMxPV46RRCfEgthUZx2OHNWKzrMGKt2OfV2cKmaiZeYlnUUpmFPUQ1SIwcq3JA6qn8TAc4eZojWT60nC71hfbGftF"
                "MGWaTzh8Uxw1otg1X83jl51ubOqshpts",
                "sig": "asdjas9dj82ewq1jce2u12h312h312m4yc1242vn742t3bv42nt3c237n49cm=",
            }
            for _ in range(event_count)
        ]
        print("AAAAAAAAAAAA", flush=True)
        with client.websocket_connect("/nostr") as ws:
            for event in events:
                print(f'Event sent: {event["id"]}', flush=True)
                ws.send_json([MessageTypes.Event.value, event])
                await sleep(0.1)
        return events

    event_filter = {
        "#e": [filtered_e_tag],
        "#p": [filtered_p_tag],
    }

    with client.websocket_connect("/nostr") as ws:
        ws.send_json(
            [
                MessageTypes.Req.value,
                subscription_id,
                event_filter,
            ]
        )
        # Consume the stored events
        while True:
            print("Consuming the events")
            [msg_t, *_] = ws.receive_json()
            if msg_t == MessageTypes.Eose.value:
                break
        # create the producer and start listening on new events
        producer_task = create_task(produce_new_events())
        recv_events: list[EventNostrDict] = []
        recv_count = 0
        while True:
            print("Receiving new events!")
            [msg_t, *rest] = ws.receive_json()
            print("Received new events!")
            print("##" * 50)
            if msg_t == MessageTypes.Event.value:
                sb_id, event_det = rest
                assert msg_t == MessageTypes.Event.value and sb_id == subscription_id
                print(f'Event Received: {event_det["id"]}')
                recv_events.append(event_det)
                if recv_count == event_count:
                    break
            elif msg_t == MessageTypes.Eose.value:
                (sb_id,) = rest
                assert sb_id == subscription_id
                break
            else:
                print(msg_t, rest)
                assert False, "Invalid Message Received"
        print("Something Went Horribly Wrong!")
        produced_events = await wait_for(producer_task, timeout=None)
        recv_events = sorted(recv_events, key=lambda e: e["id"])
        events = sorted((e for e in produced_events), key=lambda e: e["id"])
        for e1, e2 in zip(events, recv_events):
            assert e1["id"] == e2["id"], "ids are not a match!"
            assert e1["pubkey"] == e2["pubkey"], "Pubkeys are not a match!"
            assert e1["content"] == e2["content"], "Content is not a match!"
            assert e1["sig"].strip() == e2["sig"].strip(), "SIG is not a match!"
            assert e1["created_at"] == e2["created_at"], "Created at is not a match"
            assert e1["kind"] == e2["kind"], "kinds are not a match"
            e1_e_tags = sorted(
                (tag for tag in (e1.get("tags") or []) if tag[0] == "e"),
                key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),  # type: ignore
            )
            e2_e_tags = sorted(
                (tag for tag in (e2.get("tags") or []) if tag[0] == "e"),
                key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),  # type: ignore
            )
            e1_p_tags = sorted(
                (tag for tag in (e1.get("tags") or []) if tag[0] == "p"),
                key=lambda t: (t[1], t[2]),
            )
            e2_p_tags = sorted(
                (tag for tag in (e2.get("tags") or []) if tag[0] == "p"),
                key=lambda t: (t[1], t[2]),
            )
            assert all(
                (
                    len(e1) == len(e2)
                    and e1[1] == e2[1]
                    and e1[2] == e2[2]
                    and (e1[3] == e2[3] if len(e1) > 3 and len(e2) > 3 else True)  # type: ignore
                )
                for (e1, e2) in zip(e1_e_tags, e2_e_tags)
            ), "E Tags Are Not Same!"

            assert all(
                (e1[1] == e2[1] and e1[2] == e2[2])
                for (e1, e2) in zip(e1_p_tags, e2_p_tags)
            ), "P Tags Are Not Same!"
