from db.core import _get_async_connection
from events.db import (generate_sql_schema_e_tag, generate_sql_schema_event,
                       generate_sql_schem_p_tag)


async def initialize_db_task():
    conn = await _get_async_connection()
    async with conn:
        await conn.execute(generate_sql_schema_event())
        await conn.execute(generate_sql_schema_e_tag())
        await conn.execute(generate_sql_schem_p_tag())
