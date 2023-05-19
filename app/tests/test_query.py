import pytest
from db.core import _get_async_connection
from db.query_utils import (
    prepare_equal_clause,
    prepare_in_clause,
    prepare_lte_gte_clause,
    prepare_prefix_clause,
    prepare_select_statement,
    prepare_insert_into
)


@pytest.mark.asyncio
async def test_clauses():
    conn = await _get_async_connection()
    field_name = "field_name"
    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = prepare_prefix_clause(field_name=field_name, prefixes=prefixes)
    clause_str = prefix_clause.as_string(conn)
    assert clause_str == "\"field_name\" LIKE '(p1|p2|p3|p4)%%'"
    lte_clause = prepare_lte_gte_clause(field_name=field_name, lte=True)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    lte_clause = prepare_lte_gte_clause(field_name=field_name, lte=True)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == "\"field_name\" <= %s"
    gte_clause = prepare_lte_gte_clause(field_name=field_name, gte=True)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_clause = prepare_lte_gte_clause(field_name=field_name, gte=True)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == "\"field_name\" >= %s"
    gte_lte_clause = prepare_lte_gte_clause(
        field_name=field_name, lte=True, gte=True
    )
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == "\"field_name\" >= %s and \"field_name\" <= %s"

    fields = ["f1", "f2", "f3", "f4", "f5"]
    select_statement = prepare_select_statement(field_names=fields)
    select_str = select_statement.as_string(conn)
    assert select_str == 'SELECT "f1","f2","f3","f4","f5"'
    namespaced_fields = [("ns", f) for f in fields]
    select_with_ns = prepare_select_statement(field_names=namespaced_fields)
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'


@pytest.mark.asyncio
async def test_clauses_with_placeholders():
    conn = await _get_async_connection()
    field_name = "field_name"
    equal_clause = prepare_equal_clause(field_name=field_name)
    clause_str = equal_clause.as_string(conn)
    assert clause_str == '"field_name" = %s'
    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = prepare_prefix_clause(
        field_name=field_name, prefix_count=len(prefixes)
    )
    clause_str = prefix_clause.as_string(conn)
    assert clause_str == "\"field_name\" LIKE '(%s|%s|%s|%s)%%'"
    in_values = ["v1", "v2", "v3", "v4", "v5"]
    in_caluse = prepare_in_clause(field_name=field_name, value_count=len(in_values))
    clause_str = in_caluse.as_string(conn)
    assert clause_str == '"field_name" IN (%s,%s,%s,%s,%s)'
    lte_clause = prepare_lte_gte_clause(field_name=field_name, lte=True)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    lte_clause = prepare_lte_gte_clause(field_name=field_name, lte=True)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    gte_clause = prepare_lte_gte_clause(field_name=field_name, gte=True)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_clause = prepare_lte_gte_clause(field_name=field_name, gte=True)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_lte_clause = prepare_lte_gte_clause(
        field_name=field_name, lte=True, gte=True
    )
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s and "field_name" <= %s'


@pytest.mark.asyncio
async def test_select_statements():
    conn = await _get_async_connection()

    fields = ["f1", "f2", "f3", "f4", "f5"]
    select_statement = prepare_select_statement(field_names=fields)
    select_str = select_statement.as_string(conn)
    assert select_str == 'SELECT "f1","f2","f3","f4","f5"'
    namespaced_fields = [("ns", f) for f in fields]
    select_with_ns = prepare_select_statement(field_names=namespaced_fields)
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'

    select_with_ns = prepare_select_statement(
        field_names=namespaced_fields, as_names={"valo": "tag"}
    )
    select_str = select_with_ns.as_string(conn)
    assert (
        select_str
        == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5",\'valo\' as "tag"'
    )

    select_with_ns = prepare_select_statement(
        field_names=namespaced_fields,
        as_names={"valo": "tag"},
        ordering=("tag", *(f"ns.{f}" for f in fields)),
    )
    select_str = select_with_ns.as_string(conn)
    assert (
        select_str
        == 'SELECT \'valo\' as "tag","ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'
    )


@pytest.mark.asyncio
async def test_insert_statements() -> None:
    conn = await _get_async_connection()
    table_name = 'Table1'
    fields = ["f1", "f2", "f3", "f4", "f5"]

    insert_stmnt = prepare_insert_into(table_name=table_name, field_names=fields)
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "(%s,%s,%s,%s,%s)"

    insert_stmnt = prepare_insert_into(table_name=table_name, field_names=fields, value_tuple_count=2)
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "(%s,%s,%s,%s,%s)," \
                         "(%s,%s,%s,%s,%s)"
