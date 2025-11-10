from dataclasses import dataclass
from enum import Enum
from typing import NewType

class ProblemTypeEnum(Enum):
    NUMBER = "number"
    TEXT = "text"
    MULTIPLE_CHOICE = "multiple_choice"
    MATCHING = "matching"
    SHORT_ANSWER = "short_answer"
    ESSAY = "essay"

@dataclass(frozen=True)
class ProblemType:
    value: ProblemTypeEnum
    
    def __post_init__(self):
        if not isinstance(self.value, ProblemTypeEnum):
            try:
                self.__dict__['value'] = ProblemTypeEnum(self.value)
            except ValueError:
                allowed = [ptype.value for ptype in ProblemTypeEnum]
                raise ValueError(f"Problem type must be one of {allowed}: {self.value}")
    
    def __str__(self) -> str:
        return self.value.value
