from collections import deque
from contextlib import _AsyncGeneratorContextManager
from itertools import groupby
from typing import Any, Iterable, TypedDict, cast
from db.query_utils import combine_or_clauses
from db.typings import QueryComponents

from db.query import run_queries
from db.query_utils import (
    create_runnable_query,
    prepare_equal_clause,
    prepare_in_clause,
    prepare_insert_into,
    prepare_lte_gte_clause,
    prepare_prefix_clause,
    prepare_select_statement,
)
from events.data import Event
from events.db import (
    E_TAG_FIELDS,
    E_TAG_INSERT_FIELDS,
    E_TAG_ORDERING,
    E_TAG_TABLE_NAME,
    EVENT_FIELDS,
    EVENT_TABLE_NAME,
    P_TAG_FIELDS,
    P_TAG_INSERT_FIELDS,
    P_TAG_ORDERING,
    P_TAG_TABLE_NAME,
    db_to_nostr,
)
from events.filters import Filters
from events.typings import ETagRow, PTagRow
from psycopg import AsyncConnection
from tags import E_Tag, P_Tag
from tags.data.e_tag import db_to_e_tag
from tags.data.p_tag import db_to_p_tag
from utils.tools import flat_list


async def write_event(event: Event) -> None:
    insert_query = prepare_insert_into(
        EVENT_TABLE_NAME,
        EVENT_FIELDS,
    )
    # Save the Event
    await run_queries(
        no_return_queries=[
            (
                insert_query,
                (
                    event.id,
                    event.pubkey,
                    event.created_at,
                    str(event.kind),
                    event.content,
                    event.sig,
                ),
            )
        ]
    )

    e_tags = tuple(
        (
            event.id,
            tag.event_id,
            tag.recommended_relay_url,
            tag.marker if tag.marker else None,
        )
        for tag in event.tags
        if type(tag) is E_Tag
    )
    p_tags = tuple(
        (event.id, tag.pubkey, tag.recommended_relay_url)
        for tag in event.tags
        if type(tag) is P_Tag
    )

    e_tag_q = prepare_insert_into(E_TAG_TABLE_NAME, E_TAG_INSERT_FIELDS, len(e_tags))

    p_tag_q = prepare_insert_into(P_TAG_TABLE_NAME, P_TAG_INSERT_FIELDS, len(p_tags))

    await run_queries(
        no_return_queries=[(e_tag_q, flat_list(e_tags)), (p_tag_q, flat_list(p_tags))]
    )


