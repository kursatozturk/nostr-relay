from typing import Sequence
from db.query_utils import (
    create_runnable_query,
    prepare_delete_q,
    prepare_equal_clause,
    prepare_in_clause,
    prepare_insert_into,
    prepare_select_statement,
)
from db.typings import RunnableQuery
from tags.data.e_tag import E_Tag
from tags.data.e_tag import E_TAG_TAG_NAME
from tags.typings.e_tag import ETagRow, MarkerType
from common.tools import flat_tuple


E_TAG_TABLE_NAME = "e_tag"
E_TAG_FIELDS = ["event_id", "relay_url", "marker"]
E_TAG_DB_FIELDS = ["associated_event", *E_TAG_FIELDS]
E_TAG_ORDERING = tuple(f"{E_TAG_TABLE_NAME}.{fname}" for fname in E_TAG_FIELDS)


def db_to_e_tag(row: tuple[str, str, str, str, MarkerType] | tuple[str, str, str, str]) -> ETagRow:
    _, tag_name, event_id, relay_url, *marker = row
    if marker and marker[0]:
        return ("e", event_id, relay_url, marker[0])
    else:
        return ("e", event_id, relay_url)


def prepare_e_tag_db_write_query(associated_event_id: str, e_tags: Sequence[E_Tag]) -> tuple[RunnableQuery, Sequence[str | None]]:
    e_tag_q = prepare_insert_into(E_TAG_TABLE_NAME, E_TAG_DB_FIELDS, len(e_tags))
    e_tags_vals = flat_tuple(
        (
            associated_event_id,
            tag.event_id,
            tag.recommended_relay_url,
            tag.marker if tag.marker else None,
        )
        for tag in e_tags
    )
    return e_tag_q, e_tags_vals


def e_tag_filterer_query(event_ids: set[str]) -> tuple[RunnableQuery, set[str]]:
    e_tag_select = prepare_select_statement([(E_TAG_TABLE_NAME, "associated_event")])
    clause = prepare_in_clause((E_TAG_TABLE_NAME, "event_id"), len(event_ids))
    q = create_runnable_query(e_tag_select, E_TAG_TABLE_NAME, clause)
    return q, event_ids


def get_query_e_tags(associated_event_ids: Sequence[str]) -> tuple[RunnableQuery, Sequence[str]]:
    selector = prepare_select_statement(
        ((E_TAG_TABLE_NAME, f) for f in E_TAG_DB_FIELDS),
        as_names={E_TAG_TAG_NAME: "tag"},
        ordering=(
            f"{E_TAG_TABLE_NAME}.associated_event",
            "tag",
            *(f"{E_TAG_TABLE_NAME}.{f}" for f in E_TAG_FIELDS),
        ),
    )
    e_tag_event_clause = prepare_in_clause((E_TAG_TABLE_NAME, "associated_event"), len(associated_event_ids))
    q = create_runnable_query(selector, E_TAG_TABLE_NAME, e_tag_event_clause)
    return q, associated_event_ids


def prepare_delete_e_tags_q(associated_event_id: str | RunnableQuery) -> tuple[RunnableQuery, Sequence[str]]:
    vals: list[str] = []
    if isinstance(associated_event_id, RunnableQuery):
        eq_clause = prepare_equal_clause("associated_event_id", q=associated_event_id)
    else:
        eq_clause = prepare_equal_clause("associated_event_id")
        vals.append(associated_event_id)

    delete_q = prepare_delete_q(E_TAG_TABLE_NAME, (eq_clause,))
    return delete_q, vals
