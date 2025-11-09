from abc import ABC, abstractmethod
from typing import Optional, List

class IMetadataParser(ABC):
    @abstractmethod
    def extract_task_number(self, header_text: str) -> Optional[int]:
        pass

    @abstractmethod
    def extract_kes_codes(self, header_text: str) -> List[str]:
        pass

    @abstractmethod
    def extract_kos_codes(self, header_text: str) -> List[str]:
        pass
