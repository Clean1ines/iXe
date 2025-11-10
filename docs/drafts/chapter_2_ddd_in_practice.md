# Глава 2: Практика DDD в проекте iXe

## 2.1. Моделирование предметной области

В предыдущей главе мы обозначили, что проект iXe уже имеет слоистую архитектуру, но доменные сущности страдают от "анемичной модели". Настало время изменить это. В DDD сущности и агрегаты — это не просто контейнеры данных, они содержат бизнес-логику и инварианты.

### 2.1.1. Агрегат `Problem`

Текущая модель `Problem` в `domain/models/problem_schema.py` представляет собой Pydantic-схему. Для приведения её к истинно доменной сущности, мы должны добавить поведение и инварианты.

**Пример инварианта:**
```python
# domain/models/problem_schema.py
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any

class Problem(BaseModel):
    problem_id: str
    subject: str
    type: str
    text: str
    difficulty_level: str
    exam_part: str
    max_score: int = 1
    # ... другие поля ...

    @field_validator('problem_id')
    def problem_id_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Problem ID cannot be empty')
        return v

    @field_validator('difficulty_level')
    def validate_difficulty_level(cls, v):
        allowed_levels = {'basic', 'intermediate', 'advanced'}
        if v not in allowed_levels:
            raise ValueError(f'difficulty_level must be one of {allowed_levels}')
        return v

    def calculate_score(self, user_answer: str) -> int:
        """Вычисляет балл за ответ. Это сложная бизнес-логика, возможно, требующая внешнего сервиса."""
        # Пока заглушка, но место для инкапсуляции логики проверки
        # В идеале, сюда должен быть внедрен IExternalChecker через сервис
        raise NotImplementedError("Проверка ответов вынесена в AnswerService, но логика может быть делегирована сюда")

    def is_answer_type_valid(self, answer: str) -> bool:
        """Проверяет, соответствует ли тип ответа ожидаемому для этой задачи."""
        # Пример: задача на числа -> ответ должен быть числом
        # Логика зависит от self.type
        if self.type == "number":
            try:
                float(answer)
                return True
            except ValueError:
                return False
        elif self.type == "text":
            return isinstance(answer, str) and len(answer.strip()) > 0
        # ... другие проверки
        return True # По умолчанию разрешаем
```

### 2.1.2. Агрегат `UserProgress`

Этот агрегат пока не существует, но он критически важен для функциональности квиза и адаптивного обучения.

```python
# domain/models/user_progress.py
from dataclasses import dataclass
from datetime import datetime
from typing import List
from enum import Enum

class ProgressStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

@dataclass
class UserProgress:
    user_id: str
    problem_id: str
    status: ProgressStatus
    score: float = 0.0
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    events: List[DomainEvent] = None # Для событийной архитектуры

    def __post_init__(self):
        if self.events is None:
            self.events = []

    def record_attempt(self, is_correct: bool, score: float):
        """Обновляет прогресс на основе попытки."""
        self.attempts += 1
        self.last_attempt_at = datetime.now()
        self.score = max(self.score, score) # Сохраняем лучший результат
        if is_correct:
            self.status = ProgressStatus.COMPLETED
        else:
            self.status = ProgressStatus.IN_PROGRESS

        # Генерируем событие
        event = AttemptRecordedEvent(self.user_id, self.problem_id, is_correct, score)
        self.events.append(event)

    def can_retry(self) -> bool:
        """Проверяет, может ли пользователь повторить попытку."""
        # Пример бизнес-правила: не более 3 попыток в день
        if self.attempts >= 3 and self.last_attempt_at:
            time_since_last = datetime.now() - self.last_attempt_at
            return time_since_last.days >= 1
        return True
```

### 2.1.3. Агрегат `Skill`

Агрегат `Skill` важен для адаптивного обучения.

```python
# domain/models/skill.py (новый файл)
from dataclasses import dataclass
from typing import List, Set

@dataclass
class Skill:
    skill_id: str
    name: str
    description: str
    prerequisites: List[str] # Список skill_id
    related_problems: List[str] # Список problem_id

    def is_prerequisite_satisfied_by(self, user_skills: Set[str]) -> bool:
        """Проверяет, удовлетворены ли все предварительные навыки пользователем."""
        return set(self.prerequisites).issubset(user_skills)
```

## 2.2. Интерфейсы репозиториев

