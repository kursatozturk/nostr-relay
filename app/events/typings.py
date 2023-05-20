from typing import Literal, TypedDict

MarkerType = Literal["reply", "root", "mention"]
KindType = Literal[0, 1, 2, 3, 4, 5]
PositionalETagRow =  tuple[Literal["#e"], str, str]
MarkedETagRow = tuple[Literal["#e"], str, str, MarkerType]
ETagRow =PositionalETagRow | MarkedETagRow
PTagRow = tuple[Literal["#p"], str, str]


class EventDBDict(TypedDict):
    id: str
    pubkey: str
    created_at: int
    kind: KindType
    content: str
    sig: str


class EventNostrDict(EventDBDict):
    tags: list[ETagRow | PTagRow] | None
