import pytest
from db.core import _get_async_connection
from db.query import (
    PLACE_HOLDER,
    construct_equal_clause,
    construct_in_clause,
    construct_lte_gte_clause,
    construct_prefix_clause,
    construct_select_statement,
    construct_insert_into
)


@pytest.mark.asyncio
async def test_clauses():
    conn = await _get_async_connection()
    field_name = "field_name"
    equal_clause = construct_equal_clause(field_name=field_name, value="VALUE-STRANDER")
    clause_str = equal_clause.as_string(conn)
    assert clause_str == "\"field_name\" = 'VALUE-STRANDER'"
    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = construct_prefix_clause(field_name=field_name, prefixes=prefixes)
    clause_str = prefix_clause.as_string(conn)
    assert clause_str == "\"field_name\" SIMILAR TO '(p1|p2|p3|p4)%'"
    in_values = ["v1", "v2", "v3", "v4", "v5"]
    in_caluse = construct_in_clause(field_name=field_name, values=in_values)
    clause_str = in_caluse.as_string(conn)
    assert clause_str == "\"field_name\" IN ('v1','v2','v3','v4','v5')"
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte=250)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= 250'
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte="abc")
    clause_str = lte_clause.as_string(conn)
    assert clause_str == "\"field_name\" <= 'abc'"
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte=250)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= 250'
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte="abc")
    clause_str = gte_clause.as_string(conn)
    assert clause_str == "\"field_name\" >= 'abc'"
    gte_lte_clause = construct_lte_gte_clause(
        field_name=field_name, lte="val2", gte="val1"
    )
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == "\"field_name\" >= 'val1' and \"field_name\" <= 'val2'"

    fields = ["f1", "f2", "f3", "f4", "f5"]
    select_statement = construct_select_statement(field_names=fields)
    select_str = select_statement.as_string(conn)
    assert select_str == 'SELECT "f1","f2","f3","f4","f5"'
    namespaced_fields = [("ns", f) for f in fields]
    select_with_ns = construct_select_statement(field_names=namespaced_fields)
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'


@pytest.mark.asyncio
async def test_clauses_with_placeholders():
    conn = await _get_async_connection()
    field_name = "field_name"
    equal_clause = construct_equal_clause(field_name=field_name, value=PLACE_HOLDER)
    clause_str = equal_clause.as_string(conn)
    assert clause_str == '"field_name" = %s'
    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = construct_prefix_clause(
        field_name=field_name, prefix_count=len(prefixes)
    )
    clause_str = prefix_clause.as_string(conn)
    assert clause_str == "\"field_name\" SIMILAR TO '(%s|%s|%s|%s)%'"
    in_values = ["v1", "v2", "v3", "v4", "v5"]
    in_caluse = construct_in_clause(field_name=field_name, value_count=len(in_values))
    clause_str = in_caluse.as_string(conn)
    assert clause_str == '"field_name" IN (%s,%s,%s,%s,%s)'
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte=PLACE_HOLDER)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte=PLACE_HOLDER)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= %s'
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte=PLACE_HOLDER)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte=PLACE_HOLDER)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s'
    gte_lte_clause = construct_lte_gte_clause(
        field_name=field_name, lte=PLACE_HOLDER, gte=PLACE_HOLDER
    )
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == '"field_name" >= %s and "field_name" <= %s'


@pytest.mark.asyncio
async def test_select_statements():
    conn = await _get_async_connection()

    fields = ["f1", "f2", "f3", "f4", "f5"]
    select_statement = construct_select_statement(field_names=fields)
    select_str = select_statement.as_string(conn)
    assert select_str == 'SELECT "f1","f2","f3","f4","f5"'
    namespaced_fields = [("ns", f) for f in fields]
    select_with_ns = construct_select_statement(field_names=namespaced_fields)
    select_str = select_with_ns.as_string(conn)
    assert select_str == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5"'

    select_with_ns = construct_select_statement(
        field_names=namespaced_fields, as_names={"valo": "tag"}
    )
    select_str = select_with_ns.as_string(conn)
    assert (
        select_str
        == 'SELECT "ns"."f1","ns"."f2","ns"."f3","ns"."f4","ns"."f5",\'valo\' as "tag"'
    )

    select_with_ns = construct_select_statement(
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
async def test_insert_statements():
    conn = await _get_async_connection()
    table_name = 'Table1'
    fields = ["f1", "f2", "f3", "f4", "f5"]
    vals = ["val1", "val2", "val3", "val4", "val5"]
    vals2 = ["val6", "val7", "val8", "val9", "val10"]
    plcs = [PLACE_HOLDER for _ in range(len(vals))]

    insert_stmnt = construct_insert_into(table_name=table_name, field_names=fields, value_list=[vals])
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "('val1','val2','val3','val4','val5')"

    insert_stmnt = construct_insert_into(table_name=table_name, field_names=fields, value_list=[plcs])
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "(%s,%s,%s,%s,%s)"

    insert_stmnt = construct_insert_into(table_name=table_name, field_names=fields, value_list=[vals, vals2])
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "('val1','val2','val3','val4','val5')," \
                         "('val6','val7','val8','val9','val10')"

    insert_stmnt = construct_insert_into(table_name=table_name, field_names=fields, value_list=[plcs, plcs])
    insert_stm = insert_stmnt.as_string(conn)
    assert insert_stm == 'INSERT INTO "Table1" ("f1","f2","f3","f4","f5") VALUES ' \
                         "(%s,%s,%s,%s,%s)," \
                         "(%s,%s,%s,%s,%s)"
