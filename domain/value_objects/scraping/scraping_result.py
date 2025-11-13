"""
Result value objects for scraping operations.

These value objects encapsulate the results of scraping operations,
providing a consistent interface for reporting success and failure.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from domain.models.problem import Problem

@dataclass(frozen=True)
class ScrapingPageResult:
    """
    Value object representing result of scraping a single page.
    
    Business Rules:
    - Immutable result object
    - Contains all relevant metrics for a page
    - Distinguishes between successful and failed scraping
    - Provides detailed error information when needed
    """
    page_number: str
    success: bool
    problems_found: int = 0
    problems_saved: int = 0
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    raw_html_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "page_number": self.page_number,
            "success": self.success,
            "problems_found": self.problems_found,
            "problems_saved": self.problems_saved,
            "errors": self.errors,
            "timestamp": self.timestamp.isoformat(),
            "raw_html_path": self.raw_html_path,
            "metadata": self.metadata
        }

@dataclass(frozen=True)
class ScrapingSubjectResult:
    """
    Value object representing result of scraping a subject.
    
    Business Rules:
    - Aggregates results from multiple pages
    - Provides overall success/failure status
    - Contains summary statistics
    - Maintains detailed page results for debugging
    """
    subject_name: str
    success: bool
    total_pages: int = 0
    total_problems_found: int = 0
    total_problems_saved: int = 0
    page_results: List[ScrapingPageResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Get duration of scraping in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_problems_found == 0:
            return 0.0
        return (self.total_problems_saved / self.total_problems_found) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "subject_name": self.subject_name,
            "success": self.success,
            "total_pages": self.total_pages,
            "total_problems_found": self.total_problems_found,
            "total_problems_saved": self.total_problems_saved,
            "page_results": [result.to_dict() for result in self.page_results],
            "errors": self.errors,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "metadata": self.metadata
        }
