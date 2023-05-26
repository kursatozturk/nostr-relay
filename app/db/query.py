from typing import Callable, Sequence, TypeVar, overload


from db.typings import DBConnection, RunnableQuery


def returnAsTuple(x: tuple) -> tuple:
    return x


T = TypeVar("T")


def ident(_: tuple) -> tuple:
    return _


@overload
async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]],
    parallel: bool = False,
    conn: DBConnection,
) -> dict:
    ...


@overload
async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]] = [],
    return_queries: dict[str, tuple[RunnableQuery, Sequence]],
    parallel: bool = False,
    data_converters: dict[str, Callable[[tuple], T]] = {"": ident},
    conn: DBConnection,
) -> dict[str, tuple[T, ...]]:
    ...


async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]] = [],
    return_queries: dict[str, tuple[RunnableQuery, Sequence]] = {},
    data_converters: dict[str, Callable[[tuple], T]] = {"": ident},
    parallel: bool = False,
    conn: DBConnection,
) -> dict[str, tuple[T, ...]]:
    """
    Runs batches of queries.
    @PARAMETERS
    no_return_queries: a sequence of runnable queries which is not expected to return data [[NO_RETURN]]
    return_queries: a named query Mapping. The naming is required to allow paralellized queries. [[RETURN]]

    NOTE:
        - It is not optimized for best performance, yet.
        - Parallelization is not implemented. parallel param has no effect on the execution
    """

    cur = conn.cursor()
    for q, v in no_return_queries:
        await cur.execute(q, v)
    results = {
        rname: tuple(convert(r) if (convert := data_converters.get(rname)) else r for r in await (await cur.execute(q, v)).fetchall())
        for rname, (q, v) in return_queries.items()
    }
    return results
