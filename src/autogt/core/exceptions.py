"""Core exceptions for AutoGT platform."""


class AutoGTError(Exception):
    """Base exception for all AutoGT errors."""
    pass


class ValidationError(AutoGTError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message)
        self.field = field
        self.value = value


class FileParsingError(AutoGTError):
    """Raised when file parsing fails."""
    
    def __init__(self, message: str, filename: str = None):
        super().__init__(message)
        self.filename = filename


class ConfigurationError(AutoGTError):
    """Raised when configuration is invalid."""
    pass


class DatabaseError(AutoGTError):
    """Raised when database operations fail."""
    pass


class AIServiceError(AutoGTError):
    """Raised when AI service operations fail."""
    
    def __init__(self, message: str, service: str = None):
        super().__init__(message)
        self.service = service


class AuthenticationError(AutoGTError):
    """Raised when authentication fails."""
    pass


class AuthorizationError(AutoGTError):
    """Raised when authorization fails."""
    pass


class ResourceNotFoundError(AutoGTError):
    """Raised when requested resource is not found."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitError(AutoGTError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class ExportError(AutoGTError):
    """Raised when data export fails."""
    
    def __init__(self, message: str, format: str = None):
        super().__init__(message)
        self.format = format


class AnalysisError(AutoGTError):
    """Raised when TARA analysis fails."""
    
    def __init__(self, message: str, analysis_id: str = None):
        super().__init__(message)
        self.analysis_id = analysis_id