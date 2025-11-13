"""
Value object for problem status in the EGE domain.

This module defines the ProblemStatus value object and its possible values
according to domain rules and EGE regulations.
"""
from enum import Enum
from typing import Any


class ProblemStatusEnum(Enum):
    """
    Enumeration of possible problem statuses in the EGE system.
    
    These statuses reflect the lifecycle of a problem from creation to publication.
    """
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ProblemStatus:
    """
    Value object representing the status of a problem in the EGE domain.
    
    This value object encapsulates the status of a problem and ensures
    that only valid statuses according to domain rules are used.
    It maintains the invariants that the status value must be one of the
    predefined values in ProblemStatusEnum.
    
    Attributes:
        value (ProblemStatusEnum): The actual status value.
    """
    
    def __init__(self, value: ProblemStatusEnum):
        """
        Initialize the ProblemStatus value object.
        
        Args:
            value: The status value from ProblemStatusEnum.
            
        Raises:
            TypeError: If value is not a ProblemStatusEnum member.
        """
        if not isinstance(value, ProblemStatusEnum):
            raise TypeError(f"Value must be a ProblemStatusEnum member, got {type(value)}")
        self._value = value
    
    @property
    def value(self) -> ProblemStatusEnum:
        """
        Get the status value.
        
        Returns:
            ProblemStatusEnum: The status value.
        """
        return self._value
    
    def __str__(self) -> str:
        """
        Get string representation of the status.
        
        Returns:
            str: String representation of the status value.
        """
        return self._value.value
    
    def __repr__(self) -> str:
        """
        Get detailed string representation of the status.
        
        Returns:
            str: Detailed string representation.
        """
        return f"ProblemStatus({self._value})"
    
    def __eq__(self, other: Any) -> bool:
        """
        Check equality with another object.
        
        Args:
            other: Another object to compare with.
            
        Returns:
            bool: True if objects are equal, False otherwise.
        """
        if not isinstance(other, ProblemStatus):
            return NotImplemented
        return self._value == other._value
    
    def __hash__(self) -> int:
        """
        Get hash value for the status.
        
        Returns:
            int: Hash value.
        """
        return hash(self._value)
