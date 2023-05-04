from abc import ABC, abstractmethod
import json
from enum import Enum
from typing import Any, Literal
from functools import cached_property

from pydantic import BaseModel, Field, validator


class Kind(int, Enum):
    metadata = 0
    short_text_note = 1
    recommend_relay = 2
    contacts = 3
    encrypted_dm = 4
    event_deletion = 5


class Marker(str, Enum):
    reply = "reply"
    root = "root"
    mention = "mention"


class NostrModel(BaseModel, ABC):
    @abstractmethod
    def nostr_dict(self) -> dict[str, Any] | list[str | int | dict[str, Any]]:
        raise NotImplementedError()

    class Config:
        keep_untouched = (cached_property,)


class E_Tag(NostrModel):
    tag: Literal["e"]
    event_id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    recommended_relay_url: str
    marker: Marker | None = None

    @cached_property
    def nostr_dict(self):
        if self.marker:
            return [
                self.tag,
                self.event_id,
                self.recommended_relay_url,
                self.marker.value,
            ]
        return [self.tag, self.event_id, self.recommended_relay_url]


class P_Tag(NostrModel):
    tag: Literal["p"]
    pubkey: str
    recommended_relay_url: str

    @cached_property
    def nostr_dict(self):
        return [self.tag, self.pubkey, self.recommended_relay_url]


class Event(NostrModel):
    id: str  # 32-bytes lowercase hex-encoded sha256 of the serialized event data
    pubkey: str  # 32-bytes lowercase hex-encoded public key of the event creator
    created_at: int  # unix timestamp in seconds
    kind: Kind
    tags: list[E_Tag | P_Tag] = Field(default_factory=list)
    content: str
    sig: str  # 64-bytes hex of the signature of the sha256 hash of the serialized event data, which is the same as the "id" field

    @validator("tags", pre=True, each_item=True)
    def separate_tags(cls, tag_data: tuple | dict):
        if type(tag_data) is dict:
            if tag_data["tag"] == "e":
                return E_Tag(**tag_data)
            else:
                return P_Tag(**tag_data)
        else:
            if tag_data[0] == "e":
                return E_Tag(
                    tag="e",
                    event_id=tag_data[1],
                    recommended_relay_url=tag_data[2],
                    marker=tag_data[3] if len(tag_data) > 3 else None,
                )
            elif tag_data[0] == "p":
                return P_Tag(
                    tag="p", pubkey=tag_data[1], recommended_relay_url=tag_data[2]
                )
            else:
                # TODO: Add Tag Validations
                assert False

    @validator("kind", pre=True)
    def parse_int(cls, kind: str):
        return int(kind)

    def _serialize(self) -> str:
        """
        Used to obtain id. (Note that it needs to be applied sha256 to obtain final id!)
        """
        return json.dumps(
            [0, self.pubkey, self.created_at, self.kind.value, self.tags, self.content]
        )

    @cached_property
    def nostr_dict(self):
        """
        Converts the data type to nostr protocol standards.
        """
        return {
            "id": self.id,
            "pubkey": self.pubkey,
            "created_at": self.created_at,
            "kind": self.kind.value,
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


class Filters(NostrModel):
    ids: list[str] | None = None
    authors: list[str] | None = None
    kinds: list[Kind] | None = None
    since: int | None = None
    until: int | None = None
    limit: int | None = None
    e_tag: E_Tag | None = Field(None, alias="#e")
    p_tag: P_Tag | None = Field(None, alias="#p")

    @cached_property
    def nostr_dict(self):
        return {"ids": self.ids}
