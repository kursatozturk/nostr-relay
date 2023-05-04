from typing import Literal, Sequence, TypedDict, cast

from db.core import get_nostr_db_pool
from db.query import (
    PLACE_HOLDER,
    construct_equal_clause,
    construct_insert_into,
    construct_select_statement,
    construct_select_from_query,
)
from events.data import E_Tag, Event, Filters, Kind, P_Tag
from psycopg import AsyncConnection
from psycopg.rows import dict_row

EVENT_TABLE_NAME = "event"
EVENT_FIELDS = ["id", "pubkey", "created_at", "kind", "content", "sig"]
E_TAG_TABLE_NAME = "e_tag"
E_TAG_FIELDS = ["event_id", "relay_url", "marker"]
E_TAG_INSERT_FIELDS = ["associated_event", *E_TAG_FIELDS]
E_TAG_ORDERING = tuple(f"{E_TAG_TABLE_NAME}.{fname}" for fname in E_TAG_FIELDS)

P_TAG_TABLE_NAME = "p_tag"
P_TAG_FIELDS = ["pubkey", "relay_url"]
P_TAG_INSERT_FIELDS = ["associated_event", *P_TAG_FIELDS]
P_TAG_ORDERING = tuple(f"{P_TAG_TABLE_NAME}.{fname}" for fname in P_TAG_FIELDS)

ETagRow = tuple[Literal["e"], str, str, str, str | None]
PTagRow = tuple[str, str, str]


def flat_list(l: Sequence[Sequence]) -> list:
    return [a for sl in l for a in sl]


class EventDict(TypedDict):
    id: str
    pubkey: str
    created_at: int
    kind: Kind
    content: str
    sig: str


async def write_event(event: Event):
    pool = get_nostr_db_pool()
    async with pool.connection() as conn:
        insert_query = construct_insert_into(
            EVENT_TABLE_NAME,
            EVENT_FIELDS,
            value_list=[tuple(PLACE_HOLDER for _ in EVENT_FIELDS)],
        )
        cur = conn.cursor()
        await cur.execute(
            insert_query,
            (
                event.id,
                event.pubkey,
                event.created_at,
                str(event.kind.value),
                event.content,
                event.sig,
            ),
        )
        e_tags = list(
            (
                event.id,
                tag.event_id,
                tag.recommended_relay_url,
                tag.marker.value if tag.marker else None,
            )
            for tag in event.tags
            if type(tag) is E_Tag
        )
        p_tags = list(
            (event.id, tag.pubkey, tag.recommended_relay_url)
            for tag in event.tags
            if type(tag) is P_Tag
        )
        async with conn.pipeline():
            cur = conn.cursor()
            e_tag_q = construct_insert_into(
                E_TAG_TABLE_NAME,
                E_TAG_INSERT_FIELDS,
                (tuple(PLACE_HOLDER for _ in row) for row in e_tags),
            )
            await cur.execute(e_tag_q, flat_list(e_tags))
            p_tag_q = construct_insert_into(
                P_TAG_TABLE_NAME,
                P_TAG_INSERT_FIELDS,
                (tuple(PLACE_HOLDER for _ in row) for row in p_tags),
            )

            await cur.execute(p_tag_q, flat_list(p_tags))


def filter_events(filters: Filters):
    ...


async def fetch_event(event_id: str, *, conn: AsyncConnection | None = None):
    if conn is None:
        pool = get_nostr_db_pool()
        conn = pool.connection()

    async with conn as con:
        select_event = construct_select_statement(
            (EVENT_TABLE_NAME, f) for f in EVENT_FIELDS
        )
        clause = construct_equal_clause((EVENT_TABLE_NAME, "id"))
        event_query = construct_select_from_query(
            select_event, EVENT_TABLE_NAME, clause
        )
        cur = con.cursor("event_cur", row_factory=dict_row)
        event_row = cast(
            EventDict,
            await (await cur.execute(query=event_query, params=(event_id,))).fetchone(),
        )
        if event_row is None:
            return
        select_tags = construct_select_statement(
            ((E_TAG_TABLE_NAME, f) for f in E_TAG_FIELDS),
            as_names={"e": "tag"},
            ordering=("tag", *E_TAG_ORDERING),
        )
        clause = construct_equal_clause((E_TAG_TABLE_NAME, "associated_event"))
        e_query = construct_select_from_query(select_tags, E_TAG_TABLE_NAME, clause)
        e_tag_rows = cast(
            list[ETagRow],
            await (await con.execute(query=e_query, params=(event_id,))).fetchall(),
        )

        select_tags = construct_select_statement(
            ((P_TAG_TABLE_NAME, f) for f in P_TAG_FIELDS),
            as_names={"p": "tag"},
            ordering=("tag", *P_TAG_ORDERING),
        )
        clause = construct_equal_clause(
            (P_TAG_TABLE_NAME, "associated_event"), PLACE_HOLDER
        )
        p_query = construct_select_from_query(select_tags, P_TAG_TABLE_NAME, clause)
        p_tag_rows = cast(
            list[PTagRow],
            await (await con.execute(query=p_query, params=(event_id,))).fetchall(),
        )
        return Event(**event_row, tags=[*e_tag_rows, *p_tag_rows])  # type: ignore
