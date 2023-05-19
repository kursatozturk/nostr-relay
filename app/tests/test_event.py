import base64
from datetime import datetime
from random import randbytes, choice, randint, choices
from typing import Any

import pytest
import standalone_app
from events.crud import fetch_event, write_event
from events.data import E_Tag, Event, P_Tag
from events.enums import MessageTypes
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_event_storing() -> None:
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
    event_dict: dict[str, Any] = {
        "id": randbytes(16).hex(),
        "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
        "created_at": 129312931,
        "kind": choice([1, 2]),
        "tags": [
            ["#e", choice(tagged_ids), "asdla"],
            ["#e", choice(tagged_ids), "nostr-relay.co"],
            ["#p", choice(tagged_ids), "nostr-er-relay-co.co"],
            ["#p", choice(tagged_ids), "carpenter-co.co"],
            ["#e", choice(tagged_ids), "", "root"],
            ["#p", choice(tagged_ids), "ws://nostr-tr.pub/v2"],
        ],
        "content": "0tYbyhQ7cPcoNyaisCtQiouMbgd40njFBEGcdFaBJe1jCL6jlwgi6FISRrJlVHYmyAuNVpju0VIzeftk"
        "7mkj0KfJfzQ4vxWJUtwHb3DakQNt7Mt2LF5QwNev9dL0aLYSnrzXkpgChShNCjmUWwSOuwg5fcANNimEh9SDl2radme"
        "CVbXiTHqYUDgaCvYaRJjnkwYS3ejZxpInMSzx5DA6zVelCRR5b2qJZocgg1A4REhQsSgSKx678dargBlH6Cz",
        "sig": "Dn4kItKTaHnZcwPjMewufwfX8UFDaMC3yphF7YWeWIqvpnUcXe2ztPgYqBVVF5vY",
    }
    await write_event(event=Event(**event_dict))
    event = await fetch_event(event_dict["id"])
    assert event is not None
    stored_e_tags = sorted(
        (tag for tag in event.tags if type(tag) is E_Tag),
        key=lambda t: (t.event_id, t.recommended_relay_url, t.marker),
    )
    stored_p_tags = sorted(
        (tag for tag in event.tags if type(tag) is P_Tag),
        key=lambda t: (t.pubkey, t.recommended_relay_url),
    )
    e_tags = sorted(
        (tag for tag in event_dict["tags"] if tag[0] == "e"),
        key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),
    )
    p_tags = sorted(
        (tag for tag in event_dict["tags"] if tag[0] == "p"), key=lambda t: (t[1], t[2])
    )
    assert all(
        (_e1[1] == _e2.event_id and _e1[2] == _e2.recommended_relay_url)
        for (_e1, _e2) in zip(e_tags, stored_e_tags)
    ), "E Tags Are Not Same!"  # TODO: Check marker equiality
    assert all(
        (_p1[1] == _p2.pubkey and _p1[2] == _p2.recommended_relay_url)
        for (_p1, _p2) in zip(p_tags, stored_p_tags)
    ), "P Tags are not same!"
    assert (
        event.id == event_dict["id"]
        and event.pubkey == event_dict["pubkey"]
        and event.content == event_dict["content"]
        and event.sig == event_dict["sig"]
    )


