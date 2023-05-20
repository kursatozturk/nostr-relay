from contextlib import _AsyncGeneratorContextManager
from typing import Any, Callable, Iterable, Sequence, TypeVar, overload

from db.core import connect_db_pool
from db.typings import DBConnection, RunnableQuery


def returnAsTuple(x: tuple) -> tuple:
    return x


T = TypeVar("T")
_K = TypeVar("_K", bound=Iterable[str])


@overload
async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]],
    parallel: bool = False,
    conn: _AsyncGeneratorContextManager[DBConnection] | None = None,
) -> None:
    ...


@overload
async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]] = [],
    return_queries: dict[str, tuple[RunnableQuery, Sequence]],
    parallel: bool = False,
    data_converters: dict[str, Callable[[tuple], Any]] = {},
    conn: _AsyncGeneratorContextManager[DBConnection] | None = None,
) -> dict[str, tuple[tuple | Any, ...]]:
    ...


async def run_queries(
    *,
    no_return_queries: Sequence[tuple[RunnableQuery, Sequence]] = [],
    return_queries: dict[str, tuple[RunnableQuery, Sequence]] = {},
    data_converters: dict[str, Callable[[tuple], Any]] = {},
    parallel: bool = False,
    conn: _AsyncGeneratorContextManager[DBConnection] | None = None,
) -> dict[str, tuple[tuple | Any, ...]] | None:
    """
    Runs batches of queries.
    @PARAMETERS
    no_return_queries: a sequence of runnable queries which is not expected to return data [[NO_RETURN]]
    return_queries: a named query Mapping. The naming is required to allow paralellized queries. [[RETURN]]

    NOTE:
        - It is not optimized for best performance, yet.
        - Parallelization is not implemented. parallel param has no effect on the execution
    """
    if conn is None:
        pool = connect_db_pool()
        conn = pool.connection()

    async with conn as con:
        cur = con.cursor()
        for q, v in no_return_queries:
            await cur.execute(q, v)
        results = {
            rname: tuple(
                convert(r) if (convert := data_converters.get(rname)) else r
                for r in await (await cur.execute(q, v)).fetchall()
            )
            for rname, (q, v) in return_queries.items()
        }
    return results
