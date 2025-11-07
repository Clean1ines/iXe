import pytest
from unittest.mock import Mock, patch, MagicMock
from domain.services.observability_service import ObservabilityService
from domain.services.alert_service import AlertService


class TestObservabilityService:
    """Test cases for ObservabilityService."""

    @pytest.fixture(autouse=True)
    def configure_structlog_for_test(self):
        """Configure structlog specifically for this test class to avoid format_exc_info issues."""
        from utils.logging_config import configure_logging_dev
        configure_logging_dev()

    @pytest.fixture
    def alert_service(self):
        """Create a mock alert service."""
        return Mock(spec=AlertService)

    @pytest.fixture
    def observability_service(self, alert_service):
        """Create an ObservabilityService instance with mocked dependencies."""
        return ObservabilityService(alert_service=alert_service)

    def test_log_info(self, observability_service):
        """Test logging info messages."""
        # Just test that the method can be called without error
        try:
            observability_service.log_info("Test info message", {"key": "value"})
            success = True
        except Exception:
            success = False
        assert success

    def test_log_error_with_alert(self, observability_service, alert_service):
        """Test logging error messages with alert."""
        test_exception = ValueError("Test error")  # Use a simpler exception
        context = {"key": "value"}
        
        try:
            # Теперь вызываем с exception, как и задумывалось
            observability_service.log_error("Test error message", 
                                          exception=test_exception, 
                                          context=context, 
                                          alert=True)
            success = True
        except Exception as e:
            success = False
            print(f"Exception during test: {e}")
                
        assert success
        # Alert должен быть вызван
        alert_service.alert_on_exception.assert_called_once()

    def test_log_error_without_alert(self, observability_service, alert_service):
        """Test logging error messages without alert."""
        test_exception = ValueError("Test error")  # Use a simpler exception
        context = {"key": "value"}
        
        try:
            # Вызовем log_error с exception, но без alert
            observability_service.log_error("Test error message", 
                                          exception=test_exception,
                                          context=context,
                                          alert=False)
            success = True
        except Exception as e:
            success = False
            print(f"Exception during test: {e}")
            
        assert success
        # Alert НЕ должен быть вызван
        alert_service.alert_on_exception.assert_not_called()

    def test_log_warning(self, observability_service):
        """Test logging warning messages."""
        # Just test that the method can be called without error
        try:
            observability_service.log_warning("Test warning message", {"key": "value"})
            success = True
        except Exception:
            success = False
        assert success

    def test_log_metric(self, observability_service):
        """Test logging metrics."""
        # Just test that the method can be called without error
        try:
            observability_service.log_metric("test_metric", 10.5, {"tag1": "value1"})
            success = True
        except Exception:
            success = False
        assert success

    def test_generate_trace_id(self, observability_service):
        """Test generation of trace IDs."""
        trace_id = observability_service.generate_trace_id()
        
        # Should be a string representation of a UUID
        assert isinstance(trace_id, str)
        assert len(trace_id) == 36  # UUID4 length
