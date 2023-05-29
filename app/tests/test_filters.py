import base64
from random import choice, randbytes
from typing import Any

from events.data import Event
from events.filters import EventFilterer, Filters
from tags.db.e_tag import E_TAG_TAG_NAME
from tags.db.p_tag import P_TAG_TAG_NAME


def test_event_filtering() -> None:
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
            [E_TAG_TAG_NAME, choice(tagged_ids), "asdla"],
            [E_TAG_TAG_NAME, choice(tagged_ids), "nostr-relay.co"],
            [P_TAG_TAG_NAME, choice(tagged_ids), "nostr-er-relay-co.co"],
            [P_TAG_TAG_NAME, choice(tagged_ids), "carpenter-co.co"],
            [E_TAG_TAG_NAME, choice(tagged_ids), "", "root"],
            [P_TAG_TAG_NAME, choice(tagged_ids), "ws://nostr-tr.pub/v2"],
        ],
        "content": "0tYbyhQ7cPcoNyaisCtQiouMbgd40njFBEGcdFaBJe1jCL6jlwgi6FISRrJlVHYmyAuNVpju0VIzeftk"
        "7mkj0KfJfzQ4vxWJUtwHb3DakQNt7Mt2LF5QwNev9dL0aLYSnrzXkpgChShNCjmUWwSOuwg5fcANNimEh9SDl2radme"
        "CVbXiTHqYUDgaCvYaRJjnkwYS3ejZxpInMSzx5DA6zVelCRR5b2qJZocgg1A4REhQsSgSKx678dargBlH6Cz",
        "sig": "Dn4kItKTaHnZcwPjMewufwfX8UFDaMC3yphF7YWeWIqvpnUcXe2ztPgYqBVVF5vY",
    }
    event = Event(**event_dict)
    event_nostr = event.nostr_dict

    filters_1 = Filters(ids=[event_dict["id"][:14]])  # one pases
    filters_2 = Filters(ids=[event_dict["id"][10:]])  # one not but combination should allow it
    filterer = EventFilterer(filters_1, filters_2)
    assert filterer.test_event(event_nostr), "Event Id filtering is not working!"
    filters = Filters(ids=[randbytes(16).hex()[:25]])
    filterer = EventFilterer(filters)
    assert not filterer.test_event(event_nostr), "Event Id filtering is not working!"

    filters_e = Filters(
        **{"#e": [t[1] for t in event_dict["tags"] if t[0] == E_TAG_TAG_NAME][:1]},  # type: ignore
    )
    filters_p = Filters(
        **{"#p": [t[1] for t in event_dict["tags"] if t[0] == P_TAG_TAG_NAME][:1]},  # type: ignore
    )
    filterer = EventFilterer(filters_e, filters_p)
    assert filterer.test_event(event_nostr), "Tag filtering is not working!"

    filters = Filters(
        **{"#e": [randbytes(16).hex()[:5]]},  # type: ignore
        **{"#p": [randbytes(16).hex()[:5]]},  # type: ignore
    )
    filterer = EventFilterer(filters)
    assert not filterer.test_event(event_nostr), "Tag filtering is not working!"

    filters = Filters(authors=[event_dict["pubkey"][:12], randbytes(16).hex()[:14]])
    filterer = EventFilterer(filters)
    assert filterer.test_event(event_nostr), "Authors filtering not working!"

    filters = Filters(authors=[randbytes(16).hex()[:14]])
    filterer = EventFilterer(filters)
    assert not filterer.test_event(event_nostr), "Authors filtering not working!"

    filters = Filters(since=event_dict["created_at"] - 10, until=event_dict["created_at"] + 10)
    filterer = EventFilterer(filters)
    assert filterer.test_event(event_nostr), "Since/Until filtering not working!"

    filters = Filters(since=event_dict["created_at"] + 10, until=event_dict["created_at"] + 20)
    filters_2 = Filters(since=event_dict["created_at"] - 100, until=event_dict["created_at"] - 50)
    filterer = EventFilterer(filters, filters_2)
    assert not filterer.test_event(event_nostr), "Since/Until filtering not working!"

    filters = Filters(kinds=[1, 2])
    filterer = EventFilterer(filters)
    assert filterer.test_event(event_nostr), "Kinds filtering not working!"

    filters = Filters(kinds=[3, 4])
    filterer = EventFilterer(filters)
    assert not filterer.test_event(event_nostr), "Kinds filtering not working!"
