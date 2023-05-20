from typing import Callable, Hashable, Iterable, TypeVar


T = TypeVar("T")
_K = TypeVar("_K", bound=Hashable)


def flat_list(l: Iterable[Iterable[T]]) -> list[T]:
    return [a for sl in l for a in sl]


def group_by(arr: list[T], key_getter: Callable[[T], _K], /) -> dict[_K, list[T]]:
    grouped_items: dict[_K, list[T]] = {}
    for item in arr:
        key = key_getter(item)
        group = grouped_items.setdefault(key, [])
        group.append(item)
        grouped_items[key] = group
    return grouped_items
