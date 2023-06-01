from collections import OrderedDict
from typing import Iterable, Literal, Sequence

from psycopg import sql
from common.errors import ErrorTypes, InvalidMessageError

from db.typings import FieldName, QueryComponents, RunnableQuery


def create_runnable_query(
    select_statement: QueryComponents,
    table_name: str,
    where_clause: QueryComponents | Sequence[QueryComponents],
    order_by: Sequence[tuple[FieldName, Literal["ASC", "DESC"] | None]] | None = None,
    limit: int | None = None,
) -> RunnableQuery:
    # TODO: make table_name param support joins
    sts: list[QueryComponents | RunnableQuery] = []
    q_st = sql.SQL("{select} FROM {tname} WHERE {clause} ").format(
        select=select_statement,
        tname=sql.Identifier(table_name),
        clause=where_clause if isinstance(where_clause, sql.Composable) else sql.SQL(" and ").join(where_clause),
    )
    sts.append(q_st)
    if order_by:
        order_exprs = sql.SQL(",").join(
            sql.SQL("{sort_expr} {asc_desc}").format(
                sort_expr=sql.Identifier(*((fname,) if isinstance(fname, str) else fname)), asc_desc=sql.SQL(asc_desc or "")
            )
            for (fname, asc_desc) in order_by
        )
        order_st = sql.SQL("ORDER BY {order_by} ").format(order_by=order_exprs)
        q_st += order_st
        # sts.append(order_st)
    if limit:
        limit_st = sql.SQL("LIMIT {limit}").format(limit=limit)
        q_st += limit_st
        # sts.append(limit_st)
    return q_st
    # return sql.SQL(" ").join(sts)


def prepare_select_statement(
    field_names: Iterable[FieldName],
    *,
    as_names: dict[str, str] = {},  # If the key exist within field names( or field names[-1])
    # it will be used as "field"."name" as "as_name"
    # otherwise it will be treated as a literal
    # i.e. 'e' as "field_name"
    ordering: tuple[str, ...] | None = None,
) -> QueryComponents:
    template = sql.SQL("SELECT {fields}")
    components: OrderedDict[str, sql.Composable] = OrderedDict()
    for fname in (f if isinstance(f, tuple) else (f,) for f in field_names):
        if as_name := as_names.pop(fname[-1], None):
            components.setdefault(
                as_name,
                sql.SQL("{fname} as {as_name}").format(fname=sql.Identifier(*fname), as_name=sql.Identifier(as_name)),
            )
        else:
            # TODO: Find a better hashing soltn
            components.setdefault(".".join(fname), sql.Identifier(*fname))

    for literal, as_name in as_names.items():
        components.setdefault(
            as_name,
            sql.SQL("{literal} as {as_name}").format(literal=sql.Literal(literal), as_name=sql.Identifier(as_name)),
        )
    return template.format(
        fields=sql.SQL(",").join((val for fname in ordering if (val := components.get(fname))) if ordering else components.values())
    )


def prepare_equal_clause(field_name: FieldName, *, q: RunnableQuery | None = None) -> QueryComponents:
    # TODO: Make value optional,
    # when None, use Placeholder
    template = sql.SQL("{field_name} = {value}")
    if isinstance(field_name, str):
        fnames: tuple[str, ...] = (field_name,)
    elif isinstance(field_name, tuple):
        fnames = field_name
    return template.format(field_name=sql.Identifier(*fnames), value=q if q else sql.Placeholder())


def prepare_prefix_clause(
    field_name: FieldName,
    *,
    prefixes: Iterable[str] | None = None,
    prefix_count: int | None = None,  # DOES NOT WORK
) -> QueryComponents:
    # TODO: Remove prefix_count logic
    if prefix_count:
        pregex: sql.Composable = sql.SQL("|").join(sql.Placeholder() for i in range(prefix_count))
        prefix_literals: sql.Composable = sql.SQL("'({pregex})%%'").format(pregex=pregex)
    elif prefixes:
        prefix_literals = sql.Literal(f"({'|'.join(prefixes)})%%")
    else:
        raise Exception("Invalid Arguments")  # TODO: More meaningful errors
    template = sql.SQL("{field_name} SIMILAR TO {prefix_regex}")
    if isinstance(field_name, str):
        fnames: tuple[str, ...] = (field_name,)
    elif isinstance(field_name, tuple):
        fnames = field_name
    return template.format(field_name=sql.Identifier(*fnames), prefix_regex=prefix_literals)


def prepare_in_clause(
    field_name: str
    | tuple[str, ...],  # It can be a namespaced field-name (TableName.FieldName) then, the input should be ('TableName', 'FieldName')
    value_count: int | None = None,  # for placeholder count
    q: RunnableQuery | None = None,  # to use another queries result at IN
) -> QueryComponents:
    template = sql.SQL("{field_name} IN ({values})")
    if isinstance(field_name, str):
        fnames: tuple[str, ...] = (field_name,)
    elif isinstance(field_name, tuple):
        fnames = field_name
    if value_count:
        value_template: sql.Composable = sql.SQL(",").join(sql.Placeholder() for _ in range(value_count))
    elif q:
        value_template = q
    else:
        raise InvalidMessageError("Invalid Arguments", error_type=ErrorTypes.invalid_argumentation)
    return template.format(field_name=sql.Identifier(*fnames), values=value_template)


def prepare_gte_lte_clause(
    field_name: FieldName,
    *,
    gte: bool = False,
    lte: bool = False,
) -> QueryComponents:
    gte_template = sql.SQL("{field_name} >= {value}")
    lte_template = sql.SQL("{field_name} <= {value}")
    clauses: list[QueryComponents] = []

    if isinstance(field_name, str):
        fnames: tuple[str, ...] = (field_name,)
    elif isinstance(field_name, tuple):
        fnames = field_name
    if gte:
        clauses.append(gte_template.format(field_name=sql.Identifier(*fnames), value=sql.Placeholder()))
    if lte:
        clauses.append(lte_template.format(field_name=sql.Identifier(*fnames), value=sql.Placeholder()))
    return sql.SQL(" and ").join(clauses)


def prepare_insert_into(
    table_name: str,
    field_names: Sequence[FieldName],
    value_tuple_count: int = 1,
) -> RunnableQuery:
    template = sql.SQL("INSERT INTO {table_name} ({field_names}) VALUES {values}")

    fnames = map(
        lambda f: sql.Identifier(*f),
        (f if isinstance(f, tuple) else (f,) for f in field_names),
    )
    field_count = len(field_names)

    values = sql.SQL(",").join(
        sql.SQL("({valstr})").format(valstr=valstr)
        for valstr in (sql.SQL(",").join(sql.Placeholder() for _ in range(field_count)) for _ in range(value_tuple_count))
    )

    return template.format(
        table_name=sql.Identifier(table_name),
        field_names=sql.SQL(",").join(fnames),
        values=values,
    )


def combine_or_clauses(*clauses: QueryComponents) -> QueryComponents:
    return sql.SQL("({or_clauses})").format(or_clauses=sql.SQL(" or ").join(clauses))


def union_queries(*queries: RunnableQuery) -> RunnableQuery:
    return sql.SQL("({union_queries})").format(
        union_queries=sql.SQL(" UNION ").join(sql.SQL("({query})").format(query=query) for query in queries)
    )


def prepare_delete_q(table_name: str, clauses: Sequence[QueryComponents]) -> RunnableQuery:
    return sql.SQL("DELETE FROM {table_name} WHERE {clauses}").format(
        table_name=sql.Identifier(table_name), clauses=sql.SQL(" and ").join(clauses)
    )
