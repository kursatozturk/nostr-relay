from db.core import _get_async_connection
from events.db import (generate_sql_schema_e_tag, generate_sql_schema_event,
                       generate_sql_schem_p_tag, clean_out_db)


async def initialize_db_task():
    conn = await _get_async_connection()
    async with conn:
        try:
            await conn.execute(clean_out_db())
        except:
            pass
        await conn.execute(generate_sql_schema_event())
        await conn.execute(generate_sql_schema_e_tag())
        await conn.execute(generate_sql_schem_p_tag())
