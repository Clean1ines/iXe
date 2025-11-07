"""Business logic exceptions for the domain layer."""

from .base import BaseDomainException


class BusinessRuleException(BaseDomainException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, error_code: str = "BUSINESS_RULE_ERROR", details: dict = None):
        super().__init__(message, error_code, details)


class ValidationException(BaseDomainException):
    """Raised when input validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR", details: dict = None):
        super().__init__(message, error_code, details)


class ResourceNotFoundException(BaseDomainException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str, error_code: str = "RESOURCE_NOT_FOUND", details: dict = None):
        message = f"{resource_type} with ID '{resource_id}' not found"
        details = details or {}
        details.update({"resource_type": resource_type, "resource_id": resource_id})
        super().__init__(message, error_code, details)
