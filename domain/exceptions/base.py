"""Base exceptions for the domain layer."""

class BaseDomainException(Exception):
    """Base exception for all domain-related exceptions."""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., VALIDATION_ERROR)
            details: Additional structured details about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "DOMAIN_ERROR"
        self.details = details or {}

    def __str__(self):
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> dict:
        """Convert the exception to a dictionary for structured logging."""
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }
