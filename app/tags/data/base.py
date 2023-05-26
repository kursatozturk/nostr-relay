from typing import TypeVar
from utils.models import NostrModel


class BaseTag(NostrModel):
    tag: str
