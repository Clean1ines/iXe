import pytest
from domain.exceptions.base import BaseDomainException
from domain.exceptions.business import ValidationException, ResourceNotFoundException
from domain.exceptions.infrastructure import ExternalServiceException


class TestDomainExceptions:
    """Test cases for domain exception hierarchy."""

    def test_base_domain_exception_creation(self):
        """Test creation of base domain exception."""
        exc = BaseDomainException("Test message", "TEST_ERROR", {"key": "value"})
        
        assert str(exc) == "[TEST_ERROR] Test message"
        assert exc.message == "Test message"
        assert exc.error_code == "TEST_ERROR"
        assert exc.details == {"key": "value"}
        
    def test_base_domain_exception_default_error_code(self):
        """Test default error code when not specified."""
        exc = BaseDomainException("Test message")
        
        assert exc.error_code == "DOMAIN_ERROR"
        
    def test_base_domain_exception_to_dict(self):
        """Test conversion to dictionary for logging."""
        exc = BaseDomainException("Test message", "TEST_ERROR", {"key": "value"})
        exc_dict = exc.to_dict()
        
        expected = {
            "error_type": "BaseDomainException",
            "error_code": "TEST_ERROR",
            "message": "Test message",
            "details": {"key": "value"}
        }
        
        assert exc_dict == expected
        
    def test_validation_exception(self):
        """Test ValidationException."""
        exc = ValidationException("Invalid input", details={"field": "email"})
        
        assert exc.error_code == "VALIDATION_ERROR"
        assert "Invalid input" in str(exc)
        assert exc.details["field"] == "email"
        
    def test_resource_not_found_exception(self):
        """Test ResourceNotFoundException."""
        exc = ResourceNotFoundException("User", "123")
        
        assert exc.error_code == "RESOURCE_NOT_FOUND"
        assert "User with ID '123' not found" in str(exc)
        assert exc.details["resource_type"] == "User"
        assert exc.details["resource_id"] == "123"
        
    def test_external_service_exception(self):
        """Test ExternalServiceException."""
        exc = ExternalServiceException("Database", "Connection failed")
        
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert "External service 'Database' error: Connection failed" in str(exc)
        assert exc.details["service_name"] == "Database"
