# Анализ проекта iXe через призму "Паттерны разработки на Python - TDD, DDD и событийно-ориентированная архитектура"

## 1. Общая оценка соответствия принципам

### 1.1. Domain-Driven Design (DDD)
- **Положительно**:
  - Четко определен доменный слой в `domain/` с моделями (`problem_schema.py`, `answer_schema.py`), сервисами и интерфейсами адаптеров.
  - Используется инверсия зависимостей: интерфейсы адаптеров (`IExternalChecker`, `IDatabaseProvider`) определены в доменном слое, а реализации находятся в инфраструктуре.
  - Присутствуют Value Objects (например, `Problem` в `problem_schema.py`).
  - Используется слой приложений (`application/services/`) для координации.

- **Проблемы**:
  - Сущности домена (`Problem`) не содержат богатой бизнес-логики (инварианты, поведение), в основном это DTO.
  - Не до конца выдержаны границы агрегатов. Всё сваливается в один агрегат `Problem`.
  - Нет явных репозиториев в доменном слое (интерфейс `IDatabaseProvider` слишком общий).
  - Архитектура скрапинга (`scraper/fipi_scraper.py`) нарушает DDD, содержит "комок грязи" и смешивает уровни.

### 1.2. Test-Driven Development (TDD)
- **Положительно**:
  - В проекте есть папка `tests/`, что указывает на наличие тестов.
  - В `memory` упоминается, что пользователь "focused on ensuring testability".

- **Проблемы**:
  - Нет информации о содержимом `tests/` в предоставленных данных.
  - Нет явного следования циклу Red-Green-Refactor.
  - Сложная логика в скрапере и адаптерах может быть трудно тестируемой без изоляции зависимостей.

### 1.3. Событийно-ориентированная архитектура (Event-Driven Architecture)
- **Положительно**:
  - В ADR #1 планируется полиглотная персистентность, что поддерживает разные модели данных, включая события.
  - В `unified_backlog_with_analysis.md` упоминается агрегат `UserInteractionEvent`.

- **Проблемы**:
  - В текущем состоянии проекта нет явной обработки событий или шины событий.
  - Взаимодействия между сервисами (например, сохранение прогресса при проверке ответа) происходят напрямую, синхронно.

## 2. Что полезного из книги можно применить немедленно

### 2.1. Улучшения в стиле DDD

#### 2.1.1. Укрепить доменные сущности
- **Сейчас**: `Problem` в `domain/models/problem_schema.py` - это Pydantic модель, в основном DTO.
- **Применить**: Добавить в `Problem` методы, проверяющие инварианты и содержащие бизнес-логику.
  ```python
  # В domain/models/problem_schema.py
  class Problem:
      # ... существующие поля ...
      
      def is_answer_type_valid(self, answer: str) -> bool:
          """Проверяет, соответствует ли тип ответа ожидаемому для этой задачи."""
          # Логика проверки типа ответа (например, число, строка, выбор)
          pass

      def calculate_score(self, user_answer: str) -> int:
          """Вычисляет балл за ответ, если задача поддерживает автоматическую проверку."""
          # Логика вычисления балла
          pass
  ```

#### 2.1.2. Ввести явные репозитории в доменном слое
- **Сейчас**: `IDatabaseProvider` в `domain/interfaces/infrastructure_adapters.py` слишком общий.
- **Применить**: Определить конкретные интерфейсы репозиториев в доменном слое.
  ```python
  # В domain/interfaces/repositories.py (новый файл)
  from abc import abstractmethod
  from typing import Protocol, List, Optional
  from domain.models.problem_schema import Problem

  class IProblemRepository(Protocol):
      @abstractmethod
      async def save(self, problem: Problem) -> None: ...
      
      @abstractmethod
      async def get_by_id(self, problem_id: str) -> Optional[Problem]: ...
      
      @abstractmethod
      async def get_by_subject(self, subject: str) -> List[Problem]: ...
      
      # и т.д.
  ```

#### 2.1.3. Определить агрегаты и границы согласованности
- **Применить**: Явно выделить агрегаты (уже частично сделано в `unified_backlog_with_analysis.md`). Убедиться, что операции изменения касаются только одного агрегата за раз. Например, при проверке ответа (`AnswerService`) не обновлять `Problem` напрямую, а только `UserProgress`.

### 2.2. Улучшения в стиле TDD

