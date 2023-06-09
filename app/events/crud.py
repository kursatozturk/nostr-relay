from collections import deque
from itertools import groupby
from typing import Sequence

from db.core import connect_db_pool
from db.query import run_queries
from db.query_utils import (
    CountFunc,
    create_runnable_query,
    prepare_delete_q,
    prepare_equal_clause,
    prepare_gte_lte_clause,
    prepare_in_clause,
    prepare_insert_into,
    prepare_prefix_clause,
    prepare_select_statement,
    union_queries,
)
from db.typings import QueryComponents, RunnableQuery
from tags.data.e_tag import E_TAG_TAG_NAME
from tags.data.p_tag import P_TAG_TAG_NAME
from tags.db import (
    prepare_tag_filters,
    query_tags,
    write_tags,
)

from events.data import Event
from events.db import (
    EVENT_FIELDS,
    EVENT_TABLE_NAME,
    db_to_nostr,
)
from events.filters import Filters
from events.typings import EventDBDict, EventNostrDict, KindType


async def delete_event_by_kind_pubkey(kind: KindType, pubkey: str) -> None:
    kind_clause = prepare_equal_clause("kind")
    pubkey_clause = prepare_equal_clause("pubkey")
    delete_event_q = prepare_delete_q(EVENT_TABLE_NAME, (kind_clause, pubkey_clause))
    pool = connect_db_pool()
    async with pool.connection() as conn:
        # Db Will automatically delete the associated tags
        await run_queries(no_return_queries=[(delete_event_q, (kind, pubkey))], conn=conn)


