from functools import cached_property
from typing import Literal

from utils.models import NostrModel



class P_Tag(NostrModel):
    tag: Literal["#p"]
    pubkey: str
    recommended_relay_url: str

    @cached_property
    def nostr_dict(self):
        return [self.tag, self.pubkey, self.recommended_relay_url]
