from typing import Literal, TypeAlias, TypeGuard


MarkerType: TypeAlias = Literal["reply", "root", "mention"]

# tag "e", event_id
ETagRowBase = tuple[Literal["e"], str]
EtagRowWithRelay = tuple[*ETagRowBase, str]
MarkedETagRow = tuple[*EtagRowWithRelay, MarkerType]
ETagRow: TypeAlias = ETagRowBase | EtagRowWithRelay | MarkedETagRow

def e_tag_has_relay(e_tag: ETagRow) -> TypeGuard[EtagRowWithRelay | MarkedETagRow]:
    # Unfortunately, linters and type checker does not recognize
    # row[2] if len(e_tag) > 2 else None statement
    # I had to manually write out a TypeGuard
    return len(e_tag) > 2


# PositionalETagRow: TypeAlias = tuple[Literal["e"], str, str]
# MarkedETagRow: TypeAlias = tuple[Literal["e"], str, str, MarkerType]
# ETagRow: TypeAlias = PositionalETagRow | MarkedETagRow
