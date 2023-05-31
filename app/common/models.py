
from abc import ABC
from functools import cached_property
from typing import Any

from pydantic import BaseModel


class NostrModel(BaseModel, ABC):
    @property
    def nostr_dict(self) -> dict[str, Any] | list[str | int | dict[str, Any]]:
        raise NotImplementedError()

    class Config:
        keep_untouched = (cached_property,)
