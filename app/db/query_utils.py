from collections import OrderedDict
from typing import Iterable, Sequence, cast

from psycopg import sql
from utils.errors import ErrorTypes, InvalidMessageError
from db.typings import RunnableQuery, QueryComponents


def create_runnable_query(
    select_statement: QueryComponents,
    table_name: str,
    where_clause: QueryComponents | Sequence[QueryComponents],
) -> RunnableQuery:
    # TODO: make table_name param support joins
    return sql.SQL("{select} FROM {tname} WHERE {clause}").format(
        select=select_statement,
        tname=sql.Identifier(table_name),
        clause=where_clause
        if issubclass(type(where_clause), sql.Composable)
        else sql.SQL(" and ").join(cast(Sequence[sql.Composable], where_clause)),
    )


def prepare_select_statement(
    field_names: Iterable[str | tuple[str, ...]],
    *,
    as_names: dict[
        str, str
    ] = {},  # If the key exist within field names( or field names[-1])
    # it will be used as "field"."name" as "as_name"
    # otherwise it will be treated as a literal
    # i.e. 'e' as "field_name"
    ordering: tuple[str, ...] | None = None,
) -> QueryComponents:
    template = sql.SQL("SELECT {fields}")
    components: OrderedDict[str, sql.Composable] = OrderedDict()
    for fname in (
        f if type(f) is tuple else cast(tuple[str, ...], (f,)) for f in field_names
    ):
        if as_name := as_names.pop(fname[-1], None):
            components.setdefault(
                as_name,
                sql.SQL("{fname} as {as_name}").format(
                    fname=sql.Identifier(*fname), as_name=sql.Identifier(as_name)
                ),
            )
        else:
            # TODO: Find a better hashing soltn
            components.setdefault(".".join(fname), sql.Identifier(*fname))

    for literal, as_name in as_names.items():
        components.setdefault(
            as_name,
            sql.SQL("{literal} as {as_name}").format(
                literal=sql.Literal(literal), as_name=sql.Identifier(as_name)
            ),
        )
    return template.format(
        fields=sql.SQL(",").join(
            (val for fname in ordering if (val := components.get(fname)))
            if ordering
            else components.values()
        )
    )


def prepare_equal_clause(
    field_name: str | tuple[str, ...],
) -> QueryComponents:
    # TODO: Make value optional,
    # when None, use Placeholder
    template = sql.SQL("{field_name} = {value}")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    return template.format(field_name=sql.Identifier(*fnames), value=sql.Placeholder())


def prepare_prefix_clause(
    field_name: str | tuple[str, ...],
    *,
    prefixes: Iterable[str] | None = None,
    prefix_count: int | None = None,  # DOES NOT WORK
) -> QueryComponents:
    # TODO: Remove prefix_count logic
    if prefix_count:
        pregex: sql.Composable = sql.SQL("|").join(
            sql.Placeholder() for i in range(prefix_count)
        )
        prefix_literals: sql.Composable = sql.SQL("'({pregex})%%'").format(
            pregex=pregex
        )
    elif prefixes:
        prefix_literals = sql.Literal(f"({'|'.join(prefixes)})%%")
    else:
        raise Exception("Invalid Arguments")  # TODO: More meaningful errors
    template = sql.SQL("{field_name} LIKE {prefix_regex}")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    return template.format(
        field_name=sql.Identifier(*fnames), prefix_regex=prefix_literals
    )


def prepare_in_clause(
    field_name: str | tuple[str, ...],
    value_count: int | None = None,  # for placeholder
    q: RunnableQuery | None = None,  # to use another queries result at IN
) -> QueryComponents:
    template = sql.SQL("{field_name} IN ({values})")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    if value_count:
        value_template: sql.Composable = sql.SQL(",").join(
            sql.Placeholder() for _ in range(value_count)
        )
    elif q:
        value_template = q
    else:
        raise InvalidMessageError(
            "Invalid Arguments", error_type=ErrorTypes.invalid_argumentation
        )
    return template.format(field_name=sql.Identifier(*fnames), values=value_template)


def prepare_lte_gte_clause(
    field_name: str | tuple[str, ...],
    *,
    gte: bool = False,
    lte: bool = False,
) -> QueryComponents:
    gte_template = sql.SQL("{field_name} >= {value}")
    lte_template = sql.SQL("{field_name} <= {value}")
    clauses: list[sql.Composable] = []

    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    if gte:
        clauses.append(
            gte_template.format(
                field_name=sql.Identifier(*fnames), value=sql.Placeholder()
            )
        )
    if lte:
        clauses.append(
            lte_template.format(
                field_name=sql.Identifier(*fnames), value=sql.Placeholder()
            )
        )
    return sql.SQL(" and ").join(clauses)


def prepare_insert_into(
    table_name: str,
    field_names: Sequence[str | tuple[str, ...]],
    value_tuple_count: int = 1,
) -> RunnableQuery:
    template = sql.SQL("INSERT INTO {table_name} ({field_names}) VALUES {values}")

    fnames = map(
        lambda f: sql.Identifier(*f),
        (f if type(f) is tuple else cast(tuple[str, ...], (f,)) for f in field_names),
    )
    field_count = len(field_names)

    values = sql.SQL(",").join(
        sql.SQL("({valstr})").format(valstr=valstr)
        for valstr in (
            sql.SQL(",").join(sql.Placeholder() for _ in range(field_count))
            for _ in range(value_tuple_count)
        )
    )

    return template.format(
        table_name=sql.Identifier(table_name),
        field_names=sql.SQL(",").join(fnames),
        values=values,
    )
