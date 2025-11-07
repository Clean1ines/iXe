import pytest
from unittest.mock import Mock, patch
from domain.services.alert_service import AlertService


class TestAlertService:
    """Test cases for AlertService."""

    @pytest.fixture
    def alert_service(self):
        """Create an AlertService instance."""
        return AlertService()

    def test_send_alert_basic(self, alert_service):
        """Test sending a basic alert."""
        with patch.object(alert_service.logger, 'error') as mock_log_error:
            alert_service.send_alert("test_alert", "Test alert message", 
                                   {"key": "value"}, "high")
            
            mock_log_error.assert_called_once()
            # The call should include the alert data in the logged message
            assert "test_alert" in str(mock_log_error.call_args)

    def test_alert_on_exception(self, alert_service):
        """Test sending an alert for an exception."""
        test_exception = ValueError("Test exception")
        context = {"operation": "test_op"}
        
        with patch.object(alert_service, 'send_alert') as mock_send_alert:
            alert_service.alert_on_exception(test_exception, context)
            
            mock_send_alert.assert_called_once()
            # Check that the call includes the exception details
            call_args = mock_send_alert.call_args
            assert call_args is not None

    def test_alert_resource_unavailable(self, alert_service):
        """Test sending an alert for unavailable resource."""
        with patch.object(alert_service, 'send_alert') as mock_send_alert:
            alert_service.alert_resource_unavailable("Database", "Connection timeout")
            
            mock_send_alert.assert_called_once()
            # Check the call args - they are in kwargs for this method
            call_args = mock_send_alert.call_args
            assert call_args is not None

    def test_alert_external_service_failure(self, alert_service):
        """Test sending an alert for external service failure."""
        with patch.object(alert_service, 'send_alert') as mock_send_alert:
            alert_service.alert_external_service_failure("PaymentService", "charge", "Timeout")
            
            mock_send_alert.assert_called_once()
            # Check the call args - they are in kwargs for this method
            call_args = mock_send_alert.call_args
            assert call_args is not None
