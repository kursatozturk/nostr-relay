import datetime
from hashlib import sha256

import secp256k1
from common.errors import NostrValidationError

from events.data import Event


def validate_pubkey(event: Event) -> bool:
    # If it is invalid, it will (hopefully) throw Invalid Public Key Error
    try:
        secp256k1.PublicKey(bytes.fromhex("02" + event.pubkey), True)
        return True
    except Exception as exc:
        raise NostrValidationError("Cannot Validate Pubkey: ", encapsulated_exc=exc)


def validate_event_id(event: Event) -> bool:
    computed_id = sha256(event.serializeable.encode())
    if computed_id.hexdigest() != event.id:
        raise NostrValidationError("Event Id is not valid!")
    return True


def validate_event_sig(event: Event) -> bool:
    pubkey = secp256k1.PublicKey(bytes.fromhex("02" + event.pubkey), True)
    if pubkey.schnorr_verify(bytes.fromhex(event.id), bytes.fromhex(event.sig), "", True):
        return True
    else:
        raise NostrValidationError("Event Signature is not valid!")


def validate_created_at(event: Event) -> bool:
    now = datetime.datetime.now().timestamp()
    a_week_before = now - 24 * 60 * 60 * 7
    if event.created_at < a_week_before or event.created_at > now:
        raise NostrValidationError("Event Timestamp is too old!")
    return True


validators = (validate_pubkey, validate_event_id, validate_event_sig, validate_created_at)


def validate_event(event: Event) -> bool:
    return all(validator(event) for validator in validators)
