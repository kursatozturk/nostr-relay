from typing import Any

from events.typings import EventDBDict

EVENT_TABLE_NAME = "event"
EVENT_FIELDS = ["id", "pubkey", "created_at", "kind", "content", "sig"]

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


def generate_sql_schema_e_tag() -> str:
    return """
    CREATE TYPE marker_type AS ENUM ('reply', 'root', 'mention');
    CREATE TABLE e_tag (
      e_id SERIAL PRIMARY KEY,
      associated_event CHAR(32) REFERENCES event(id),
      event_id VARCHAR(32),
      relay_url TEXT,
      marker marker_type
    );
  """


def generate_sql_schem_p_tag() -> str:
    return """
    CREATE TABLE p_tag (
      p_id SERIAL PRIMARY KEY,
      associated_event CHAR(32) REFERENCES event(id),
      pubkey VARCHAR(32),
      relay_url TEXT
    );
  """


def generate_sql_schema_event() -> str:
    return """
    CREATE TABLE event (
        id CHAR(32) PRIMARY KEY,
        pubkey CHAR(32),
        created_at BIGINT,
        kind INT,
        content TEXT,
        sig CHAR(64)
    );
    """


def clean_out_db() -> str:
    return """
  DROP TABLE e_tag;
  DROP TABLE p_tag;
  DROP TYPE marker_type;
  DROP TABLE event;
  DROP TYPE kinds;
  """
