import re
from typing import Callable

from tags.db.e_tag import E_TAG_TAG_NAME
from tags.db.p_tag import P_TAG_TAG_NAME
from utils.tools import flat_list

from events.typings import EventNostrDict
from pydantic import BaseModel, Field


class Filters(BaseModel):
    """
    Base Model to validate Filter Requests
    """

    ids: list[str] | None = None
    authors: list[str] | None = None
    kinds: list[int] | None = None
    since: int | None = None
    until: int | None = None
    limit: int | None = None
    e_tag: list[str] | None = Field(default=None, alias="#e")
    p_tag: list[str] | None = Field(default=None, alias="#p")

class EventFilterer:
    """
    A helper class to test out the Events using the Filters
    """

    def __init__(self, *filters: Filters) -> None:
        self._filters = filters
        tests: dict[str, Callable[..., bool]] = {}
        tag_tests: dict[str, Callable[..., bool]] = {}

        if ids := flat_list(f.ids for f in filters if f.ids):
            combined_ids = "|".join(ids)
            regex = re.compile(rf"(({combined_ids})[0-9a-f]*)")
            tests.setdefault("id", lambda val: bool(regex.match(val)))

        if authors := flat_list(f.authors for f in filters if f.authors):
            combined_authors = "|".join(authors)
            regex = re.compile(rf"(({combined_authors})[0-9a-z]*)")
            tests.setdefault("pubkey", lambda val: bool(regex.match(val)))

        if kinds := flat_list(f.kinds for f in filters if f.kinds):
            kinds_set = set(k for k in kinds)
            tests.setdefault("kind", lambda val: val in kinds_set)

        if created_at_f := [(f.since, f.until) for f in filters if (f.since or f.until)]:
            tests.setdefault(
                "created_at",
                lambda v: any((since or v) <= v <= (until or v) for (since, until) in created_at_f)
                # lambda v: ((filters.since or v) <= v <= (filters.until or v)),
            )
        # Tag Tests
        if e_tags := flat_list(f.e_tag for f in filters if f.e_tag):
            e_tag_set = set(e_tags)
            # E_TAG_TAG_NAME, "{event_id}", *rest_values of tag
            tag_tests.setdefault(E_TAG_TAG_NAME, lambda val, *_: val in e_tag_set)

        if p_tags := flat_list(f.p_tag for f in filters if f.p_tag):
            p_tag_set = set(p_tags)
            # P_TAG_TAG_NAME, "{pubkey}", *rest_values of tag
            tag_tests.setdefault(P_TAG_TAG_NAME, lambda val, *_: val in p_tag_set)

        if len(tag_tests):

            def tags_tester(tags: list) -> bool:
                print('#' * 100)
                print(tags)
                print('#' * 100)
                return all(
                    any(tag_test(*event_tag) for (e_t, *event_tag) in tags if e_t == tag_name) for tag_name, tag_test in tag_tests.items()
                )

            tests.setdefault("tags", tags_tester)

        self.tests = tests

    def test_event(self, event: EventNostrDict) -> bool:
        return all(tester(event.get(key)) for (key, tester) in self.tests.items())
