from enum import Enum


class MessageTypes(Enum):
    Event = "EVENT"
    Req = "REQ"
    Close = "CLOSE"
    Eose = "EOSE"
    Notice = "NOTICE"
    Count = "COUNT"
