
from typing import Iterable, TypeVar


T = TypeVar("T")
def flat_list(l: Iterable[Iterable[T]]) -> list[T]:
    return [a for sl in l for a in sl]
