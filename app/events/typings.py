from typing import TypedDict
from tags.typings import TagRow

KindType =  int # Literal[0, 1, 2, 3, 5]


class EventDBDict(TypedDict):
    id: str
    pubkey: str
    created_at: int
    kind: KindType
    content: str
    sig: str


class EventNostrDict(EventDBDict):
    tags: list[TagRow] | None
