from functools import cached_property
from typing import Literal

from tags.data import BaseTag

from ..typings.e_tag import ETagRow, MarkerType, e_tag_has_relay

E_TAG_TAG_NAME = "e"


class E_Tag(BaseTag):
    tag: Literal["e"]
    event_id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    recommended_relay_url: str | None
    marker: MarkerType | None

    # @cached_property
    # def nostr_dict(self) -> list:
    #     return list(self._nostr_dict)

    @cached_property
    def nostr_dict(self) -> ETagRow:
        if self.marker:
            return (self.tag, self.event_id, self.recommended_relay_url or "", self.marker)
        elif self.recommended_relay_url:
            return (self.tag, self.event_id, self.recommended_relay_url)
        else:
            return (self.tag, self.event_id)


def row_to_e_tag(row: ETagRow) -> E_Tag:
    return E_Tag(
        tag="e", event_id=row[1], recommended_relay_url=row[2] if e_tag_has_relay(row) else None, marker=row[3] if len(row) == 4 else None
    )
