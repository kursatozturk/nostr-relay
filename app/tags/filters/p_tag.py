import re
from typing import Callable, Sequence

from tags.typings import PTagRow


def prepare_p_tag_tests(p_tags: set[str]) -> Callable[..., bool]:
    regex = re.compile(rf'^({"|".join(p_tags)}).*')

    def test(tags: Sequence[PTagRow]) -> bool:
        return any(regex.match(t[1]) for t in tags)

    return test
