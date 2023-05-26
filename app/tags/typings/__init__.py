from typing import TypeAlias
from .e_tag import ETagRow
from .p_tag import PTagRow


TagRow: TypeAlias = ETagRow | PTagRow
__all__ = ("ETagRow", "PTagRow", "TagRow")
