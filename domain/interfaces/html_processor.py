from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from bs4.element import Tag


class IHTMLProcessor(ABC):
    """Domain interface for HTML processing operations."""
    
    @abstractmethod
    async def process_html_block(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a single HTML block pair and return structured data."""
        pass


class ITaskClassifier(ABC):
    """Domain interface for task classification operations."""
    
    @abstractmethod
    def classify_task(
        self, 
        kes_codes: List[str], 
        kos_codes: List[str], 
        answer_type: str
    ) -> Dict[str, Any]:
        """Classify a task based on KES/KOS codes and return classification result."""
        pass
