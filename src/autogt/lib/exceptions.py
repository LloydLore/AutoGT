"""AutoGT exception classes."""


class AutoGTError(Exception):
    """Base exception for AutoGT."""
    pass


class ValidationError(AutoGTError):
    """Validation-related errors."""
    pass


class DatabaseError(AutoGTError):
    """Database-related errors."""
    pass


class AIError(AutoGTError):
    """AI agent-related errors."""
    pass