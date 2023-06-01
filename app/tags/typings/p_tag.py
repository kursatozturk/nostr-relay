from typing import Literal, TypeGuard


PTagRowBase = tuple[Literal["p"], str]
PTagRowWithRelay = tuple[*PTagRowBase, str]
PTagRowWithpet_name = tuple[*PTagRowWithRelay, str]
PTagRow = PTagRowBase | PTagRowWithRelay | PTagRowWithpet_name


def p_tag_has_relay(p_tag: PTagRow) -> TypeGuard[PTagRowWithpet_name | PTagRowWithpet_name]:
    # Unfortunately, linters and type checker does not recognize
    # row[2] if len(e_tag) > 2 else None statement
    # I had to manually write out a TypeGuard
    return len(p_tag) > 2
