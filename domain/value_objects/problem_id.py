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
EOFcat <<'EOF' > domain/value_objects/problem_id.py
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
EOFcat <<'EOF' > domain/value_objects/difficulty_level.py
from dataclasses import dataclass
from enum import Enum
from typing import NewType

class DifficultyLevelEnum(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate" 
    ADVANCED = "advanced"

@dataclass(frozen=True)
class DifficultyLevel:
    value: DifficultyLevelEnum
    
    def __post_init__(self):
        if not isinstance(self.value, DifficultyLevelEnum):
            try:
                self.__dict__['value'] = DifficultyLevelEnum(self.value)
            except ValueError:
                allowed = [level.value for level in DifficultyLevelEnum]
                raise ValueError(f"Difficulty level must be one of {allowed}: {self.value}")
    
    @classmethod
    def basic(cls):
        return cls(DifficultyLevelEnum.BASIC)
    
    @classmethod
    def intermediate(cls):
        return cls(DifficultyLevelEnum.INTERMEDIATE)
    
    @classmethod
    def advanced(cls):
        return cls(DifficultyLevelEnum.ADVANCED)
    
    def __str__(self) -> str:
        return self.value.value
