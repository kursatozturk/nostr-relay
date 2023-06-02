import pytest
from db.core import _get_async_connection
from db.query_utils import (
    prepare_delete_q,
    prepare_equal_clause,
    prepare_in_clause,
    prepare_gte_lte_clause,
    prepare_prefix_clause,
    prepare_select_statement,
    prepare_insert_into,
    combine_or_clauses,
    create_runnable_query,
    union_queries,
)


@pytest.mark.asyncio
async def test_delete_query():
    conn = await _get_async_connection()
    table_name = "test_table"
    equal_clause = prepare_equal_clause(field_name="f1")
    gte_clause = prepare_gte_lte_clause(field_name="f2", gte=True)
    delete_q = prepare_delete_q(table_name=table_name, clauses=[equal_clause, gte_clause])
    q_str = delete_q.as_string(conn)
    assert q_str == 'DELETE FROM "test_table" WHERE "f1" = %s and "f2" >= %s'


@pytest.mark.asyncio
async def test_runnable_query():
    conn = await _get_async_connection()
    fields = ["f1", "f2", "f3", "f4", "f5"]
    order_by_field = "f2"
    table_name = "test_table"
    select_statement = prepare_select_statement(field_names=fields)
    equal_clause = prepare_equal_clause(field_name=fields[0])
    gte_clause = prepare_gte_lte_clause(field_name=fields[2], gte=True)
    runnable_q = create_runnable_query(
        select_statement=select_statement,
        from_t=table_name,
        where_clause=(equal_clause, gte_clause),
        order_by=[(order_by_field, "DESC")],
        limit=10,
    )
    q_str = runnable_q.as_string(conn)
    assert q_str == 'SELECT "f1","f2","f3","f4","f5" FROM "test_table" WHERE "f1" = %s and "f3" >= %s ORDER BY "f2" DESC LIMIT 10'

    select_statement = prepare_select_statement(field_names=fields)
    equal_clause = prepare_equal_clause(field_name=fields[2])
    lte_clause = prepare_gte_lte_clause(field_name=fields[1], lte=True)
    runnable_q_2 = create_runnable_query(
        select_statement=select_statement,
        from_t=table_name,
        where_clause=(equal_clause, lte_clause),
        order_by=[(fields[-1], "DESC")],
        limit=255,
    )
    q_str = runnable_q_2.as_string(conn)
    assert q_str == 'SELECT "f1","f2","f3","f4","f5" FROM "test_table" WHERE "f3" = %s and "f2" <= %s ORDER BY "f5" DESC LIMIT 255'

    union_q = union_queries(runnable_q, runnable_q_2)
    q_str = union_q.as_string(conn)
    assert q_str == (
        '((SELECT "f1","f2","f3","f4","f5" FROM "test_table" WHERE "f1" = %s and "f3" >= %s ORDER BY "f2" DESC LIMIT 10)'
        " UNION "
        '(SELECT "f1","f2","f3","f4","f5" FROM "test_table" WHERE "f3" = %s and "f2" <= %s ORDER BY "f5" DESC LIMIT 255))'
    )


@pytest.mark.asyncio
async def test_where_claus_utils():
    conn = await _get_async_connection()
    field_name = "field_name"
    equal_clause = prepare_equal_clause(field_name=field_name)
    clause_str = equal_clause.as_string(conn)
    assert clause_str == '"field_name" = %s'

    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = prepare_prefix_clause(field_name=field_name, prefixes=prefixes)
    clause_str = prefix_clause.as_string(conn)
    assert clause_str == "\"field_name\" SIMILAR TO '(p1|p2|p3|p4)%%'"

    in_values = ["v1", "v2", "v3", "v4", "v5"]
    in_caluse = prepare_in_clause(field_name=field_name, value_count=len(in_values))
    clause_str = in_caluse.as_string(conn)
    assert clause_str == '"field_name" IN (%s,%s,%s,%s,%s)'
    lte_clause = prepare_gte_lte_clause(field_name=field_name, lte=True)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    gte_clause = prepare_gte_lte_clause(field_name=field_name, gte=True)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_lte_clause = prepare_gte_lte_clause(field_name=field_name, lte=True, gte=True)
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s and "field_name" <= %s'

    or_clauses = combine_or_clauses(equal_clause, in_caluse, lte_clause, gte_clause)
    clause_str = or_clauses.as_string(conn)
    assert clause_str == '("field_name" = %s or "field_name" IN (%s,%s,%s,%s,%s) or "field_name" <= %s or "field_name" >= %s)'


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

    select_with_ns = prepare_select_statement(field_names=namespaced_fields, as_names={"valo": "tag"})
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5",\'valo\' as "tag"'

    select_with_ns = prepare_select_statement(
        field_names=namespaced_fields,
        as_names={"valo": "tag"},
        ordering=("tag", *(f"ns.{f}" for f in fields)),
    )
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT \'valo\' as "tag","ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'


@pytest.mark.asyncio
async def test_insert_statements() -> None:
    conn = await _get_async_connection()
    table_name = "Table1"
    fields = ["f1", "f2", "f3", "f4", "f5"]

    insert_stmnt = prepare_insert_into(table_name=table_name, field_names=fields)
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' "(%s,%s,%s,%s,%s)"

    insert_stmnt = prepare_insert_into(table_name=table_name, field_names=fields, value_tuple_count=2)
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' "(%s,%s,%s,%s,%s)," "(%s,%s,%s,%s,%s)"
