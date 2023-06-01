import json
from functools import cached_property

from pydantic import Field, validator
from tags.data import Tag, parse_tags
from common.models import NostrModel

from events.typings import EventNostrDict, KindType

METADATA_KIND = 0

class Event(NostrModel):
    id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    pubkey: str  # 32-bytes lowercase hex-encoded public key of the event creator
    created_at: int  # unix timestamp in seconds
    kind: KindType
    tags: list[Tag] = Field(default_factory=list)
    content: str
    sig: str  # 64-bytes hex of the signature of the sha256 hash of the serialized event data, which is the same as the "id" field

    _tag_separator = validator("tags", pre=True, allow_reuse=True)(parse_tags)

    @property
    def serializeable(self) -> str:
        """
        Used to obtain id. (Note that it needs to be applied sha256 to obtain final id!)
        """
        return json.dumps(
            [0, self.pubkey, self.created_at, self.kind, [tag.nostr_dict for tag in self.tags], self.content],
            separators=(',',':'),
            ensure_ascii=False
        )

    @cached_property
    def nostr_dict(self) -> EventNostrDict:
        """
        Converts the data type to nostr protocol standards.
        """
        return {
            "id": self.id,
            "pubkey": self.pubkey,
            "created_at": self.created_at,
            "kind": self.kind,
            "tags": [tag.nostr_dict for tag in self.tags],
            "content": self.content,
            "sig": self.sig,
        }

    @property
    def is_metadata(self) -> bool:
        return self.kind == 0

    @property
    def is_contact_list(self) -> bool:
        return self.kind == 3
