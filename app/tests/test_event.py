import base64
from functools import reduce
from random import randbytes

import pytest
import standalone_app
from events.coms import MessageTypes
from fastapi.testclient import TestClient


def test_event_storing_capability():
    event_1 = {
        "id": randbytes(16).hex(),
        "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
        "created_at": 129312931,
        "kind": 1,
        "tags": [["e", "eab9c7fb4b34cb2f3fb1d5e30744bc2b", "asdla"]],
        "content": "0tYbyhQ7cPcoNyaisCtQiouMbgd40njFBEGcdFaBJe1jCL6jlwgi6FISRrJlVHYmyAuNVpju0VIzeftk"
        "7mkj0KfJfzQ4vxWJUtwHb3DakQNt7Mt2LF5QwNev9dL0aLYSnrzXkpgChShNCjmUWwSOuwg5fcANNimEh9SDl2radme"
        "CVbXiTHqYUDgaCvYaRJjnkwYS3ejZxpInMSzx5DA6zVelCRR5b2qJZocgg1A4REhQsSgSKx678dargBlH6Cz",
        "sig": "Dn4kItKTaHnZcwPjMewufwfX8UFDaMC3yphF7YWeWIqvpnUcXe2ztPgYqBVVF5vY",
    }
    event_2 = {
        "id": randbytes(16).hex(),
        "pubkey": base64.urlsafe_b64encode(randbytes(32)).decode()[:32],
        "created_at": 182312831824812,
        "kind": 1,
        "tags": [
            ["e", "88e4485952df3b5e783dcbb5a6e78e87", "nostr-relay.co"],
            ["p", "gsgxsqcmgfqkawugzzcewyrhjqtbhaid", "nostr-er-relay-co.co"],
            ["p", "axroedqxfanffqjniyjfrkococabogfq", "carpenter-co.co"],
            ["e", "11bbfc8a353fbe5bcf79710fcd876a84", "ws://carpenter.social", "root"],
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
    event_filter_1 = {"ids": [event_1["id"]]}
    client = TestClient(standalone_app.app)
    with client.websocket_connect("/nostr") as ws:
        ws.send_json([MessageTypes.Event.value, event_1])
        ws.send_json(
            [
                MessageTypes.Req.value,
                "ekb0AqlmrufGCHoSFldWIG3E0CJIpsSji4vxmO4WkCFk7P1N",
                event_filter_1,
            ]
        )
        data = ws.receive_json()
        print(data)
        assert (
            False
            and len(data) >= 1
            and data[0]["id"] == event_1["id"]
            and data[0]["pubkey"] == event_1["pubkey"]
        )
