import pytest
from fastapi.testclient import TestClient
from api.app import create_app
from domain.exceptions.business import ValidationException, ResourceNotFoundException
from domain.exceptions.infrastructure import ExternalServiceException


@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)


class TestErrorHandlingIntegration:
    """Integration tests for error handling with FastAPI."""

    def test_domain_exception_handler(self, client):
        """Test that domain exceptions are properly handled by FastAPI."""
        # We'll test this by creating a temporary endpoint that raises a domain exception
        from fastapi import APIRouter
        from api.app import create_app
        import domain.exceptions.business as business_exceptions
        
        app = create_app()
        test_router = APIRouter()
        
        @test_router.get("/test-domain-exception")
        def test_domain_exc():
            raise business_exceptions.ValidationException(
                "Invalid input provided",
                details={"field": "email", "reason": "invalid_format"}
            )
        
        app.include_router(test_router)
        test_client = TestClient(app)
        
        response = test_client.get("/test-domain-exception")
        
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error_type"] == "ValidationException"
        assert response_data["error_code"] == "VALIDATION_ERROR"
        assert "Invalid input provided" in response_data["message"]
        assert response_data["details"]["field"] == "email"

    def test_external_service_exception_handler(self, client):
        """Test that external service exceptions are properly handled."""
        from fastapi import APIRouter
        from api.app import create_app
        import domain.exceptions.infrastructure as infra_exceptions
        
        app = create_app()
        test_router = APIRouter()
        
        @test_router.get("/test-external-exception")
        def test_external_exc():
            raise infra_exceptions.ExternalServiceException(
                service_name="Database",
                message="Connection failed",
                details={"host": "localhost", "port": 5432}
            )
        
        app.include_router(test_router)
        test_client = TestClient(app)
        
        response = test_client.get("/test-external-exception")
        
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error_type"] == "ExternalServiceException"
        assert response_data["error_code"] == "EXTERNAL_SERVICE_ERROR"
        assert "Database" in response_data["message"]
        assert response_data["details"]["service_name"] == "Database"

    def test_resource_not_found_exception_handler(self, client):
        """Test that resource not found exceptions are properly handled."""
        from fastapi import APIRouter
        from api.app import create_app
        import domain.exceptions.business as business_exceptions
        
        app = create_app()
        test_router = APIRouter()
        
        @test_router.get("/test-not-found-exception")
        def test_not_found_exc():
            raise business_exceptions.ResourceNotFoundException(
                resource_type="User",
                resource_id="123"
            )
        
        app.include_router(test_router)
        test_client = TestClient(app)
        
        response = test_client.get("/test-not-found-exception")
        
        assert response.status_code == 422
        response_data = response.json()
        assert response_data["error_type"] == "ResourceNotFoundException"
        assert response_data["error_code"] == "RESOURCE_NOT_FOUND"
        assert "User with ID '123' not found" in response_data["message"]
        assert response_data["details"]["resource_type"] == "User"
        assert response_data["details"]["resource_id"] == "123"
