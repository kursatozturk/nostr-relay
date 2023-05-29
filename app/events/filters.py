import re
from typing import Any, Callable

from pydantic import BaseModel, Field, root_validator
from tags.filters import prepare_tag_tests
from utils.tools import create_regex_matcher_func, create_set_includes_func

from events.typings import EventNostrDict


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
    tags: dict[str, set[str]] = Field(default_factory=dict)
    # e_tag: list[str] | None = Field(default=None, alias="#e")
    # p_tag: list[str] | None = Field(default=None, alias="#p")

    @root_validator(pre=True)
    def group_tags(cls, values: dict[str, Any]) -> dict[str, Any]:
        tags: dict[str, set[str]] = dict((key.strip("#"), set(val)) for (key, val) in values.items() if key.startswith("#"))

        values["tags"] = tags
        return values

class EventFilterer:
    """
    A helper class to test out the Events using the Filters
    """

    def __init__(self, *filters: Filters) -> None:
        self._filters = filters
        self._tests: list[dict[str, Callable[..., bool]]] = []
        for f in filters:
            tests: dict[str, Callable[..., bool]] = {}

            if f.ids:
                combined_ids = "|".join(f.ids)
                regex = re.compile(rf"(({combined_ids})[0-9a-f]*)")
                tests.setdefault("id", create_regex_matcher_func(regex))

            if f.authors:
                combined_authors = "|".join(f.authors)
                regex = re.compile(rf"(({combined_authors})[0-9a-z]*)")
                tests.setdefault("pubkey", create_regex_matcher_func(regex))

            if f.kinds:
                kinds_set = set(k for k in f.kinds)
                tests.setdefault("kind", create_set_includes_func(kinds_set))

            if f.since or f.until:
                tests.setdefault("created_at", lambda v: (f.since or v) <= v <= (f.until or v))
            if f.tags:
                tags_test = prepare_tag_tests(f.tags)
                tests.setdefault("tags", tags_test)
            self._tests.append(tests)
        print(self._tests)

    def test_event(self, event: EventNostrDict) -> bool:
        return any(all(tester(event.get(key)) for (key, tester) in test.items()) for test in self._tests)
