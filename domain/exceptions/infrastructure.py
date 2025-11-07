"""Infrastructure-related exceptions for the domain layer."""

from .base import BaseDomainException


class InfrastructureException(BaseDomainException):
    """Raised when an infrastructure-related error occurs."""

    def __init__(self, message: str, error_code: str = "INFRASTRUCTURE_ERROR", details: dict = None):
        super().__init__(message, error_code, details)


class ExternalServiceException(BaseDomainException):
    """Raised when an external service call fails."""

    def __init__(self, service_name: str, message: str, error_code: str = "EXTERNAL_SERVICE_ERROR", details: dict = None):
        message = f"External service '{service_name}' error: {message}"
        details = details or {}
        details.update({"service_name": service_name})
        super().__init__(message, error_code, details)


class ResourceUnavailableException(BaseDomainException):
    """Raised when a required resource is temporarily unavailable."""

    def __init__(self, resource_name: str, message: str = None, error_code: str = "RESOURCE_UNAVAILABLE", details: dict = None):
        message = message or f"Resource '{resource_name}' is currently unavailable"
        details = details or {}
        details.update({"resource_name": resource_name})
        super().__init__(message, error_code, details)
