from common.typings import SenderAsyncWebsocket
from events.crud import count_events
from events.enums import MessageTypes

from events.filters import Filters


async def handle_received_count(ws: SenderAsyncWebsocket, subs_id: str, filters: list[Filters]) -> None:
    count = await count_events(*filters)
    await ws.send_json(
        [
            MessageTypes.Count.value,
            subs_id,
            {"count": count},
        ]
    )
