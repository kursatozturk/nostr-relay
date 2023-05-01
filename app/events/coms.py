from enum import Enum
from typing import Literal

from pydantic import BaseModel

from .data import Event


class Filters(BaseModel):
    pass


class MessageTypes(Enum):
    Event = "EVENT"
    Req = "REQ"
    Close = "CLOSE"


EventMessage = tuple[Literal['EVENT'], Event]

ReqTypes = tuple[Literal["EVENT"], Event] | tuple[Literal["REQ"], str, Filters]
