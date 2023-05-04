from collections import OrderedDict
from typing import Any, Iterable, Literal, cast

from psycopg import sql


class __PlaceHolder:
    # TODO: Make it singleton
    ...


PLACE_HOLDER = __PlaceHolder()


def construct_query(
    select_statement: sql.Composable,
    from_statement: sql.Composable,
    where_clause: sql.Composable | None = None,
) -> sql.Composable:
    return sql.SQL("").join(
        (select_statement, from_statement, where_clause or sql.SQL(""))
    )


def construct_select_from_query(
    select_statement: sql.Composable,
    table_name: str,
    where_clause: sql.Composable,
) -> sql.Composed:
    # TODO: make table_name join compatible
    return sql.SQL("{select} FROM {tname} WHERE {clause}").format(
        select=select_statement, tname=sql.Identifier(table_name), clause=where_clause
    )


def construct_select_statement(
    field_names: Iterable[str | tuple[str, ...]],
    *,
    as_names: dict[
        str, str
    ] = {},  # If the key exist within field names( or field names[-1])
    # it will be used as "field"."name" as "as_name"
    # otherwise it will be treated as a literal
    # i.e. 'e' as "field_name"
    ordering: tuple[str, ...] | None = None,
) -> sql.Composable:
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


def construct_equal_clause(
    field_name: str | tuple[str, ...],
    value: str | int | float | __PlaceHolder = PLACE_HOLDER,
) -> sql.Composable:
    # TODO: Make value optional,
    # when None, use Placeholder
    template = sql.SQL("{field_name} = {value}")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    return template.format(
        field_name=sql.Identifier(*fnames),
        value=sql.Placeholder() if type(value) is __PlaceHolder else sql.Literal(value),
    )


def construct_prefix_clause(
    field_name: str | tuple[str, ...],
    *,
    prefixes: Iterable[str] | None = None,
    prefix_count: int | None = None,  # if not None, we will use it for placeholders
) -> sql.Composable:
    if prefix_count:
        pregex: sql.Composable = sql.SQL("|").join(
            sql.Placeholder() for i in range(prefix_count)
        )
        prefix_literals: sql.Composable = sql.SQL("'({pregex})%'").format(pregex=pregex)
    elif prefixes:
        prefix_literals = sql.Literal(f"({'|'.join(prefixes)})%")
    else:
        raise Exception("Invalid Arguments")  # TODO: More meaningful errors
    template = sql.SQL("{field_name} SIMILAR TO {prefix_regex}")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    return template.format(
        field_name=sql.Identifier(*fnames), prefix_regex=prefix_literals
    )


def construct_in_clause(
    field_name: str | tuple[str, ...],
    *,
    values: Iterable[Any] | None = None,
    value_count: int | None = None,  # for placeholder
) -> sql.Composable:
    template = sql.SQL("{field_name} IN ({values})")
    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name

    if values is None and value_count:
        value_template = sql.SQL(",").join(
            sql.Placeholder() for _ in range(value_count)
        )
    elif values is not None and value_count is None:
        value_template = sql.SQL(",").join(sql.Literal(value) for value in values)
    else:
        raise Exception("Invalid Arguments")  # TODO: More meaningful errors
    return template.format(field_name=sql.Identifier(*fnames), values=value_template)


def construct_lte_gte_clause(
    field_name: str | tuple[str, ...],
    *,
    gte: int | float | str | __PlaceHolder | None = None,
    lte: int | float | str | __PlaceHolder | None = None,
) -> sql.Composable:
    gte_template = sql.SQL("{field_name} >= {value}")
    lte_template = sql.SQL("{field_name} <= {value}")
    clauses: list[sql.Composable] = []

    if type(field_name) is str:
        fnames: tuple[str, ...] = (field_name,)
    elif type(field_name) is tuple:
        fnames = field_name
    if gte is not None:
        clauses.append(
            gte_template.format(
                field_name=sql.Identifier(*fnames),
                value=sql.Placeholder()
                if type(gte) is __PlaceHolder
                else sql.Literal(gte),
            )
        )
    if lte is not None:
        clauses.append(
            lte_template.format(
                field_name=sql.Identifier(*fnames),
                value=sql.Placeholder()
                if type(lte) is __PlaceHolder
                else sql.Literal(lte),
            )
        )
    return sql.SQL(" and ").join(clauses)


def construct_insert_into(
    table_name: str,
    field_names: Iterable[str | tuple[str, ...]],
    value_list: Iterable[tuple[str | int | float | __PlaceHolder, ...]],
):
    template = sql.SQL("INSERT INTO {table_name} ({field_names}) VALUES {values}")

    fnames = map(
        lambda f: sql.Identifier(*f),
        (f if type(f) is tuple else cast(tuple[str, ...], (f,)) for f in field_names),
    )

    values = sql.SQL(",").join(
        sql.SQL("({valstr})").format(valstr=valstr)
        for valstr in (
            sql.SQL(",").join(
                sql.Placeholder() if type(val) is __PlaceHolder else sql.Literal(val)
                for val in vals
            )
            for vals in value_list
        )
    )

    return template.format(
        table_name=sql.Identifier(table_name),
        field_names=sql.SQL(",").join(fnames),
        values=values,
    )
