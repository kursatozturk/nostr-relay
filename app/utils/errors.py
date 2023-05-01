from enum import Enum


class ErrorTypes(str, Enum):
    validation_error = "Validation Error"
    not_found = "Not Found"
    not_implemented = 'Not Implemented'
    unknown = "Unknown"


class InvalidMessageError(Exception):
    def __init__(
        self,
        message: str,
        *,
        error_type: ErrorTypes = ErrorTypes.unknown,
        encapsulated_exc: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error_type
        self.encapsulated_exc = encapsulated_exc
