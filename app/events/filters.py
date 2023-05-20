import re
from typing import Callable

from events.typings import EventNostrDict
from pydantic import BaseModel


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
    e_tag: list[str] | None = None
    p_tag: list[str] | None = None

    class Config:
        @classmethod
        def alias_generator(cls, fname: str) -> str:
            if fname.endswith("tag"):
                tag_name, *_ = fname.split("_")
                return f"#{tag_name}"
            return fname


class EventFilterer:
    """
        A helper class to test out the Events using the Filters
    """
    def __init__(self, filters: Filters) -> None:
        self._filters = filters
        tests: dict[str, Callable[..., bool]] = {}
        tag_tests: dict[str, Callable[..., bool]] = {}

        if filters.ids:
            combined_ids = "|".join(filters.ids)
            regex = re.compile(rf"(({combined_ids})[0-9a-f]*)")
            tests.setdefault("id", lambda val: bool(regex.match(val)))

        if filters.authors:
            combined_authors = "|".join(filters.authors)
            regex = re.compile(rf"(({combined_authors})[0-9a-z]*)")
            tests.setdefault("pubkey", lambda val: bool(regex.match(val)))

        if filters.kinds:
            kinds_set = set(k for k in filters.kinds)
            tests.setdefault("kind", lambda val: val in kinds_set)

        if filters.since or filters.until:
            tests.setdefault(
                "created_at",
                lambda v: ((filters.since or v) <= v <= (filters.until or v)),
            )

        if filters.until:
            until_f = lambda val: val <= filters.until
            tests.setdefault("created_at", lambda val: (val <= filters.until))

        # Tag Tests
        if filters.e_tag:
            e_tag_set = set(filters.e_tag)
            # "#e", "{event_id}", *rest_values of tag
            tag_tests.setdefault("#e", lambda val, *_: val in e_tag_set)

        if filters.p_tag:
            p_tag_set = set(filters.p_tag)
            # "#p", "{pubkey}", *rest_values of tag
            tag_tests.setdefault("#p", lambda val, *_: val in p_tag_set)

        if len(tag_tests):

            def tags_tester(tags: list) -> bool:
                return all(
                    any(
                        tag_test(*event_tag)
                        for (e_t, *event_tag) in tags
                        if e_t == tag_name
                    )
                    for tag_name, tag_test in tag_tests.items()
                )

            tests.setdefault("tags", tags_tester)

        self.tests = tests

    def test_event(self, event: EventNostrDict) -> bool:
        return all(tester(event.get(key)) for (key, tester) in self.tests.items())
