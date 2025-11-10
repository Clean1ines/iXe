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
