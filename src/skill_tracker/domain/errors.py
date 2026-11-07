"""Domain-level exceptions."""


class DomainError(Exception):
    """Base class for errors that describe a violated domain rule."""


class ValidationError(DomainError):
    """Raised when a value object or entity is given invalid data."""


class EntityNotFoundError(DomainError):
    """Raised when an operation targets an entity that does not exist."""
