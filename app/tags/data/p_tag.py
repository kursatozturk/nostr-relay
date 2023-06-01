from functools import cached_property
from typing import Literal

from tags.data.base import BaseTag
from tags.typings.p_tag import PTagRow, p_tag_has_relay

P_TAG_TAG_NAME = "p"


class P_Tag(BaseTag):
    tag: Literal["p"]
    pubkey: str
    recommended_relay_url: str | None = None
    pet_name: str | None = None

    # @cached_property
    # def nostr_dict(self) -> list:
    #     return list(self._nostr_dict)

    @cached_property
    def nostr_dict(self) -> PTagRow:
        if self.recommended_relay_url:
            return (self.tag, self.pubkey, self.recommended_relay_url)
        else:
            return (self.tag, self.pubkey)


def row_to_p_tag(row: PTagRow) -> P_Tag:
    if p_tag_has_relay(row):
        return P_Tag(tag="p", pubkey=row[1], recommended_relay_url=row[2], pet_name=row[3] if len(row) == 4 else None)
    else:
        return P_Tag(tag="p", pubkey=row[1])
