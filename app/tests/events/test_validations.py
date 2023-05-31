from events.validators import validate_created_at, validate_event_id, validate_event_sig
from tests.events.utils import generate_event


def test_verify_event() -> None:
    event = generate_event()
    print(event)
    assert validate_event_id(event=event)
    assert validate_event_sig(event=event)
    assert validate_created_at(event=event)
