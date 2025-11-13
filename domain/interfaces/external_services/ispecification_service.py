"""
Domain interfaces for specification services.

These interfaces define contracts for working with exam specifications,
KES/KOS mappings, and other educational standards data.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class ISpecificationService(ABC):
    """
    Interface for specification services.
    
    Business Rules:
    - Provides access to exam specifications and standards
    - Handles mapping between different educational codes
    - Abstracts away data source details (JSON files, APIs, etc.)
    - Ensures consistency of specification data
    """
    
    @abstractmethod
    async def get_task_specification(self, task_number: str, subject: str) -> Optional[Dict[str, Any]]:
        """
        Get task specification by task number and subject.
        
        Args:
            task_number: Task number (e.g., "1", "2", "19")
            subject: Subject name (e.g., "mathematics", "informatics")
            
        Returns:
            Task specification dictionary if found, None otherwise
            
        Business Rules:
        - Must handle invalid task numbers gracefully
        - Should support multiple subjects
        - Must return consistent data structure
        """
        pass
    
    @abstractmethod
    async def get_kes_kos_mapping(self, subject: str) -> Dict[str, List[str]]:
        """
        Get KES/KOS mapping for a subject.
        
        Args:
            subject: Subject name
            
        Returns:
            Dictionary mapping KES codes to KOS codes
            
        Business Rules:
        - Must handle subjects without mappings gracefully
        - Should return empty dictionary if no mappings exist
        - Must maintain consistent key-value format
        """
        pass
    
    @abstractmethod
    async def get_difficulty_levels(self) -> List[str]:
        """
        Get available difficulty levels.
        
        Returns:
            List of difficulty level names
            
        Business Rules:
        - Must return consistent difficulty level names
        - Should include all supported difficulty levels
        """
        pass
    
    @abstractmethod
    async def get_exam_parts(self) -> List[str]:
        """
        Get available exam parts.
        
        Returns:
            List of exam part names
            
        Business Rules:
        - Must return consistent exam part names
        - Should include all exam parts for supported subjects
        """
        pass
