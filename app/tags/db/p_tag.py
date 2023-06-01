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
from tags.data.p_tag import P_TAG_TAG_NAME
from tags.typings.p_tag import PTagRow
from common.tools import flat_tuple

from tags.data.p_tag import P_Tag

P_TAG_TABLE_NAME = "p_tag"
P_TAG_FIELDS = ["pubkey", "relay_url", "pet_name"]
P_TAG_DB_FIELDS = ["associated_event", *P_TAG_FIELDS]
P_TAG_ORDERING = tuple(f"{P_TAG_TABLE_NAME}.{fname}" for fname in P_TAG_FIELDS)


def db_to_p_tag(row: tuple[str, str, str, str, str]) -> PTagRow:
    _, tag_name, pubkey, relay_url, pet_name = row
    return ("p", pubkey, relay_url, pet_name)


def prepare_p_tag_db_write_query(associated_event_id: str, p_tags: Sequence[P_Tag]) -> tuple[RunnableQuery, Sequence[str | None]]:
    p_tag_q = prepare_insert_into(P_TAG_TABLE_NAME, P_TAG_DB_FIELDS, len(p_tags))
    p_tag_vals = flat_tuple((associated_event_id, tag.pubkey, tag.recommended_relay_url, tag.pet_name) for tag in p_tags)
    return p_tag_q, p_tag_vals


def prepare_p_tag_query(pubkeys: set[str]) -> tuple[RunnableQuery, set[str]]:
    p_tag_select = prepare_select_statement([(P_TAG_TABLE_NAME, "associated_event")])
    clause = prepare_in_clause((P_TAG_TABLE_NAME, "pubkey"), len(pubkeys))
    q = create_runnable_query(p_tag_select, P_TAG_TABLE_NAME, clause)
    return q, pubkeys


def get_query_p_tags(associated_event_ids: Sequence[str]) -> tuple[RunnableQuery, Sequence[str]]:
    selector = prepare_select_statement(
        ((P_TAG_TABLE_NAME, f) for f in P_TAG_DB_FIELDS),
        as_names={P_TAG_TAG_NAME: "tag"},
        ordering=(
            f"{P_TAG_TABLE_NAME}.associated_event",
            "tag",
            *(f"{P_TAG_TABLE_NAME}.{f}" for f in P_TAG_FIELDS),
        ),
    )
    clause = prepare_in_clause((P_TAG_TABLE_NAME, "associated_event"), len(associated_event_ids))
    q = create_runnable_query(selector, P_TAG_TABLE_NAME, clause)
    return q, associated_event_ids


def prepare_delete_p_tags_q(associated_event_id: str | RunnableQuery) -> tuple[RunnableQuery, Sequence[str]]:
    vals: list[str] = []
    if isinstance(associated_event_id, RunnableQuery):
        eq_clause = prepare_equal_clause("associated_event_id", q=associated_event_id)
    else:
        eq_clause = prepare_equal_clause("associated_event_id")
        vals.append(associated_event_id)

    delete_q = prepare_delete_q(P_TAG_TABLE_NAME, (eq_clause,))
    return delete_q, vals
