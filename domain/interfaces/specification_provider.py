from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class ISpecificationProvider(ABC):
    """Domain interface for specification data access."""

    @abstractmethod
    def get_task_spec(self, task_number: int) -> Optional[Dict]:
        """Get official task specification by number (1–19)."""
        pass

    @abstractmethod
    def explain_kos(self, kos_code: str) -> str:
        """Return human-readable KOS description."""
        pass

    @abstractmethod
    def explain_kes(self, kes_code: str) -> str:
        """Return human-readable KES description."""
        pass

    @abstractmethod
    def get_feedback_for_task(self, task_number: int) -> Dict[str, Any]:
        """
        Generate pedagogical feedback for a given task number.
        Returns structured feedback including KOS explanation, KES topics, and next steps.
        """
        pass
