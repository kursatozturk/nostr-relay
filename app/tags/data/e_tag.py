from functools import cached_property
from typing import Literal

from events.typings import MarkerType
from utils.models import NostrModel


class E_Tag(NostrModel):
    tag: Literal["#e"]
    event_id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    recommended_relay_url: str
    marker: MarkerType | None

    @cached_property
    def nostr_dict(self):
        if self.marker:
            return [self.tag, self.event_id, self.recommended_relay_url, self.marker]
        return [self.tag, self.event_id, self.recommended_relay_url]
