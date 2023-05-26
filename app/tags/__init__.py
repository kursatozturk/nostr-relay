from typing import TypeAlias

from .data.e_tag import E_Tag
from .data.p_tag import P_Tag

TagTypes: TypeAlias = E_Tag | P_Tag

__all__ = ("E_Tag", "P_Tag", "TagTypes")
