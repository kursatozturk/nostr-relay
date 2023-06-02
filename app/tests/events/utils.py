import datetime
import json
from hashlib import sha256

import secp256k1
from events.data import Event
from tags.data import Tag
from tags.data.base import BaseTag


def _generate_keypairs() -> tuple[secp256k1.PrivateKey, secp256k1.PublicKey]:
    privkey = secp256k1.PrivateKey()
    pubkey = privkey.pubkey
    assert pubkey is not None

    return privkey, pubkey


def serialize_event(pubkey: str, created_at: int, kind: int, tags: list[BaseTag], content: str):
    return json.dumps(
        [0, pubkey, created_at, kind, [tag.nostr_dict for tag in tags], content], separators=(",", ":"), ensure_ascii=False
    ).encode()


def generate_event(content: str | None = None, tags: list[BaseTag] | None = None, kind: int | None = None) -> Event:
    priv, pub = _generate_keypairs()
    event_dict = {
        "pubkey": pub.serialize().hex()[2:],  # Strip the 02 in the beginning
        "created_at": int(datetime.datetime.now().timestamp()),
        "kind": kind or 1,
        "tags": tags or [],
        "content": content or "Today is a good day for testing!",
    }
    serialized_event = serialize_event(
        event_dict["pubkey"], event_dict["created_at"], event_dict["kind"], event_dict["tags"], event_dict["content"]
    )
    event_id = sha256(serialized_event)
    sig = priv.schnorr_sign(event_id.digest(), None, True)
    event_dict["id"] = event_id.hexdigest()
    event_dict["sig"] = sig.hex()
    return Event(**event_dict)


def assert_tags_same(e1_tags: list[Tag], e2_tags: list[Tag]) -> None:
    ...


def assert_two_events_same(e1: Event, e2: Event) -> None:
    assert e1.id == e2.id, "ids are not a match!"
    assert e1.pubkey == e2.pubkey, "Pubkeys are not a match!"
    assert e1.content == e2.content, "Content is not a match!"
    assert e1.sig == e2.sig, "SIG is not a match!"
    assert e1.created_at == e2.created_at, "Created at is not a match"
    assert e1.kind == e2.kind, "kinds are not a match"
    assert_tags_same(e1.tags, e2.tags)
