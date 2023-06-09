from typing import TypeAlias

from psycopg import AsyncConnection, sql
from psycopg_pool import AsyncConnectionPool

RunnableQuery: TypeAlias = sql.SQL | sql.Composed
QueryComponents: TypeAlias = sql.Composable
DBConnection: TypeAlias = AsyncConnection
DBConnectionPool: TypeAlias = AsyncConnectionPool

FieldName = str | tuple[str, ...]
