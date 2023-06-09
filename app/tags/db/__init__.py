from collections import deque
import itertools
from typing import Callable, Protocol, Sequence
from db.core import connect_db_pool

from db.query import run_queries
from db.query_utils import union_queries
from db.typings import DBConnection, RunnableQuery
from tags.data import Tag

from tags.data.e_tag import E_TAG_TAG_NAME
from tags.data.p_tag import P_TAG_TAG_NAME
from tags.typings import TagRow

from .e_tag import (
    E_TAG_DB_FIELDS,
    E_TAG_FIELDS,
    E_TAG_ORDERING,
    E_TAG_TABLE_NAME,
    db_to_e_tag,
    get_query_e_tags,
    prepare_delete_e_tags_q,
    prepare_e_tag_db_write_query,
    e_tag_filterer_query,
)
from .p_tag import (
    P_TAG_DB_FIELDS,
    P_TAG_FIELDS,
    P_TAG_ORDERING,
    P_TAG_TABLE_NAME,
    db_to_p_tag,
    get_query_p_tags,
    prepare_delete_p_tags_q,
    prepare_p_tag_db_write_query,
    prepare_p_tag_query,
)

__all__ = (
    "E_TAG_TABLE_NAME",
    "E_TAG_FIELDS",
    "E_TAG_DB_FIELDS",
    "E_TAG_ORDERING",
    "P_TAG_TABLE_NAME",
    "P_TAG_FIELDS",
    "P_TAG_DB_FIELDS",
    "P_TAG_ORDERING",
    "write_tags",
    "query_tags",
    "prepare_tag_filters",
    "prepare_delete_tags_query",
)

__wr_query_builder_map: dict[str, Callable[..., tuple[RunnableQuery, Sequence]]] = {
    "e": prepare_e_tag_db_write_query,
    "p": prepare_p_tag_db_write_query,
}

__del_query_builder_map: dict[str, Callable[..., tuple[RunnableQuery, Sequence]]] = {
    "e": prepare_delete_e_tags_q,
    "p": prepare_delete_p_tags_q,
}


class __Q_BUILDERS(Protocol):
    def __call__(self, associated_event_ids: Sequence[str]) -> tuple[RunnableQuery, Sequence[str]]:
        ...


__query_builders: dict[str, __Q_BUILDERS] = {"e": get_query_e_tags, "p": get_query_p_tags}
__db_to_nostr: dict[str, Callable[[tuple], TagRow]] = {"e": db_to_e_tag, "p": db_to_p_tag}


async def write_tags(associated_event_id: str, tags: list[Tag], *, conn: DBConnection | None = None):
    try:
        grouped_tags: dict[str, list[Tag]] = {
            key: list(vals) for key, vals in itertools.groupby(sorted(tags, key=lambda tag: tag.tag), lambda tag: tag.tag)
        }
        queries = tuple(
            q_builder(associated_event_id, _tags) for tname, _tags in grouped_tags.items() if (q_builder := __wr_query_builder_map[tname])
        )

        if conn:
            await run_queries(no_return_queries=queries, conn=conn)
        else:
            pool = connect_db_pool()
            async with pool.connection() as conn:
                await run_queries(no_return_queries=queries, conn=conn)
    except KeyError as e:
        print(f"{e!r} | {e!s}")
        raise e


async def query_tags(associated_event_ids: Sequence[str], *, conn: DBConnection | None = None) -> dict[str, tuple[TagRow, ...]]:
    qs = {tag_name: q_builder(associated_event_ids=associated_event_ids) for tag_name, q_builder in __query_builders.items()}
    if conn:
        q_results = await run_queries(return_queries=qs, data_converters=__db_to_nostr, conn=conn)
    else:
        pool = connect_db_pool()
        async with pool.connection() as conn:
            q_results = await run_queries(return_queries=qs, data_converters=__db_to_nostr, conn=conn)

    return q_results


def prepare_tag_filters(tags: dict[str, set[str]]) -> tuple[RunnableQuery | None, Sequence[str]]:
    qs: deque[RunnableQuery] = deque()
    vals: deque[str] = deque()
    if e_tags := tags.get(E_TAG_TAG_NAME):
        e_tag_filters, e_tag_vals = e_tag_filterer_query(event_ids=e_tags)
        qs.append(e_tag_filters)
        vals.extend(e_tag_vals)
    if p_tags := tags.get(P_TAG_TAG_NAME):
        p_tag_filters, p_tag_vals = prepare_p_tag_query(pubkeys=p_tags)
        qs.append(p_tag_filters)
        vals.extend(p_tag_vals)
    if qs:
        q = union_queries(*qs)
        return q, vals
    return None, vals


def prepare_delete_tags_query(
    associated_event_id: str | RunnableQuery, *, selective_tags: set[str] | None = None
) -> dict[str, tuple[RunnableQuery, Sequence]]:
    if selective_tags is None:
        selective_tags = {t for t in __del_query_builder_map.keys()}
    return {
        tag_name: q_builder(associated_event_id=associated_event_id)
        for tag_name, q_builder in __del_query_builder_map.items()
        if tag_name in selective_tags
    }
