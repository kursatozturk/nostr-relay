import timeit
from typing import Any
from pydantic import BaseModel, Field, root_validator


class X(BaseModel):
    tags: dict[str, list[str]] = Field(default_factory=dict)

    @root_validator(pre=True)
    def set_tags(cls, values: dict[str, Any]) -> dict[str, Any]:
        tags = dict((key, value) for key, value in values.items() if key.startswith("#"))
        values["tags"] = tags
        return values


async def test():
    # data = {"#e": ["E1", "E2"], "#p": ["P1", "P2"], "#a": ["A1", "A2", "A3"]}
    # x = X(**data)
    # x2 = X()
    # print(x, x2)
    x = 23
    upper = int(2e10)
    test_c = int(1e6)
    r = range(0, upper)
    rt = timeit.timeit("x in r", globals={'x': x, 'r': r}, number=test_c)
    ct = timeit.timeit("0 <= x <= upper", globals={'x': x, 'upper': upper}, number=test_c)
    print(f'{rt=}|{ct=}')
    raise ValueError("AHA")