Как мы уже обсуждали, интерфейсы адаптеров находятся в доменном слое. Это правильно. Однако текущий `IDatabaseProvider` слишком общий. Следуя DDD, мы должны определить конкретные интерфейсы репозиториев для каждого агрегата.

```python
# domain/interfaces/repositories.py (новый файл)
from abc import abstractmethod
from typing import Protocol, List, Optional
from domain.models.problem_schema import Problem
from domain.models.user_progress import UserProgress
from domain.models.skill import Skill

class IProblemRepository(Protocol):
    @abstractmethod
    async def save(self, problem: Problem) -> None: ...
    
    @abstractmethod
    async def get_by_id(self, problem_id: str) -> Optional[Problem]: ...
    
    @abstractmethod
    async def get_by_subject(self, subject: str) -> List[Problem]: ...
    
    @abstractmethod
    async def get_by_exam_part(self, exam_part: str) -> List[Problem]: ...

class IUserProgressRepository(Protocol):
    @abstractmethod
    async def save(self, progress: UserProgress) -> None: ...
    
    @abstractmethod
    async def get_by_user_and_problem(self, user_id: str, problem_id: str) -> Optional[UserProgress]: ...
    
    @abstractmethod
    async def get_by_user(self, user_id: str) -> List[UserProgress]: ...

class ISkillRepository(Protocol):
    @abstractmethod
    async def get_by_id(self, skill_id: str) -> Optional[Skill]: ...
    
    @abstractmethod
    async def get_all(self) -> List[Skill]: ...
    
    @abstractmethod
    async def get_by_problem_id(self, problem_id: str) -> List[Skill]: ...
```

Эти интерфейсы теперь можно использовать в сервисах прикладного уровня, инъецируя их через зависимости FastAPI, как это уже делается в `api/dependencies.py`.

## 2.3. Сервисы прикладного уровня

Сервисы прикладного уровня (`application/services/`) координируют работу между агрегатами и репозиториями. Они реализуют сценарии использования (use cases) приложения.

Например, `QuizService` должен использовать `IProblemRepository`, `IUserProgressRepository` и `ISkillRepository` для реализации логики выбора задач.

```python
# application/services/quiz_service.py (обновленный)
from domain.interfaces.repositories import IProblemRepository, IUserProgressRepository, ISkillRepository
from domain.models.user_progress import UserProgress, ProgressStatus
from domain.models.problem_schema import Problem
from typing import List

class QuizApplicationService:
    def __init__(
        self,
        problem_repo: IProblemRepository,
        progress_repo: IUserProgressRepository,
        skill_repo: ISkillRepository,
    ):
        self._problem_repo = problem_repo
        self._progress_repo = progress_repo
        self._skill_repo = skill_repo

    async def start_quiz(self, user_id: str, subject: str) -> List[Problem]:
        """Сценарий использования: начать квиз."""
        # 1. Получить задачи по предмету
        all_problems = await self._problem_repo.get_by_subject(subject)

        # 2. Получить прогресс пользователя
        user_progress_list = await self._progress_repo.get_by_user(user_id)
        completed_problem_ids = {p.problem_id for p in user_progress_list if p.status == ProgressStatus.COMPLETED}

        # 3. Отфильтровать задачи, которые пользователь уже прошел
        available_problems = [p for p in all_problems if p.problem_id not in completed_problem_ids]

        # 4. (Заглушка) Выбрать 5 случайных задач
        # В будущем здесь будет сложная логика адаптивного выбора
        selected_problems = available_problems[:5]

        # 5. (Заглушка) Сохранить сессию квиза
        # ...

        return selected_problems
```

Таким образом, мы разделяем чистую бизнес-логику (в агрегатах) от координации (в сервисах прикладного уровня) и от реализации доступа к данным (в адаптерах инфраструктуры).

## 2.4. Выводы

Применение принципов DDD к проекту iXe позволяет:
- **Изолировать бизнес-логику** в агрегатах, делая её более понятной и защищённой.
- **Четко определить границы согласованности** с помощью агрегатов.
- **Сделать архитектуру более гибкой** за счёт использования интерфейсов репозиториев.
- **Упростить тестирование**, так как бизнес-логика изолирована от инфраструктуры.

В следующей главе мы рассмотрим, как TDD может направлять этот процесс рефакторинга и внедрения новых паттернов.
