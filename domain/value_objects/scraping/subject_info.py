"""
Value objects for scraping operations.

These value objects encapsulate domain concepts related to scraping,
ensuring data integrity and providing meaningful domain semantics.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

@dataclass(frozen=True)
class SubjectInfo:
    """
    Value object representing subject information for scraping.
    
    Business Rules:
    - Immutable after creation
    - Contains all necessary subject identification data
    - Provides derived properties for common operations
    - Validates data during construction
    """
    official_name: str
    alias: str
    subject_key: str
    proj_id: str
    exam_year: str = "2026"
    
    def __post_init__(self):
        """Validate subject information after initialization."""
        if not self.official_name:
            raise ValueError("Official name cannot be empty")
        if not self.alias:
            raise ValueError("Alias cannot be empty")
        if not self.subject_key:
            raise ValueError("Subject key cannot be empty")
        if not self.proj_id:
            raise ValueError("Project ID cannot be empty")
    
    @property
    def output_directory(self) -> Path:
        """Get output directory path for this subject."""
        return Path("data") / self.alias / self.exam_year
    
    @property
    def database_path(self) -> Path:
        """Get database path for this subject."""
        return self.output_directory / "fipi_data.db"
    
    @property
    def raw_html_directory(self) -> Path:
        """Get raw HTML directory path for this subject."""
        return self.output_directory / "raw_html"
    
    @classmethod
    def from_official_name(cls, official_name: str, exam_year: str = "2026") -> "SubjectInfo":
        """
        Create SubjectInfo from official name.
        
        Args:
            official_name: Official subject name in Russian
            exam_year: Exam year
            
        Returns:
            SubjectInfo instance
            
        Business Rules:
        - Uses subject mapping utilities for conversion
        - Falls back to defaults for missing information
        - Raises meaningful errors for invalid subjects
        """
        from utils.subject_mapping import (
            get_alias_from_official_name,
            get_subject_key_from_alias,
            get_proj_id_for_subject
        )
        
        try:
            alias = get_alias_from_official_name(official_name)
            subject_key = get_subject_key_from_alias(alias)
            proj_id = get_proj_id_for_subject(subject_key)
            
            return cls(
                official_name=official_name,
                alias=alias,
                subject_key=subject_key,
                proj_id=proj_id,
                exam_year=exam_year
            )
        except KeyError as e:
            raise ValueError(f"Subject '{official_name}' not found in mappings: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "official_name": self.official_name,
            "alias": self.alias,
            "subject_key": self.subject_key,
            "proj_id": self.proj_id,
            "exam_year": self.exam_year,
            "output_directory": str(self.output_directory),
            "database_path": str(self.database_path)
        }
