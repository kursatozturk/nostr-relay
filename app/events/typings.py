from typing import Literal, TypedDict
from tags.typings import TagRow

KindType = Literal[0, 1, 2, 3, 4, 5]


class EventDBDict(TypedDict):
    id: str
    pubkey: str
    created_at: int
    kind: KindType
    content: str
    sig: str


class EventNostrDict(EventDBDict):
    tags: list[TagRow] | None
