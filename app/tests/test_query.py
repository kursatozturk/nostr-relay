import pytest
from db.core import _get_async_connection
from db.query import (construct_in_clause, construct_lte_gte_clause,
                      construct_prefix_clause)


@pytest.mark.asyncio
async def test_clauses():
    conn = await _get_async_connection()
    field_name = "field_name"
    prefixes = ["p1", "p2", "p3", "p4"]
    prefix_clause = construct_prefix_clause(field_name=field_name, prefixes=prefixes)
    clause_str = prefix_clause.as_string(conn)
    print(clause_str)
    assert  clause_str == '"field_name" SIMILAR TO \'(p1|p2|p3|p4)%\''
    in_values = ["v1", "v2", "v3", "v4", "v5"]
    in_caluse = construct_in_clause(field_name=field_name, values=in_values)
    clause_str = in_caluse.as_string(conn)
    assert clause_str == "\"field_name\" IN ('v1','v2','v3','v4','v5')"
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte=250)
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= 250'
    lte_clause = construct_lte_gte_clause(field_name=field_name, lte='abc')
    clause_str = lte_clause.as_string(conn)
    assert clause_str == '"field_name" <= \'abc\''
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte=250)
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= 250'
    gte_clause = construct_lte_gte_clause(field_name=field_name, gte='abc')
    clause_str = gte_clause.as_string(conn)
    assert clause_str == '"field_name" >= \'abc\''
    gte_lte_clause = construct_lte_gte_clause(field_name=field_name, lte='val2', gte='val1')
    clause_str = gte_lte_clause.as_string(conn)
    assert clause_str == '"field_name" >= \'val1\' and "field_name" <= \'val2\''
