import base64
from random import randbytes

import standalone_app
from events.coms import MessageTypes
from events.crud import fetch_event, write_event
from events.data import E_Tag, Event, P_Tag
from fastapi.testclient import TestClient

import pytest


@pytest.mark.asyncio
async def test_event_storing():
    event_dict = {
        "id": randbytes(16).hex(),
        "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
        "created_at": 129312931,
        "kind": 1,
        "tags": [
            ["e", "eab9c7fb4b34cb2f3fb1d5e30744bc2b", "asdla"],
            ["e", "88e4485952df3b5e783dcbb5a6e78e87", "nostr-relay.co"],
            ["p", "gsgxsqcmgfqkawugzzcewyrhjqtbhaid", "nostr-er-relay-co.co"],
            ["p", "axroedqxfanffqjniyjfrkococabogfq", "carpenter-co.co"],
            ["e", "11bbfc8a353fbe5bcf79710fcd876a84", "", "root"],
            ["p", "989999sadkasjdj128e382jas9ds99d9", "ws://nostr-tr.pub/v2"],
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
    print(stored_e_tags, e_tags)
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


def test_event_handling_capability():
    event = {
        "id": randbytes(16).hex(),
        "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
        "created_at": 182312831824812,
        "kind": 1,
        "tags": [
            ["e", "88e4485952df3b5e783dcbb5a6e78e87", "nostr-relay.co"],
            ["p", "gsgxsqcmgfqkawugzzcewyrhjqtbhaid", "nostr-er-relay-co.co"],
            ["p", "axroedqxfanffqjniyjfrkococabogfq", "carpenter-co.co"],
            ["e", "11bbfc8a353fbe5bcf79710fcd876a84", "", "root"],
            ["p", "989999sadkasjdj128e382jas9ds99d9", "ws://nostr-tr.pub/v2"],
        ],
        "content": "BJnEKLP7jPWr2V4uvvX24EgXvWArugLX6nFpk2SWC244Oq5FgQlEFl51yH6Pgz1ScePv9rpQ9wvDHnQF98Is"
        "VNJuKX6JW2IipZrP7BkUtYYtAZvZqRukWGzFGb3vZf22Nw4j7iIUJgHq0Z0OV3gQlOoSakd6wa4gKuFascSYvYE9IKRwG2VS"
        "tbQAhEMT6xM9oJcwvrmCVgW9IAzVGzEojT5ZHCwq8yQ3jvGTd5Tf7qSVSz7Wb1roJ9HNYWSKQ2e7OIFY5O3WkYm2SX5qtZ9a"
        "3y66ZHb0Km4g3rovMNAzOFOd7GTYchojk0rP6pXZTB4NbmYulQOxA1rr7mct2ul9rBhWgNZe8aGXa1KAMZL4E2SviNHnYZoy"
        "kw0gNQuQMxPV46RRCfEgthUZx2OHNWKzrMGKt2OfV2cKmaiZeYlnUUpmFPUQ1SIwcq3JA6qn8TAc4eZojWT60nC71hfbGftF"
        "MGWaTzh8Uxw1otg1X83jl51ubOqshpts",
        "sig": "asdjas9dj82ewq1jce2u12h312h312m4yc1242vn742t3bv42nt3c237n49cm=",
    }
    event_filter = {"ids": [event["id"]]}
    client = TestClient(standalone_app.app)
    with client.websocket_connect("/nostr") as ws:
        ws.send_json([MessageTypes.Event.value, event])
        ws.send_json(
            [
                MessageTypes.Req.value,
                "ekb0AqlmrufGCHoSFldWIG3E0CJIpsSji4vxmO4WkCFk7P1N",
                event_filter,
            ]
        )
        data = ws.receive_json()
        print(data)
        assert (
            len(data) >= 1
            and data[0]["id"] == event["id"]
            and data[0]["pubkey"] == event["pubkey"]
        )
