"""Service for centralized alerting on critical errors."""

import logging
from typing import Dict, Any, Optional
from utils.logging_config import get_logger


class AlertService:
    """Centralized service for sending alerts on critical errors."""

    def __init__(self):
        """Initialize the alert service."""
        self.logger = get_logger(__name__)
        # In a real system, you would initialize connections to alerting systems like Slack, email, etc.
        # For now, we'll just log alerts

    def send_alert(self, alert_type: str, message: str, details: Dict[str, Any] = None, severity: str = "high") -> None:
        """
        Send an alert about a critical issue.

        Args:
            alert_type: Type of alert (e.g., "database_failure", "external_service_down")
            message: Alert message
            details: Additional structured details about the alert
            severity: Severity level ("low", "medium", "high", "critical")
        """
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "severity": severity,
            "details": details or {},
        }
        
        # Log the alert
        self.logger.error(f"ALERT [{severity.upper()}]: {message}", extra=alert_data)
        
        # In a real system, you would send this to Slack, email, etc.
        # For example:
        # self._send_to_slack(alert_data)
        # self._send_to_email(alert_data)
        
        # For now, just log it
        print(f"ALERT [{severity.upper()}]: {alert_type} - {message}")
        if details:
            print(f"  Details: {details}")

    def alert_on_exception(self, exc: Exception, context: Dict[str, Any] = None) -> None:
        """
        Send an alert when an exception occurs.

        Args:
            exc: Exception that occurred
            context: Additional context about where the exception occurred
        """
        alert_type = "exception_occurred"
        message = f"Critical exception occurred: {type(exc).__name__} - {str(exc)}"
        
        details = context or {}
        details["exception_type"] = type(exc).__name__
        details["exception_message"] = str(exc)
        
        # Determine severity based on exception type
        severity = "high"
        if isinstance(exc, (MemoryError, KeyboardInterrupt)):
            severity = "critical"
        
        self.send_alert(alert_type, message, details, severity)

    def alert_resource_unavailable(self, resource_name: str, reason: str = None) -> None:
        """
        Send an alert when a resource becomes unavailable.

        Args:
            resource_name: Name of the unavailable resource
            reason: Reason why the resource is unavailable
        """
        message = f"Resource '{resource_name}' is unavailable"
        if reason:
            message += f": {reason}"
            
        self.send_alert(
            alert_type="resource_unavailable",
            message=message,
            details={"resource_name": resource_name, "reason": reason},
            severity="high"
        )

    def alert_external_service_failure(self, service_name: str, operation: str = None, error_details: str = None) -> None:
        """
        Send an alert when an external service fails.

        Args:
            service_name: Name of the failing external service
            operation: Operation that failed
            error_details: Details about the error
        """
        message = f"External service '{service_name}' failed"
        if operation:
            message += f" on operation '{operation}'"
            
        details = {
            "service_name": service_name,
            "operation": operation,
            "error_details": error_details
        }
        
        self.send_alert(
            alert_type="external_service_failure",
            message=message,
            details=details,
            severity="high"
        )