#### 2.2.1. Начать с тестирования новых компонентов по TDD
- **Применить**: При реализации новых адаптеров для полиглотной персистентности (например, `ArangoDocumentAdapter`) начинать с написания тестов.
  ```python
  # tests/unit/test_arango_document_adapter.py (новый файл)
  import pytest
  from unittest.mock import AsyncMock, Mock
  from domain.models.problem_schema import Problem
  from infrastructure.adapters.arango_document_adapter import ArangoDocumentAdapter

  @pytest.mark.asyncio
  async def test_save_problem_calls_arango_client_correctly():
      # Arrange
      mock_arango_client = AsyncMock()
      adapter = ArangoDocumentAdapter(mock_arango_client)
      problem = Problem(problem_id="test", text="test text", subject="math")
      
      # Act
      await adapter.save(problem)
      
      # Assert
      # Проверить, что mock_arango_client.collection.insert был вызван с правильными аргументами
      mock_arango_client.collection.insert.assert_called_once()
  ```

#### 2.2.2. Изолировать сложные зависимости в тестах
- **Применить**: Использовать моки для `BrowserManager`, `QdrantClient`, `ArangoDBClient` в юнит-тестах адаптеров и сервисов.

### 2.3. Улучшения в стиле Event-Driven Architecture

#### 2.3.1. Ввести простую систему событий
- **Применить**: Начать с простого `EventPublisher` и `EventHandler`.
  ```python
  # domain/events.py (новый файл)
  from dataclasses import dataclass
  from typing import Any, Dict

  @dataclass
  class DomainEvent:
      event_type: str
       Dict[str, Any]

  @dataclass
  class AnswerCheckedEvent(DomainEvent):
      user_id: str
      problem_id: str
      is_correct: bool
      timestamp: str

  # domain/event_publisher.py (новый файл)
  from typing import Callable, Dict, List
  from .events import DomainEvent

  class EventPublisher:
      _handlers: Dict[str, List[Callable]] = {}

      @classmethod
      def subscribe(cls, event_type: str, handler: Callable):
          if event_type not in cls._handlers:
              cls._handlers[event_type] = []
          cls._handlers[event_type].append(handler)

      @classmethod
      async def publish(cls, event: DomainEvent):
          handlers = cls._handlers.get(event.event_type, [])
          for handler in handlers:
              await handler(event)
  ```

- **Интегрировать в существующие сервисы**:
  ```python
  # services/answer_service.py (обновленный)
  from domain.events import AnswerCheckedEvent, EventPublisher

  class AnswerService:
      # ... существующий код ...
      
      async def _generate_feedback(self, problem_id, is_correct, ...):
          # ... существующая логика ...
          
          # Опубликовать событие
          event = AnswerCheckedEvent(
              user_id="...", # получить из контекста
              problem_id=problem_id,
              is_correct=is_correct,
              timestamp="..." # получить текущее время
          )
          await EventPublisher.publish(event)
  ```

#### 2.3.2. Подготовить агрегаты для событийной архитектуры
- **Применить**: В `UserProgress` агрегате (в доменном слое) определить методы, которые будут генерировать события при изменении состояния.
  ```python
  # domain/models/user_progress.py (новый файл или обновление существующего)
  from dataclasses import dataclass
  from typing import List
  from domain.events import DomainEvent, AnswerCheckedEvent

  @dataclass
  class UserProgress:
      user_id: str
      problem_id: str
      status: str
      attempts: int = 0
      events: List[DomainEvent] = None # Список неподтвержденных событий
      
      def __post_init__(self):
          if self.events is None:
              self.events = []

      def record_attempt(self, is_correct: bool):
          self.attempts += 1
          if is_correct:
              self.status = "completed"
          else:
              self.status = "in_progress"
          
          # Генерируем событие
          event = AnswerCheckedEvent(user_id=self.user_id, problem_id=self.problem_id, is_correct=is_correct, timestamp="...")
          self.events.append(event)
  ```

## 3. Выводы и рекомендации

1. **DDD**: Проект уже имеет хорошую основу для DDD. Необходимо усилить бизнес-логику в доменных сущностях и явно выделить репозитории. Это улучшит тестируемость и поддержку кода.
2. **TDD**: Начать применять TDD при разработке новых компонентов, особенно при миграции на новую архитектуру хранения. Это повысит уверенность в корректности изменений.
3. **Event-Driven**: Внедрение простой системы событий может улучшить слабую связанность между компонентами. Например, обновление прогресса может быть реактивным на событие `AnswerCheckedEvent`, а не синхронным вызовом из `AnswerService`.

**Приоритетные действия**:
1. Ввести интерфейсы репозиториев в доменном слое (2.1.2).
2. Начать писать тесты для новых адаптеров (2.2.1).
3. Реализовать простой `EventPublisher` и использовать его в `AnswerService` (2.3.1).
4. Укрепить `Problem` сущность (2.1.1) как пример богатой доменной модели.
