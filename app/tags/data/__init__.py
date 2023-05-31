from typing import Annotated, Callable, Sequence

from pydantic import Field

from tags.typings import TagRow

from .base import BaseTag
from .e_tag import E_TAG_TAG_NAME, E_Tag, row_to_e_tag
from .p_tag import P_TAG_TAG_NAME, P_Tag, row_to_p_tag

__all__ = ("E_Tag", "P_Tag", "Tag")


Tag = Annotated[E_Tag | P_Tag, Field(discriminator="tag")]

__row_to_tag: dict[str, Callable[[tuple], BaseTag]] = {E_TAG_TAG_NAME: row_to_e_tag, P_TAG_TAG_NAME: row_to_p_tag}


def parse_tags(rows: Sequence[TagRow]) -> list[BaseTag]:
    return [converter(row) for row in rows if (converter := __row_to_tag.get(row[0]))]
