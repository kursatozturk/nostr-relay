from events.crud import query_tags

async def run_query_tags():
    r = await query_tags()
