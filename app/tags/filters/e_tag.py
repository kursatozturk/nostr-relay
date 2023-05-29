import re
from typing import Callable, Sequence

from tags.typings import ETagRow


def prepare_e_tag_tests(e_tags: set[str]) -> Callable[..., bool]:
    regex = re.compile(rf'^({"|".join(e_tags)}).*')

    def test(tags: Sequence[ETagRow]) -> bool:
        return any(regex.match(t[1]) for t in tags)

    return test
