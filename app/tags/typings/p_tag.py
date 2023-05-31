from typing import Literal


PTagRowBase = tuple[Literal['p'], str]
PTagRowWithRelay = tuple[*PTagRowBase, str]
PTagRow = PTagRowBase | PTagRowWithRelay
