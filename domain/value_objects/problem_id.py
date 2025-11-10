from dataclasses import dataclass
from typing import NewType
import re

ProblemIdValue = NewType('ProblemIdValue', str)

@dataclass(frozen=True)
class ProblemId:
    value: ProblemIdValue
    
    def __post_init__(self):
        if not self._is_valid_format():
            raise ValueError(f"Invalid problem ID format: {self.value}")
    
    def _is_valid_format(self) -> bool:
        # Пример формата: "math_1_2024_1" или "rus_12_2023_5"
        pattern = r'^[a-z]+_\d+_\d{4}_\d+$'
        return bool(re.match(pattern, self.value))
    
    def __str__(self) -> str:
        return self.value
