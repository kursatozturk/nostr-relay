import pytest
from events.crud import fetch_event, write_event
from events.data import Event

from tests.events.utils import assert_two_events_same, generate_event


@pytest.mark.asyncio
async def test_event_storing() -> None:
    # tag ids/pubkeys are not validated
    # tag_rows = [
    #     (E_TAG_TAG_NAME, "d5o13keqmav1qqc3lhif8j6jngh11ihh"),
    #     (E_TAG_TAG_NAME, "4wzq8hzlvojq0hqthwgnpr0otfdg5oi1", "nostr-relay.co"),
    #     (E_TAG_TAG_NAME, "11bbfc8a353fbe5bcf79710fcd876a84", "", "root"),
    #     (E_TAG_TAG_NAME, "axroedqxfanffqjniyjfrkococabogfq", "nostr-er-relay-co.co", "root"),
    #     (P_TAG_TAG_NAME, "omg56t48awudwg4h48llt62xdjlb0h9w"),
    #     (P_TAG_TAG_NAME, "989999sadkasjdj128e382jas9ds99d9", "carpenter-co.co"),
    #     (P_TAG_TAG_NAME, "gsgxsqcmgfqkawugzzcewyrhjqtbhaid", "ws://nostr-tr.pub/v2"),
    # ]
    # tags = parse_tags(tag_rows)
    content = "Hello there Nostr! Don't mind me, just testing.."
    event = generate_event(content=content)
    print(event.sig, len(event.sig))
    await write_event(event=event)
    stored_event_dict = await fetch_event(event_id=event.id)
    assert stored_event_dict
    stored_event = Event(**stored_event_dict)  # type: ignore
    assert_two_events_same(event, stored_event)
