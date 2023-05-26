from typing import Literal, TypeAlias


MarkerType: TypeAlias = Literal["reply", "root", "mention"]
PositionalETagRow: TypeAlias = tuple[Literal["e"], str, str]
MarkedETagRow: TypeAlias = tuple[Literal["e"], str, str, MarkerType]
ETagRow: TypeAlias = PositionalETagRow | MarkedETagRow
