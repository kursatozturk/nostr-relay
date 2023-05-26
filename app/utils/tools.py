from typing import Awaitable, Callable, Hashable, Iterable, Type, TypeVar

T = TypeVar("T")
_K = TypeVar("_K", bound=Hashable)


def flat_list(arr: Iterable[Iterable[T]]) -> list[T]:
    return [a for sl in arr for a in sl]


def flat_tuple(arr: Iterable[Iterable[T]]) -> tuple[T, ...]:
    return tuple(a for sl in arr for a in sl)


def group_by(arr: list[T], key_getter: Callable[[T], _K], /) -> dict[_K, list[T]]:
    grouped_items: dict[_K, list[T]] = {}
    for item in arr:
        key = key_getter(item)
        group = grouped_items.setdefault(key, [])
        group.append(item)
        grouped_items[key] = group
    return grouped_items


async def surpress_exc_coroutine(coro: Awaitable[T], exc: Type[BaseException]) -> T | None:
    try:
        return await coro
    except exc:
        pass
    return None