async def fetch_event_by_kind_pubkey(kind: KindType, pubkey: str) -> EventDBDict | None:
    """
    Use this with replacable Event Kind Values only!
    (10000 <= kind < 20000)
    """
    kind_clause = prepare_equal_clause("kind")
    pubkey_clause = prepare_equal_clause("pubkey")
    select_event = prepare_select_statement((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS)
    q = create_runnable_query(select_event, EVENT_TABLE_NAME, (kind_clause, pubkey_clause))

    pool = connect_db_pool()
    async with pool.connection() as conn:
        response = await run_queries(return_queries={"events": (q, (kind, pubkey))}, data_converters={"events": db_to_nostr}, conn=conn)
        if response["events"]:
            return response["events"][0]
        else:
            return None


async def delete_events(pubkey: str, e_ids: Sequence[str]) -> None:
    pubkey_clause = prepare_equal_clause("pubkey")
    id_clause = prepare_in_clause("id", 1)
    delete_q = prepare_delete_q(EVENT_TABLE_NAME, (pubkey_clause, id_clause))
    pool = connect_db_pool()
    async with pool.connection() as conn:
        # Db Will automatically delete the associated tags
        await run_queries(no_return_queries=[(delete_q, (pubkey, e_ids))], conn=conn)


async def write_event(event: Event) -> None:
    insert_query = prepare_insert_into(
        EVENT_TABLE_NAME,
        EVENT_FIELDS,
    )
    # Save the Event
    pool = connect_db_pool()
    async with pool.connection() as conn:
        await run_queries(
            no_return_queries=[
                (
                    insert_query,
                    (
                        event.id,
                        event.pubkey,
                        event.created_at,
                        event.kind,
                        event.content,
                        event.sig,
                    ),
                )
            ],
            conn=conn,
        )
        await write_tags(event.id, event.tags, conn=conn)


def prepare_filter_clauses(f: Filters) -> tuple[Sequence[QueryComponents], Sequence[str | int]]:
    filter_queue: deque[QueryComponents] = deque()
    values: deque[str | int] = deque()
    if f.ids:
        id_filter = prepare_prefix_clause((EVENT_TABLE_NAME, "id"), prefixes=f.ids)
        filter_queue.append(id_filter)

    if f.authors:
        author_filter = prepare_prefix_clause((EVENT_TABLE_NAME, "pubkey"), prefixes=f.authors)
        filter_queue.append(author_filter)

    if f.kinds:
        kind_filter = prepare_in_clause((EVENT_TABLE_NAME, "kind"), value_count=len(f.kinds))
        filter_queue.append(kind_filter)
        values.extend(map(str, f.kinds))

    if f.since or f.until:
        btwn_filter = prepare_gte_lte_clause(
            (EVENT_TABLE_NAME, "created_at"),
            gte=f.since is not None,
            lte=f.until is not None,
        )
        if f.since:
            values.append(f.since)
        if f.until:
            values.append(f.until)

        filter_queue.append(btwn_filter)

    tag_q, tag_vals = prepare_tag_filters(f.tags)
    if tag_q:
        tag_filter = prepare_in_clause((EVENT_TABLE_NAME, "id"), q=tag_q)
        filter_queue.append(tag_filter)
        values.extend(tag_vals)

    return filter_queue, values


async def count_events(*filters: Filters) -> int:
    filter_queries: deque[RunnableQuery] = deque()
    filter_q_vals: deque[str | int] = deque()
    for f in filters:
        filter_queue, values = prepare_filter_clauses(f)

        select_statement = prepare_select_statement(["id"])
        query = create_runnable_query(
            select_statement, EVENT_TABLE_NAME, filter_queue, order_by=[((EVENT_TABLE_NAME, "created_at"), "DESC")], limit=f.limit
        )
        filter_queries.append(query)
        filter_q_vals.extend(values)

    from_t = union_queries(*filter_queries)
    selector = prepare_select_statement([], as_names={CountFunc("id", True): "event_count"})
    query = create_runnable_query(selector, from_t)
    pool = connect_db_pool()
    async with pool.connection() as conn:
        print(query.as_string(conn))
        query_results = await run_queries(
            return_queries={"count": (query, filter_q_vals)},
            conn=conn,
        )
        print(query_results)
        count_data = query_results["count"]
        event_count: int = count_data[0][0]
    return event_count


async def query_events(*filters: Filters) -> list[EventNostrDict]:
    filter_queries: deque[RunnableQuery] = deque()
    filter_q_vals: deque[str | int] = deque()
    for f in filters:
        filter_queue, values = prepare_filter_clauses(f)

        select_statement = prepare_select_statement(((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS))
        query = create_runnable_query(
            select_statement, EVENT_TABLE_NAME, filter_queue, order_by=[((EVENT_TABLE_NAME, "created_at"), "DESC")], limit=f.limit
        )
        filter_queries.append(query)
        filter_q_vals.extend(values)

    pool = connect_db_pool()
    query = union_queries(*filter_queries)
    async with pool.connection() as conn:
        print(query.as_string(conn))
        query_results = await run_queries(
            return_queries={"events": (query, filter_q_vals)},
            data_converters={"events": db_to_nostr},
            conn=conn,
        )
        events: Sequence[EventDBDict] = query_results["events"]
        event_ids = tuple(event["id"] for event in events)
        if not len(event_ids):
            return []

        tags = await query_tags(event_ids, conn=conn)

    event_e_tags = dict(groupby(sorted(tags.get(E_TAG_TAG_NAME, []), key=lambda e: e[0]), lambda e: e[0]))
    event_p_tags = dict(groupby(sorted(tags.get(P_TAG_TAG_NAME, []), key=lambda p: p[0]), lambda p: p[0]))
    return [
        EventNostrDict(
            **event,
            tags=[
                *event_e_tags.get(event["id"], []),  # type: ignore
                *event_p_tags.get(event["id"], []),  # type: ignore
            ],
        )
        for event in events
    ]


async def fetch_event(event_id: str) -> EventNostrDict | None:
    select_event = prepare_select_statement((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS)
    clause = prepare_equal_clause((EVENT_TABLE_NAME, "id"))
    event_query = create_runnable_query(select_event, EVENT_TABLE_NAME, clause)

    pool = connect_db_pool()
    async with pool.connection() as conn:
        query_results = await run_queries(
            return_queries={
                "events": (event_query, (event_id,)),
            },
            conn=conn,
        )
        events = [db_to_nostr(event) for event in query_results["events"]]
        if len(events) == 0:
            return None

        tags = await query_tags((event_id,), conn=conn)
    return EventNostrDict(**events[0], tags=[*tags.get(E_TAG_TAG_NAME, []), *tags.get(P_TAG_TAG_NAME, [])])
