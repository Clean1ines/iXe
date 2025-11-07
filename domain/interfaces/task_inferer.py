from abc import ABC, abstractmethod
from typing import List, Optional


class ITaskNumberInferer(ABC):
    """Domain interface for task number inference operations."""
    
    @abstractmethod
    def infer(self, kes_codes: List[str], answer_type: str) -> Optional[int]:
        """Infer the official ЕГЭ task number from KES codes and answer type."""
        pass
