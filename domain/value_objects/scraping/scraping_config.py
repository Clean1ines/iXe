"""
Configuration value objects for scraping operations.

These value objects encapsulate scraping configuration parameters,
ensuring type safety and providing sensible defaults.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class ScrapingMode(Enum):
    """Enumeration of scraping modes."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    SINGLE_PAGE = "single_page"

@dataclass(frozen=True)
class ScrapingConfig:
    """
    Value object for scraping configuration.
    
    Business Rules:
    - Immutable configuration object
    - Provides sensible defaults for all parameters
    - Validates configuration parameters
    - Supports both sequential and parallel modes
    """
    mode: ScrapingMode = ScrapingMode.SEQUENTIAL
    max_empty_pages: int = 2
    start_page: str = "init"
    max_pages: Optional[int] = None
    force_restart: bool = False
    parallel_workers: int = 3
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_empty_pages < 1:
            raise ValueError("max_empty_pages must be at least 1")
        if self.parallel_workers < 1:
            raise ValueError("parallel_workers must be at least 1")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")
        if self.retry_attempts < 0:
            raise ValueError("retry_attempts cannot be negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds cannot be negative")
    
    @classmethod
    def for_sequential_scraping(cls, **kwargs) -> "ScrapingConfig":
        """Create configuration for sequential scraping."""
        return cls(mode=ScrapingMode.SEQUENTIAL, **kwargs)
    
    @classmethod
    def for_parallel_scraping(cls, **kwargs) -> "ScrapingConfig":
        """Create configuration for parallel scraping."""
        return cls(mode=ScrapingMode.PARALLEL, **kwargs)
    
    @classmethod
    def for_single_page(cls, page_number: str, **kwargs) -> "ScrapingConfig":
        """Create configuration for single page scraping."""
        return cls(
            mode=ScrapingMode.SINGLE_PAGE,
            start_page=page_number,
            max_pages=1,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "mode": self.mode.value,
            "max_empty_pages": self.max_empty_pages,
            "start_page": self.start_page,
            "max_pages": self.max_pages,
            "force_restart": self.force_restart,
            "parallel_workers": self.parallel_workers,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
            "user_agent": self.user_agent
        }
