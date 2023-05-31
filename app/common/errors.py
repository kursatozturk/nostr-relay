from enum import Enum


class ErrorTypes(str, Enum):
    validation_error = "Validation Error"
    not_found = "Not Found"
    not_implemented = "Not Implemented"
    invalid_argumentation = "Invalid Arguments"
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

    def __str__(self) -> str:
        return f"{self.error} [{self.encapsulated_exc!r}]"


class NostrValidationError(InvalidMessageError):
    def __init__(self, message: str, *, encapsulated_exc: Exception | None = None) -> None:
        super().__init__(message, error_type=ErrorTypes.validation_error, encapsulated_exc=encapsulated_exc)
