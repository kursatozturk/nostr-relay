from events.data import Kind, Marker


def generate_sql_schema_e_tag():
    return f"""
    CREATE TYPE marker_type AS ENUM {tuple(str(m.value) for m in Marker)};
    CREATE TABLE e_tag (
      e_id SERIAL PRIMARY KEY,
      associated_event CHAR(32) REFERENCES event(id),
      event_id VARCHAR(32),
      relay_url TEXT,
      marker marker_type
    );
  """


def generate_sql_schem_p_tag():
    return f"""
    CREATE TABLE p_tag (
      p_id SERIAL PRIMARY KEY,
      associated_event CHAR(32) REFERENCES event(id),
      pubkey VARCHAR(32),
      relay_url TEXT
    );
  """


def generate_sql_schema_event():
    return f"""
    CREATE TYPE kinds AS ENUM {tuple(str(k.value) for k in Kind)};
    CREATE TABLE event (
        id CHAR(32) PRIMARY KEY,
        pubkey CHAR(32),
        created_at BIGINT,
        kind kinds,
        content TEXT,
        sig CHAR(64)
    );
    """
