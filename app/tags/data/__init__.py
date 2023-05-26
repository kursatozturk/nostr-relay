from typing import Annotated

from pydantic import Field
from .e_tag import E_Tag
from .p_tag import P_Tag

__all__ = ("E_Tag", "P_Tag")


Tag = Annotated[E_Tag | P_Tag, Field(discriminator="tag")]
