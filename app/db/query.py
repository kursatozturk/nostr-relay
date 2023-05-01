from typing import Any, Iterable

from psycopg import sql


def construct_prefix_clause(field_name: str, prefixes: Iterable[str]) -> sql.Composable:
    template = sql.SQL("{field_name} SIMILAR TO {prefix_regex}")
    p_regex = sql.Literal(f'({"|".join(prefixes)})%')
    return template.format(field_name=sql.Identifier(field_name), prefix_regex=p_regex)


def construct_in_clause(field_name: str, values: Iterable[Any]) -> sql.Composable:
    template = sql.SQL("{field_name} IN ({values})")
    return template.format(
        field_name=sql.Identifier(field_name),
        values=sql.SQL(",").join(sql.Literal(value) for value in values),
    )


def construct_lte_gte_clause(
    field_name: str, *, gte: str | None = None, lte: int | float | str | None = None
) -> sql.Composable:
    gte_template = sql.SQL("{field_name} >= {value}")
    lte_template = sql.SQL("{field_name} <= {value}")
    clauses: list[sql.Composable] = []
    if gte is not None:
        clauses.append(
            gte_template.format(
                field_name=sql.Identifier(field_name), value=sql.Literal(gte)
            )
        )
    if lte is not None:
        clauses.append(
            lte_template.format(
                field_name=sql.Identifier(field_name), value=sql.Literal(lte)
            )
        )
    return sql.SQL(" and ").join(clauses)
