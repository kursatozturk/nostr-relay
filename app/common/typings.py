from typing import Any, Coroutine, Mapping, Protocol, TypeAlias


SerializableDataType: TypeAlias = list[str | Mapping]

class SenderAsyncWebsocket(Protocol):
    async def send_json(self, data: SerializableDataType) -> None:
        ...


class ReceiverAsyncWebsocket(Protocol):
    async def receive_json(self) -> Coroutine[Any, Any, SerializableDataType]:
        ...
