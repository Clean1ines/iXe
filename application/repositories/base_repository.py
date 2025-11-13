"""
Base repository class for DDD-compliant repositories.

This class provides common functionality for all repository implementations
including logging, type conversion utilities, and error handling patterns.
"""
import logging
from typing import Optional, Any
from domain.value_objects.problem_id import ProblemId

logger = logging.getLogger(__name__)

class BaseRepository:
    """
    Base class for all repository implementations.
    
    Provides common functionality:
    - Standardized logging
    - Type conversion utilities
    - Error handling patterns
    - Value Object conversion helpers
    
    All repository implementations should inherit from this class
    to ensure consistent behavior and reduce code duplication.
    """
    
    def __init__(self):
        """Initialize base repository with standard logger."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _convert_problem_id(self, problem_id: Any) -> str:
        """
        Convert ProblemId value object to string for infrastructure layer.
        
        Business Rules:
        - Handles both ProblemId objects and raw strings
        - Ensures compatibility with database adapters
        - Preserves original behavior for backward compatibility
        
        Args:
            problem_id: ProblemId object or string representation
            
        Returns:
            String representation of problem ID
        """
        if isinstance(problem_id, ProblemId):
            return str(problem_id.value)
        if hasattr(problem_id, 'value'):
            return str(problem_id.value)
        return str(problem_id)
    
    def _handle_conversion_error(self, entity_type: str, error: Exception) -> None:
        """
        Handle errors during domain-to-infrastructure conversion.
        
        Business Rules:
        - Standardized error logging
        - Preserves original exception context
        - Provides clear error messages
        
        Args:
            entity_type: Type of entity being converted
            error: Original exception
            
        Raises:
            Exception: Re-raises the original exception after logging
        """
        self.logger.error(f"Failed to convert {entity_type} entity: {error}", exc_info=True)
        raise
    
    def _safe_getattr(self, obj: Any, attr_name: str, default: Any = None) -> Any:
        """
        Safely get attribute from object with fallback to default.
        
        Business Rules:
        - Handles missing attributes gracefully
        - Provides default values when attributes don't exist
        - Prevents AttributeError crashes
        
        Args:
            obj: Object to get attribute from
            attr_name: Name of attribute to retrieve
            default: Default value if attribute doesn't exist
            
        Returns:
            Attribute value or default
        """
        return getattr(obj, attr_name, default)
