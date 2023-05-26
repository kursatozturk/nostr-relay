import json
from functools import cached_property

from pydantic import Field, validator
from tags import E_Tag, P_Tag
from tags.data import Tag
from tags.db.e_tag import E_TAG_TAG_NAME
from tags.db.p_tag import P_TAG_TAG_NAME
from tags.typings import ETagRow, PTagRow
from utils.models import NostrModel

from events.typings import EventNostrDict, KindType


class Event(NostrModel):
    id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    pubkey: str  # 32-bytes lowercase hex-encoded public key of the event creator
    created_at: int  # unix timestamp in seconds
    kind: KindType
    tags: list[Tag] = Field(default_factory=list)
    content: str
    sig: str  # 64-bytes hex of the signature of the sha256 hash of the serialized event data, which is the same as the "id" field

    @validator("tags", pre=True, each_item=True)
    def separate_tags(cls, tag_data: E_Tag | P_Tag | ETagRow | PTagRow | dict):
        if isinstance(tag_data, E_Tag) or isinstance(tag_data, P_Tag):
            return tag_data
        elif isinstance(tag_data, dict):
            if tag_data["tag"] == E_TAG_TAG_NAME:
                return E_Tag(**tag_data)
            else:
                return P_Tag(**tag_data)
        else:
            if tag_data[0] == E_TAG_TAG_NAME:
                return E_Tag(
                    tag=E_TAG_TAG_NAME,
                    event_id=tag_data[1],
                    recommended_relay_url=tag_data[2],
                    marker=tag_data[3] if len(tag_data) == 4 else None,
                )
            elif tag_data[0] == P_TAG_TAG_NAME:
                return P_Tag(tag=P_TAG_TAG_NAME, pubkey=tag_data[1], recommended_relay_url=tag_data[2])
            else:
                print(tag_data)
                assert False

    @validator("kind", pre=True)
    def parse_int(cls, kind: str):
        return int(kind)

    def _serialize(self) -> str:
        """
        Used to obtain id. (Note that it needs to be applied sha256 to obtain final id!)
        """
        return json.dumps([0, self.pubkey, self.created_at, self.kind, self.tags, self.content])

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

    class Config:
        json_encoders = {
            E_Tag: lambda e: list(
                filter(
                    lambda x: x,
                    (
                        e.tag,
                        e.e_id,
                        e.recommended_relay_url,
                        e.marker.value if e.marker else None,
                    ),
                )
            ),
            P_Tag: lambda p: [
                p.tag,
                p.pubkey,
                p.recommended_relay_url,
            ],
        }