def test_event_handling_capability() -> None:
    event_count: int = 400
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
    events: list[dict[str, Any]] = [
        {
            "id": randbytes(16).hex(),
            "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
            "created_at": randint(
                int(datetime.now().timestamp()) - 10000000,
                int(datetime.now().timestamp()),
            ),
            "kind": choice([1, 2]),
            "tags": [
                ["#e", choice(tagged_ids), "asdla"],
                ["#e", choice(tagged_ids), "nostr-relay.co"],
                ["#p", choice(tagged_ids), "nostr-er-relay-co.co"],
                ["#p", choice(tagged_ids), "carpenter-co.co"],
                ["#e", choice(tagged_ids), "", "root"],
                ["#p", choice(tagged_ids), "ws://nostr-tr.pub/v2"],
            ],
            "content": "BJnEKLP7jPWr2V4uvvX24EgXvWArugLX6nFpk2SWC244Oq5FgQlEFl51yH6Pgz1ScePv9rpQ9wvDHnQF98Is"
            "VNJuKX6JW2IipZrP7BkUtYYtAZvZqRukWGzFGb3vZf22Nw4j7iIUJgHq0Z0OV3gQlOoSakd6wa4gKuFascSYvYE9IKRwG2VS"
            "tbQAhEMT6xM9oJcwvrmCVgW9IAzVGzEojT5ZHCwq8yQ3jvGTd5Tf7qSVSz7Wb1roJ9HNYWSKQ2e7OIFY5O3WkYm2SX5qtZ9a"
            "3y66ZHb0Km4g3rovMNAzOFOd7GTYchojk0rP6pXZTB4NbmYulQOxA1rr7mct2ul9rBhWgNZe8aGXa1KAMZL4E2SviNHnYZoy"
            "kw0gNQuQMxPV46RRCfEgthUZx2OHNWKzrMGKt2OfV2cKmaiZeYlnUUpmFPUQ1SIwcq3JA6qn8TAc4eZojWT60nC71hfbGftF"
            "MGWaTzh8Uxw1otg1X83jl51ubOqshpts",
            "sig": "asdjas9dj82ewq1jce2u12h312h312m4yc1242vn742t3bv42nt3c237n49cm=",
        }
        for _ in range(event_count)
    ]
    event_filter = {
        "ids": [event["id"] for event in events],
        "kinds": [1, 2],
        "since": randint(
            int(datetime.now().timestamp()) - 12500000,
            int(datetime.now().timestamp()) - 2500000,
        ),
        "until": randint(
            int(datetime.now().timestamp()) - 7500000,
            int(datetime.now().timestamp()) + 250000,
        ),
        "#e": choices(tagged_ids, k=4 * len(tagged_ids) // 10),
        "#p": choices(tagged_ids, k=8 * len(tagged_ids) // 10),
    }
    client = TestClient(standalone_app.app)
    subscription_id = "ekb0AqlmrufGCHoSFldWIG3E0CJIpsSji4vxmO4WkCFk7P1N"
    with client.websocket_connect("/nostr") as ws:
        for event in events:
            ws.send_json([MessageTypes.Event.value, event])

        ws.send_json(
            [
                MessageTypes.Req.value,
                subscription_id,
                event_filter,
            ]
        )
        recv_events = []
        while True:
            [msg_t, *rest] = ws.receive_json()
            if msg_t == MessageTypes.Event.value:
                sb_id, event_det = rest
                assert msg_t == MessageTypes.Event.value and sb_id == subscription_id
                recv_events.append(event_det)
            elif msg_t == MessageTypes.Eose.value:
                (sb_id,) = rest
                assert sb_id == subscription_id
                break
            else:
                print(msg_t, rest)
                assert False, "Invalid Message Received"
        recv_event_ids = set(e["id"] for e in recv_events)
        recv_events = sorted(recv_events, key=lambda e: e["id"])
        # TODO: apply manual filtering
        # And compare
        # For now, check the integrity of received tags
        events = sorted(
            (e for e in events if e["id"] in recv_event_ids), key=lambda e: e["id"]
        )
        for e1, e2 in zip(events, recv_events):
            assert e1["id"] == e2["id"], "ids are not a match!"
            assert e1["pubkey"] == e2["pubkey"], "Pubkeys are not a match!"
            assert e1["content"] == e2["content"], "Content is not a match!"
            assert e1["sig"].strip() == e2["sig"].strip(), "SIG is not a match!"
            assert e1["created_at"] == e2["created_at"], "Created at is not a match"
            assert e1["kind"] == e2["kind"], "kinds are not a match"
            e1_e_tags = sorted(
                (tag for tag in e1["tags"] if tag[0] == "e"),
                key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),
            )
            e2_e_tags = sorted(
                (tag for tag in e2["tags"] if tag[0] == "e"),
                key=lambda t: (t[1], t[2], t[3] if len(t) == 4 else None),
            )
            e1_p_tags = sorted(
                (tag for tag in e1["tags"] if tag[0] == "p"), key=lambda t: (t[1], t[2])
            )
            e2_p_tags = sorted(
                (tag for tag in e2["tags"] if tag[0] == "p"), key=lambda t: (t[1], t[2])
            )
            assert all(
                (
                    len(e1) == len(e2)
                    and e1[1] == e2[1]
                    and e1[2] == e2[2]
                    and (e1[3] == e2[3] if len(e1) > 3 and len(e2) > 3 else True)
                )
                for (e1, e2) in zip(e1_e_tags, e2_e_tags)
            ), "E Tags Are Not Same!"

            assert all(
                (e1[1] == e2[1] and e1[2] == e2[2])
                for (e1, e2) in zip(e1_p_tags, e2_p_tags)
            ), "P Tags Are Not Same!"
