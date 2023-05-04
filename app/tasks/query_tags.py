from events.crud import fetch_event

async def run_query_tags():
    r = await fetch_event("85629adcff99d1580738984d31b17bc2")
    print(r)
