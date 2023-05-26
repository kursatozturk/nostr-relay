from collections import deque
from itertools import groupby
from typing import Sequence

from db.core import connect_db_pool
from db.query import run_queries
from db.query_utils import (
    combine_or_clauses,
    create_runnable_query,
    prepare_equal_clause,
    prepare_in_clause,
    prepare_insert_into,
    prepare_lte_gte_clause,
    prepare_prefix_clause,
    prepare_select_statement,
)
from db.typings import QueryComponents
from events.typings import EventDBDict, EventNostrDict
from tags.db.e_tag import E_TAG_TAG_NAME
from tags.db.p_tag import P_TAG_TAG_NAME
from utils.tools import flat_list

from events.data import Event
from events.db import (
    EVENT_FIELDS,
    EVENT_TABLE_NAME,
    db_to_nostr,
)
from tags.db import (
    prepare_tag_filters,
    query_tags,
    write_tags,
)
from events.filters import Filters


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


async def query_events(*filters: Filters) -> list[EventNostrDict]:
    filter_queue: deque = deque()
    values: list[str | int | float] = []
    if fids := flat_list(f.ids for f in filters if f.ids):
        id_filter = prepare_prefix_clause((EVENT_TABLE_NAME, "id"), prefixes=fids)
        filter_queue.append(id_filter)

    if fauthors := flat_list(f.authors for f in filters if f.authors):
        author_filter = prepare_prefix_clause((EVENT_TABLE_NAME, "pubkey"), prefix_count=len(fauthors))
        filter_queue.append(author_filter)
        values.extend(fauthors)

    if fkinds := flat_list(f.kinds for f in filters if f.kinds):
        kind_filter = prepare_in_clause((EVENT_TABLE_NAME, "kind"), value_count=len(fkinds))
        filter_queue.append(kind_filter)
        values.extend(map(str, fkinds))

    if created_at_fs := [(f.since, f.until) for f in filters if (f.since or f.until)]:
        c_values: list[float | int] = []
        clauses: list[QueryComponents] = []
        for since, until in created_at_fs:
            btwn_filter = prepare_lte_gte_clause(
                (EVENT_TABLE_NAME, "created_at"),
                gte=since is not None,
                lte=until is not None,
            )
            clauses.append(btwn_filter)
            if since:
                c_values.append(since)
            if until:
                c_values.append(until)

        filter_queue.append(combine_or_clauses(*clauses))
        values.extend(c_values)

    tag_q, tag_vals = prepare_tag_filters(
        e_tags=flat_list(f.e_tag for f in filters if f.e_tag), p_tags=flat_list(f.p_tag for f in filters if f.p_tag)
    )
    if tag_q:
        tag_filter = prepare_in_clause((EVENT_TABLE_NAME, "id"), q=tag_q)
        filter_queue.append(tag_filter)
        values.extend(tag_vals)

    select_statement = prepare_select_statement(((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS))
    query = create_runnable_query(select_statement, EVENT_TABLE_NAME, filter_queue)

    pool = connect_db_pool()
    async with pool.connection() as conn:
        query_results = await run_queries(
            return_queries={"events": (query, values)},
            data_converters={"events": db_to_nostr},
            conn=conn,
        )
        # events = [db_to_nostr(event) for event in query_results["events"]]
        events: Sequence[EventDBDict] = query_results["events"]
        event_ids = tuple(event["id"] for event in events)
        if not len(event_ids):
            return []

        tags = await query_tags(event_ids, conn=conn)

    event_e_tags = dict(groupby(sorted(tags.get(E_TAG_TAG_NAME, []), key=lambda e: e[0]), lambda e: e[0]))
    event_p_tags = dict(groupby(sorted(tags.get(P_TAG_TAG_NAME, []), key=lambda p: p[0]), lambda p: p[0]))
    print("@" * 100)
    print(tags)
    print("#" * 100)
    print(event_e_tags)
    print("#" * 100)
    print(event_p_tags)
    print("#" * 100)
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
