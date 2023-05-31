from typing import Any

from events.typings import EventDBDict
from psycopg import sql

EVENT_TABLE_NAME = "event"
EVENT_FIELDS = ["id", "pubkey", "created_at", "kind", "content", "sig"]
EVENT_DB_FIELDS = [*EVENT_FIELDS, "source"]


def db_to_nostr(event_row: tuple[Any, ...]) -> EventDBDict:
    return EventDBDict(
        id=event_row[0],
        pubkey=event_row[1],
        created_at=event_row[2],
        kind=event_row[3],
        content=event_row[4],
        sig=event_row[5],
    )


# TODO: Write the up to date method for schemas


def generate_sql_schema_e_tag() -> sql.SQL:
    return sql.SQL(
        """
    CREATE TYPE marker_type AS ENUM ('reply', 'root', 'mention');
    CREATE TABLE e_tag (
      e_id SERIAL PRIMARY KEY,
      associated_event CHAR(64) REFERENCES event(id),
      event_id VARCHAR(64),
      relay_url TEXT,
      marker marker_type
    );
    CREATE INDEX "e_tag_event_id_index" ON e_tag (event_id);
  """
    )


def generate_sql_schem_p_tag() -> sql.SQL:
    return sql.SQL(
        """
    CREATE TABLE p_tag (
      p_id SERIAL PRIMARY KEY,
      associated_event CHAR(64) REFERENCES event(id),
      pubkey VARCHAR(64),
      relay_url TEXT
    );
    CREATE INDEX "p_tag_pubkey_index" ON p_tag (pubkey);
  """
    )


def generate_sql_schema_event() -> sql.SQL:
    return sql.SQL(
        """
    CREATE TABLE event (
        id CHAR(64) PRIMARY KEY,
        pubkey CHAR(64),
        created_at BIGINT,
        kind INT,
        content TEXT,
        sig CHAR(128)
    );
    CREATE INDEX "event_kind_pubkey_index" ON event (kind, pubkey);
    """
    )


def clean_out_db() -> sql.SQL:
    return sql.SQL(
        """
    DROP TABLE e_tag;
    DROP TABLE p_tag;
    DROP TYPE marker_type;
    DROP TABLE event;
    """
    )
