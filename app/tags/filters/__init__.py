from typing import Callable
from tags.data.e_tag import E_TAG_TAG_NAME
from tags.data.p_tag import P_TAG_TAG_NAME

from common.tools import group_by

from tags.typings import TagRow

from .e_tag import prepare_e_tag_tests
from .p_tag import prepare_p_tag_tests

tag_test_mapper: dict[str, Callable[[set[str]], Callable[..., bool]]] = {
    E_TAG_TAG_NAME: prepare_e_tag_tests,
    P_TAG_TAG_NAME: prepare_p_tag_tests,
}


def prepare_tag_tests(tag_filters: dict[str, set[str]]) -> Callable[[list[TagRow]], bool]:
    # setted_filters = {tag_name: set(tag_vals) for tag_name, tag_vals in tag_filters.items()}

    def test(tags: list[TagRow]) -> bool:
        grouped_tags = group_by(tags, lambda t: t[0])
        tests = {tname: tester(tsets) for tname, tsets in tag_filters.items() if (tester := tag_test_mapper.get(tname))}

        return all(test(grouped_tags.get(tname, [])) for tname, test in tests.items())

    return test
