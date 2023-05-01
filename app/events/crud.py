from typing import Coroutine, Iterable, TypeVar

from db.core import get_nostr_db_pool
from events.data import E_Tag, Event, P_Tag
from psycopg import AsyncConnection


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
        e_tags: Iterable[E_Tag] = map(
            lambda tag: (
                event.id,
                tag.e_id,
                tag.recommended_relay_url,
                tag.marker.value if tag.marker else None,
            ),
            filter(lambda t: t.tag == "e", event.tags),
        )
        p_tags: Iterable[P_Tag] = map(
            lambda tag: (event.id, tag.pubkey, tag.recommended_relay_url),
            filter(lambda t: t.tag == "p", event.tags),
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


async def fetch_event(event_id: str, /, conn: AsyncConnection | None = None):
    if conn is None:
        pool = get_nostr_db_pool()
        conn = pool.connection()

    event: Event = None
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
                ["e", *row[5:8]] if row[5] is not None else ["p", *row[8:10]]
                for row in rows
            ]
            event = Event(
                pubkey=pubkey,
                created_at=created_at,
                kind=kind,
                tags=tags,
                content=content,
                sig=sig,
            )

    return event
