from typing import Any, Iterable
from db.core import get_nostr_db_pool
from events.data import E_Tag, Event, P_Tag
from psycopg import AsyncConnection, sql


async def write_event(event: Event):
    pool = get_nostr_db_pool()
    async with pool.connection() as conn:
        await conn.execute(
            """ INSERT INTO event
        (id, pubkey, created_at, kind, content, sig)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                event.id,
                event.pubkey,
                event.created_at,
                str(event.kind.value),
                event.content,
                event.sig,
            ),
        )
        e_tags = (
            (
                event.id,
                tag.event_id,
                tag.recommended_relay_url,
                tag.marker.value if tag.marker else None,
            )
            for tag in event.tags
            if type(tag) is E_Tag
        )
        p_tags = (
            (event.id, tag.pubkey, tag.recommended_relay_url)
            for tag in event.tags
            if type(tag) is P_Tag
        )
        async with conn.pipeline():
            cur = conn.cursor()
            await cur.executemany(
                """
                    INSERT INTO e_tag
                    (associated_event, event_id, relay_url, marker)
                    VALUES (%s, %s, %s, %s)
                """,
                e_tags,
            )
            await cur.executemany(
                """
                INSERT INTO p_tag
                (associated_event, pubkey, relay_url)
                VALUES (%s, %s, %s)
                """,
                p_tags,
            )


async def fetch_event(event_id: str, *, conn: AsyncConnection | None = None):
    # TODO: The query logic is completely wrong!
    if conn is None:
        pool = get_nostr_db_pool()
        conn = pool.connection()

    event: Event | None = None
    async with conn as con:
        cur = con.cursor()
        rows = await (
            await cur.execute(
                "SELECT e.pubkey, e.created_at, e.kind, e.content, e.sig, "
                "et.event_id, et.relay_url, et.marker, "
                "pt.pubkey, pt.relay_url "
                "FROM event e LEFT JOIN e_tag et ON e.id=et.associated_event "
                "LEFT JOIN p_tag pt ON e.id=pt.associated_event "
                "WHERE e.id = %s;",
                (event_id,),
            )
        ).fetchall()
        if len(rows):
            pubkey, created_at, kind, content, sig, *_ = rows[0]
            tags = [
                ("e", *row[5:8]) if row[5] is not None else ("p", *row[8:10])
                for row in rows
            ]
            event = Event(
                id=event_id,
                pubkey=pubkey,
                created_at=created_at,
                kind=kind,
                tags=tags,  # type: ignore
                content=content,
                sig=sig,
            )

    return event


async def query_tags(*, conn: AsyncConnection | None = None):
    # Literal Values
    field_names = ("event_id", "relay_url", "marker")
    table_name = "e_tag"
    id_prefixes = ["eab9c7fb4b34cb2f", "11bbfc8a353fbe5bcf7971"]

    # Templates
    prefix_q = sql.SQL("{fname} SIMILAR TO {p_regex}")

    # Prepared !Composables
    fields = sql.SQL(",").join(sql.Identifier(fname) for fname in field_names)
    p_regex = sql.Literal(f'({"|".join(id_prefixes)})%')

    # Template formatting
    id_filter = prefix_q.format(fname=sql.Identifier("event_id"), p_regex=p_regex)

    # Query building
    q = sql.SQL("SELECT {fields} from {table_name} WHERE {filters}").format(
        fields=fields,
        table_name=sql.Identifier(table_name),
        filters=sql.Composed([id_filter, sql.SQL("")]),
    )
    if conn is None:
        pool = get_nostr_db_pool()
        conn = pool.connection()

    async with conn as con:
        print(q.as_string(con))
        cur = await con.execute(q)
        rows = await cur.fetchall()
        print(rows)
