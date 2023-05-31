from events.filters import EventFilterer, Filters
from tests.events.utils import generate_event


def test_filtering() -> None:
    content = "Filtering"
    event = generate_event(content=content)
    filter1 = Filters(ids=[event.id[:20], "19a9fb0c9023914f"])  # a random id
    filterer = EventFilterer(filter1)
    assert filterer.test_event(event.nostr_dict), "One Pos, One Neg Filter should Allow Event!"
    filter2 = Filters(ids=[event.id[:15]])  # multiple of positive filters
    filterer = EventFilterer(filter2)
    assert filterer.test_event(event.nostr_dict), "One Pos Filter should Allow Event!"
    filter3 = Filters(ids=["0000000000000000000"])  # a negative filter
    filterer = EventFilterer(filter3)
    assert not filterer.test_event(event.nostr_dict), "One Neg Filter should Not Allow Event!"
    filterer = EventFilterer(filter1, filter2, filter3)
    assert filterer.test_event(event.nostr_dict), "Multiple Filter with having at least one Pos Filter, Should Allow!"

    authors_filter1 = Filters(authors=[event.pubkey[:13], "999a9b99c994913299f"])
    filterer = EventFilterer(authors_filter1)
    assert filterer.test_event(event.nostr_dict), "Pos Authors Filter Should Allow Event!"
    authors_filter2 = Filters(authors=["999a9b99c994913299f"])  # a negative filters
    filterer = EventFilterer(authors_filter2)
    assert not filterer.test_event(event.nostr_dict), "Neg Authors Filter Should Not Allow Event!"

    filterer = EventFilterer(authors_filter1, authors_filter2)
    assert filterer.test_event(event.nostr_dict), "One Pos One Neg Authors Filter Should Allow Event!"

    created_at_filters1 = Filters(since=event.created_at - 10, until=event.created_at + 10)  # a pos filter
    filterer = EventFilterer(created_at_filters1)
    assert filterer.test_event(event.nostr_dict), "One Pos Created at Filter Should Allow Event!"

    created_at_filters2 = Filters(since=event.created_at - 10, until=event.created_at - 5)  # a neg filter
    filterer = EventFilterer(created_at_filters2)
    assert not filterer.test_event(event.nostr_dict), "One Neg Created at Filter Should Not Allow Event!"

    filterer = EventFilterer(created_at_filters1, created_at_filters2)
    assert filterer.test_event(event.nostr_dict), "One Pos and One Neg Created at Filter Should Allow Event!"

    kind_filters1 = Filters(kinds=[1]) # a pos filter
    filterer = EventFilterer(kind_filters1)
    assert filterer.test_event(event.nostr_dict), "One Pos Kind Filter Should Allow Event!"

    kind_filters2 = Filters(kinds=[2]) # a neg filter
    filterer = EventFilterer(kind_filters2)
    assert not filterer.test_event(event.nostr_dict), "One Neg Kind Filter Should Not Allow Event!"

    filterer = EventFilterer(kind_filters1, kind_filters2)
    assert filterer.test_event(event.nostr_dict), "One Pos and One Neg Kind Filter Should Allow Event!"
