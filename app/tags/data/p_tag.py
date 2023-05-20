from functools import cached_property
from typing import Literal
from events.typings import PTagRow

from utils.models import NostrModel

def db_to_p_tag(row: tuple) -> 'P_Tag':
    _, tag_name, pubkey, relay_url = row
    return P_Tag(tag=tag_name, pubkey=pubkey, recommended_relay_url=relay_url)


class P_Tag(NostrModel):
    tag: Literal["#p"]
    pubkey: str
    recommended_relay_url: str

    @cached_property
    def nostr_dict(self):
        return [self.tag, self.pubkey, self.recommended_relay_url]
