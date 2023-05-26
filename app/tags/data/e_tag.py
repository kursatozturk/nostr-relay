from functools import cached_property
from typing import Literal

from tags.data.base import BaseTag

from ..typings.e_tag import ETagRow, MarkerType


class E_Tag(BaseTag):
    tag: Literal["e"]
    event_id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    recommended_relay_url: str
    marker: MarkerType | None

    @cached_property
    def nostr_dict(self) -> ETagRow:
        if self.marker:
            return (self.tag, self.event_id, self.recommended_relay_url, self.marker)
        return (self.tag, self.event_id, self.recommended_relay_url)
