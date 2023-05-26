from functools import cached_property
from typing import Literal

from tags.data.base import BaseTag
from tags.typings.p_tag import PTagRow


class P_Tag(BaseTag):
    tag: Literal["p"]
    pubkey: str
    recommended_relay_url: str

    @cached_property
    def nostr_dict(self) -> PTagRow:
        return (self.tag, self.pubkey, self.recommended_relay_url)
