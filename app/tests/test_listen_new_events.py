import base64
from asyncio import ALL_COMPLETED, create_task, wait
from datetime import datetime
from random import choice, randbytes, randint
from typing import AsyncGenerator

import pytest
import standalone_app
from async_asgi_testclient import TestClient
from events.enums import MessageTypes
from events.typings import EventNostrDict


@pytest.mark.asyncio
async def test_new_event_catcher() -> None:
    subscription_id = "ekb0AqlmrufGCHoSFldWIG3E0CJIpsSji4vxmO4WkCFk7P1N"
    filtered_e_tag = "kyadiln6qqcmqbfhgd0hisjjl9y1c9er"
    filtered_p_tag = "ickkeebk1uu50sp3q2nin3y2cvyazsa8"
    pubkey = base64.urlsafe_b64encode(randbytes(32)).decode()[:32]
    event_count = 100
    event_filter = {
        "#e": [filtered_e_tag],
        "#p": [filtered_p_tag],
    }

    async def listen_new_events() -> AsyncGenerator[list[EventNostrDict], None]:
        recv_events: list[EventNostrDict] = []
        recv_count = 0
        async with TestClient(standalone_app.app) as client:
            async with client.websocket_connect("/nostr") as ws:
                await ws.send_json(
                    [
                        MessageTypes.Req.value,
                        subscription_id,
                        event_filter,
                    ]
                )
                # Consume the stored events
                while True:
                    print("Consuming the events")
                    [msg_t, *t] = await ws.receive_json()
                    print(msg_t, t, flush=True)
                    if msg_t == MessageTypes.Eose.value:
                        break
                trials = 0
                yield []
                while True:
                    print("Receiving new events!")
                    try:
                        [msg_t, *rest] = await ws.receive_json()
                        trials = 0
                        if msg_t == MessageTypes.Event.value:
                            sb_id, event_det = rest
                            assert (
                                msg_t == MessageTypes.Event.value
                                and sb_id == subscription_id
                            ), "SubscriptionId Error"
                            print(f'Event Received: {event_det["id"]}')
                            recv_events.append(event_det)
                            recv_count += 1
                            if recv_count == event_count:
                                break
                        elif msg_t == MessageTypes.Eose.value:
                            (sb_id,) = rest
                            assert sb_id == subscription_id
                            break
                        else:
                            print(msg_t, rest)
                            print("AMAN AMAAAAN NERELERE DUSTUK HAANIMM")
                            # assert False, "Invalid Message Received"
                    except Exception as e:
                        print("------" * 100)
                        print(e, f"{e!r}", f"{e!s}")
                        print("#@_@#" * 100)
                        trials += 1
                        if trials == 5:
                            break
        yield recv_events

    async def produce_new_events() -> list[EventNostrDict]:
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
        async with TestClient(standalone_app.app) as client:
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
            async with client.websocket_connect("/nostr") as ws:
                for event in events:
                    print(f'Event sent: {event["id"]}', flush=True)
                    await ws.send_json([MessageTypes.Event.value, event])
        return events

    listener = listen_new_events()

    # Conume the filter events
    await anext(listener)

    async def l():
        return await anext(listener)

    receiver = create_task(l(), name="Listener")
    producer = create_task(
        produce_new_events(),
        name="Producer",
    )
    finished, _ = await wait((receiver, producer), return_when=ALL_COMPLETED)
    recv_events, produced_events = (task.result() for task in finished)
    assert len(recv_events) == len(produced_events), "Event Counts Are Not Same!"
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
            (tag for tag in (e1.get("tags") or []) if tag[0] == "#e"),
            key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),  # type: ignore
        )
        e2_e_tags = sorted(
            (tag for tag in (e2.get("tags") or []) if tag[0] == "#e"),
            key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),  # type: ignore
        )
        e1_p_tags = sorted(
            (tag for tag in (e1.get("tags") or []) if tag[0] == "#p"),
            key=lambda t: (t[1], t[2]),
        )
        e2_p_tags = sorted(
            (tag for tag in (e2.get("tags") or []) if tag[0] == "#p"),
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