async def filter_events(
    *filters: Filters,
    conn: _AsyncGeneratorContextManager[AsyncConnection[Any]] | None = None,
) -> list[Event]:
    filter_queue: deque = deque()
    values: list[str | int | float] = []
    if fids := flat_list(f.ids for f in filters if f.ids):
        id_filter = prepare_prefix_clause((EVENT_TABLE_NAME, "id"), prefixes=fids)
        filter_queue.append(id_filter)

    if fauthors := flat_list(f.authors for f in filters if f.authors):
        author_filter = prepare_prefix_clause(
            (EVENT_TABLE_NAME, "pubkey"), prefix_count=len(fauthors)
        )
        filter_queue.append(author_filter)
        values.extend(fauthors)

    if fkinds := flat_list(f.kinds for f in filters if f.kinds):
        kind_filter = prepare_in_clause(
            (EVENT_TABLE_NAME, "kind"), value_count=len(fkinds)
        )
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

    if f_e_tags := flat_list(f.e_tag for f in filters if f.e_tag):
        # Prepare e_tag query
        e_tag_select = prepare_select_statement(
            [(E_TAG_TABLE_NAME, "associated_event")]
        )
        e_tag_in_clause = prepare_in_clause(
            (E_TAG_TABLE_NAME, "event_id"), len(f_e_tags)
        )
        q = create_runnable_query(e_tag_select, E_TAG_TABLE_NAME, e_tag_in_clause)

        # now use the result of the q to have "IN" clause
        e_tag_filter = prepare_in_clause((EVENT_TABLE_NAME, "id"), q=q)
        filter_queue.append(e_tag_filter)
        values.extend(f_e_tags)

    if f_p_tags := flat_list(f.p_tag for f in filters if f.p_tag):
        # Prepare p_tag query
        p_tag_select = prepare_select_statement(
            [(P_TAG_TABLE_NAME, "associated_event")]
        )
        p_tag_in_clause = prepare_in_clause(
            (P_TAG_TABLE_NAME, "pubkey"), len(f_p_tags)
        )
        q = create_runnable_query(p_tag_select, P_TAG_TABLE_NAME, p_tag_in_clause)

        # now use the result of the q to have "IN" clause
        p_tag_filter = prepare_in_clause((EVENT_TABLE_NAME, "id"), q=q)
        filter_queue.append(p_tag_filter)
        values.extend(f_p_tags)

    select_statement = prepare_select_statement(
        ((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS)
    )
    query = create_runnable_query(select_statement, EVENT_TABLE_NAME, filter_queue)
    query_results = await run_queries(
        return_queries={"events": (query, values)},
        conn=conn,
    )
    events = [db_to_nostr(event) for event in query_results["events"]]
    event_ids = tuple(event["id"] for event in events)
    if not len(event_ids):
        return []

    in_clause = prepare_in_clause(
        (E_TAG_TABLE_NAME, "associated_event"), value_count=1  # len(event_ids)
    )
    selector = prepare_select_statement(
        ((E_TAG_TABLE_NAME, f) for f in E_TAG_INSERT_FIELDS),
        as_names={"#e": "tag"},
        ordering=(
            f"{P_TAG_TABLE_NAME}.associated_event",
            "tag",
            *(f"{E_TAG_TABLE_NAME}.{f}" for f in E_TAG_FIELDS),
        ),
    )
    e_query = create_runnable_query(selector, E_TAG_TABLE_NAME, in_clause)

    in_clause = prepare_in_clause(
        (P_TAG_TABLE_NAME, "associated_event"), value_count=1  # len(event_ids)
    )

    selector = prepare_select_statement(
        ((P_TAG_TABLE_NAME, f) for f in P_TAG_INSERT_FIELDS),
        as_names={"#p": "tag"},
        ordering=(
            f"{P_TAG_TABLE_NAME}.associated_event",
            "tag",
            *(f"{P_TAG_TABLE_NAME}.{f}" for f in P_TAG_FIELDS),
        ),
    )
    p_query = create_runnable_query(selector, P_TAG_TABLE_NAME, in_clause)

    tags = await run_queries(
        return_queries={"#p": (p_query, (event_ids,)), "#e": (e_query, (event_ids,))},
        data_converters={"#p": db_to_p_tag, "#e": db_to_e_tag},
        conn=conn,
    )
    event_e_tags = dict(
        groupby(sorted(tags.get("#e", []), key=lambda e: e[0]), lambda e: e[0])
    )
    event_p_tags = dict(
        groupby(sorted(tags.get("#p", []), key=lambda p: p[0]), lambda p: p[0])
    )
    print("@" * 100)
    print(tags)
    print("#" * 100)
    print(event_e_tags)
    print("#" * 100)
    print(event_p_tags)
    print("#" * 100)
    return [
        Event(
            **event,
            tags=[
                *event_e_tags.get(event["id"], []),  # type: ignore
                *event_p_tags.get(event["id"], []),  # type: ignore
            ],
        )
        for event in events
    ]


async def fetch_event(
    event_id: str,
    *,
    conn: _AsyncGeneratorContextManager[AsyncConnection[Any]] | None = None,
) -> Event | None:
    select_event = prepare_select_statement((EVENT_TABLE_NAME, f) for f in EVENT_FIELDS)
    clause = prepare_equal_clause((EVENT_TABLE_NAME, "id"))
    event_query = create_runnable_query(select_event, EVENT_TABLE_NAME, clause)

    query_results = await run_queries(
        return_queries={
            "events": (event_query, (event_id,)),
        },
        conn=conn,
    )
    events = [db_to_nostr(event) for event in query_results["events"]]
    if len(events) == 0:
        return None

    select_tags = prepare_select_statement(
        [(E_TAG_TABLE_NAME, f) for f in E_TAG_INSERT_FIELDS],
        as_names={"#e": "tag"},
        ordering=(f"{E_TAG_TABLE_NAME}.associated_event", "tag", *E_TAG_ORDERING),
    )
    clause = prepare_equal_clause((E_TAG_TABLE_NAME, "associated_event"))
    e_query = create_runnable_query(select_tags, E_TAG_TABLE_NAME, clause)

    select_tags = prepare_select_statement(
        [(P_TAG_TABLE_NAME, f) for f in P_TAG_INSERT_FIELDS],
        as_names={"#p": "tag"},
        ordering=(f"{P_TAG_TABLE_NAME}.associated_event", "tag", *P_TAG_ORDERING),
    )
    clause = prepare_equal_clause((P_TAG_TABLE_NAME, "associated_event"))
    p_query = create_runnable_query(select_tags, P_TAG_TABLE_NAME, clause)

    tags = cast(
        dict[str, Iterable[E_Tag | P_Tag]],
        await run_queries(
            return_queries={"#e": (e_query, (event_id,)), "#p": (p_query, (event_id,))},
            data_converters={"#e": db_to_e_tag, "#p": db_to_p_tag},
            conn=conn,
        ),
    )

    return Event(**events[0], tags=[*tags.get("#e", []), *tags.get("#p", [])])
