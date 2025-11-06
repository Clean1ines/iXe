### **Задача 2. Обновить `Dockerfile` для `web-api-service` с новыми зависимостями**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий Dockerfile
cat Dockerfile
# Вывести .dockerignore
cat .dockerignore
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `Dockerfile` и `.dockerignore`)

**3. Само задание:**

**Цель:** Обновить `Dockerfile` для `web-api-service`, чтобы он использовал `requirements_web.txt`, включал `pip cache purge` и применял многоступенчатую сборку.
**Действия:**
- В `Dockerfile`:
    - Заменить `COPY requirements.txt .` на `COPY requirements_web.txt requirements.txt .` перед `RUN pip install ...`.
    - Убедиться, что используется многоступенчатая сборка (две или более директивы `FROM`).
    - Добавить `RUN pip cache purge` *после* `RUN pip install --no-cache-dir -r requirements.txt` в `builder` стадии.
    - Убедиться, что `RUN playwright install chromium` *отсутствует* в `runtime` стадии для веб-API Dockerfile.
- В `.dockerignore`:
    - Убедиться, что `venv/`, `.git/`, `tests/`, `frontend/node_modules/`, `__pycache__/`, `.pytest_cache/`, `.vscode/`, `.idea/`, `*.log`, `*.tmp`, `*.swp`, `data/`, `docs/` включены.
**Acceptance:**
- `Dockerfile` использует `requirements_web.txt`.
- `Dockerfile` включает `pip cache purge`.
- `Dockerfile` использует многоступенчатую сборку.
- `playwright install` отсутствует в `runtime` стадии `Dockerfile` для веб-API.

---

(Уточнение к Задаче 2): Обновление Dockerfile веб-API.
Задача 2 (обновленная): Обновить Dockerfile для web-api-service, чтобы он использовал requirements_web.txt и включал pip cache purge.
Зависит от: Задача 1.1 (создания requirements_web.txt).
Предназначение: Подготовить веб-API к деплою без тяжелых зависимостей.### **Задача 3. Создать `scraper-service` (Render Private Service)**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий скрипт скрапинга
cat scripts/scrape_tasks.py
# Вывести связанные утилиты
cat scraper/fipi_scraper.py
cat utils/browser_manager.py # (если используется в скрапере)
cat utils/browser_pool_manager.py # (если используется в скрапере)
# Вывести текущий DatabaseManager (для понимания, как он будет обновлен для Supabase)
cat utils/database_manager.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `scripts/scrape_tasks.py`, `scraper/fipi_scraper.py`, `utils/browser_manager.py`, `utils/browser_pool_manager.py`, `utils/database_manager.py`)

**3. Само задание:**

**Цель:** Вынести логику скрапинга в отдельный сервис, изолировав `playwright` и обновляя задачи в Supabase.
**Действия:**
- Создать новый репозиторий/папку `scraper-service`.
- Скопировать `scripts/scrape_tasks.py`, `scraper/fipi_scraper.py`, `utils/browser_manager.py`, `utils/browser_pool_manager.py`.
- Обновить `scripts/scrape_tasks.py` и `scraper/fipi_scraper.py`, чтобы они использовали *новую версию* `DatabaseManager`, подключающуюся к **Supabase**.
- Создать `requirements_scraping.txt` (с `playwright`, `beautifulsoup4`, `lxml`, `aiofiles`, `sqlalchemy`, `asyncpg`, `pydantic`, `python-dotenv`).
- Создать `Dockerfile.scraping` с установкой `playwright install`, копированием *только* файлов скрапера.
- Создать `api/app.py` (FastAPI) с эндпоинтом `POST /scrape/{subject}` для запуска скрапинга.
- *Опционально:* Добавить логику для вызова `indexer-service` после успешного скрапинга и загрузки в Supabase.
**Acceptance:**
- `scraper-service` развернут как Render Private Service.
- Он может скрапить задачи и сохранять их в Supabase.
- `playwright` изолирован от `web-api-service`.

---
### **Задача 4. Создать `indexer-service` (Render Private Service)**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий скрипт индексации
cat scripts/index_problems.py
# Вывести QdrantProblemIndexer
cat utils/vector_indexer.py
# Вывести QdrantProblemRetriever (для понимания модели задачи)
cat utils/retriever.py
# Вывести модели
cat models/database_models.py
cat models/pydantic_models.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `scripts/index_problems.py`, `utils/vector_indexer.py`, `utils/retriever.py`, `models/database_models.py`, `models/pydantic_models.py`)

**3. Само задание:**

**Цель:** Вынести логику индексации задач в Qdrant в отдельный сервис, читающий задачи из Supabase.
**Действия:**
- Создать новый репозиторий/папку `indexer-service`.
- Скопировать `scripts/index_problems.py`, `utils/vector_indexer.py`.
- Обновить `scripts/index_problems.py` и `utils/vector_indexer.py`, чтобы они подключались к **Supabase** (для чтения задач) и **Qdrant** (для записи векторов).
- Создать `requirements_indexing.txt` (с `qdrant-client`, `sqlalchemy`, `asyncpg`, `pydantic`, `python-dotenv`).
- Создать `Dockerfile.indexer`.
- Создать `api/app.py` (FastAPI) с эндпоинтом `POST /index` для запуска индексации.
- *Опционально:* Добавить фоновую задачу/триггер для автоматической индексации при обновлении задач в Supabase.
**Acceptance:**
- `indexer-service` развернут как Render Private Service.
- Он может читать задачи из Supabase и индексировать их в Qdrant.
- `qdrant-client` изолирован от `web-api-service`.

---

(Уточнение к Задаче 4): Создать indexer-service.
Задача 4: Вынести индексацию в отдельный сервис.
Создать репозиторий/папку indexer-service.
Копировать/адаптировать файлы (index_problems.py, vector_indexer.py).
Создать requirements_indexing.txt, Dockerfile.indexer.
Обновить indexer-service для подключения к Supabase (чтение) и Qdrant (запись).
Результат: Сервис, изолированный от web-api-service, с qdrant-client.### **Задача 5. Создать `database_manager.py` для работы с Supabase PostgreSQL**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий DatabaseManager
cat utils/database_manager.py
# Вывести модели базы данных
cat models/database_models.py
# Вывести модели Pydantic
cat models/pydantic_models.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `utils/database_manager.py`, `models/database_models.py`, `models/pydantic_models.py`)

**3. Само задание:**

**Цель:** Создать обновленный `database_manager.py`, который подключается к Supabase PostgreSQL и реализует CRUD операции для пользовательских данных (пользователи, ответы, статусы задач, сессии викторин, граф навыков).
**Действия:**
- Создать новый файл `database/database_manager.py`.
- Использовать `sqlalchemy` с драйвером `asyncpg` для подключения к PostgreSQL.
- Определить строки подключения через переменные окружения (например, `SUPABASE_DATABASE_URL`).
- Реализовать методы:
    - `get_user(self, user_id: int) -> UserSchema`
    - `create_user(self, email: str) -> UserSchema`
    - `save_answer(self, user_id: int, problem_id: str, user_answer: str, is_correct: bool) -> None`
    - `get_answer_and_status(self, user_id: int, problem_id: str) -> Optional[AnswerSchema]`
    - `update_task_status(self, user_id: int, problem_id: str, status: str) -> None` (например, "seen", "solved_correctly", "solved_incorrectly")
    - `get_quiz_session(self, session_id: str) -> Optional[QuizSessionSchema]`
    - `create_quiz_session(self, user_id: int, subject: str) -> str` (возвращает ID сессии)
    - `update_quiz_session(self, session_id: str, current_state: dict) -> None`
    - `get_user_skill_graph(self, user_id: int) -> dict` (или соответствующая схема)
    - `update_user_skill_graph(self, user_id: int, new_knowledge_state: dict) -> None`
- Использовать существующие Pydantic-модели (возможно, с небольшими адаптациями) для валидации данных.
- Обеспечить корректное управление сессиями SQLAlchemy (`AsyncSession`).
- (Опционально) Добавить логирование ошибок подключения/операций.
**Acceptance:**
- Файл `database/database_manager.py` создан.
- Он подключается к PostgreSQL (Supabase).
- Реализованы методы для CRUD пользовательских данных.
- Используются Pydantic-модели для валидации.

---
### **Задача 13. Создать `search-service` (Render Private Service) (если не используется прямое подключение к Qdrant)**

**1. Команды терминала для получения контекста:**

```bash
# Вывести QdrantProblemRetriever
cat utils/retriever.py
# Вывести модели
cat models/pydantic_models.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `utils/retriever.py`, `models/pydantic_models.py`)

**3. Само задание:**

**Цель:** Вынести логику поиска похожих задач в отдельный сервис, изолировав `qdrant-client`.
**Действия:**
- Создать новый репозиторий/папку `search-service`.
- Скопировать `utils/retriever.py` (только `QdrantProblemRetriever` и зависимости).
- Обновить `utils/retriever.py`, чтобы он подключался к **Qdrant**.
- Создать `requirements_search.txt` (с `fastapi`, `uvicorn`, `qdrant-client`, `pydantic`, `python-dotenv`).
- Создать `Dockerfile.search`.
- Создать `api/app.py` с эндпоинтом `POST /search/similar` для поиска.
**Acceptance:**
- `search-service` развернут как Render Private Service.
- Он может принимать запросы и возвращать похожие задачи из Qdrant.
- `qdrant-client` изолирован от `web-api-service`.

---

(Уточнение к Задаче 13): Создать search-service (опционально, но рекомендуется).
Задача 13: Вынести поиск похожих задач в отдельный сервис.
Создать репозиторий/папку search-service.
Копировать/адаптировать файлы (retriever.py - только QdrantProblemRetriever).
Создать requirements_search.txt, Dockerfile.search.
Создать FastAPI-приложение с эндпоинтом /search/similar.
Результат: Сервис, изолированный от web-api-service, с qdrant-client.
### **Задача 7. Создать `clients/checker_client.py` для взаимодействия с `checker-service`**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий AnswerChecker
cat utils/answer_checker.py
# Вывести схемы API, связанные с ответами
grep -A 10 -B 10 "CheckAnswer" models/schemas.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `utils/answer_checker.py` и *релевантные части* `models/schemas.py`)

**3. Само задание:**

**Цель:** Создать HTTP-клиент для вызова `checker-service` из `web-api-service`.
**Действия:**
- Создать новый файл `clients/checker_client.py`.
- Использовать `httpx.AsyncClient`.
- Определить URL `CHECKER_SERVICE_URL` через переменную окружения.
- Реализовать асинхронный метод `async def check_answer(self, task_id: str, user_answer: str, subject: str) -> dict` (или возвращаемый тип, соответствующий `CheckAnswerResponse`).
- Внутри метода выполнить `POST` запрос к `f"{CHECKER_SERVICE_URL}/check_answer"` с телом `{"task_id": task_id, "user_answer": user_answer, "subject": subject}`.
- Обработать возможные HTTP-ошибки (например, `500`, `400`) и вернуть соответствующую ошибку или `None`.
- (Опционально) Добавить таймауты для запросов.
**Acceptance:**
- Файл `clients/checker_client.py` создан.
- Содержит асинхронный метод `check_answer`.
- Метод корректно формирует и отправляет HTTP-запрос к `checker-service`.
- Обрабатываются ошибки.

### **Задача 9. Создать `clients/search_client.py` для взаимодействия с `search-service` (или Qdrant)**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий QdrantProblemRetriever
cat utils/retriever.py
# Вывести схемы, связанные с задачами
grep -A 5 -B 5 "Problem" models/pydantic_models.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `utils/retriever.py` и *релевантные части* `models/pydantic_models.py`)

**3. Само задание:**

**Цель:** Создать HTTP-клиент для вызова `search-service` (или прямого взаимодействия с Qdrant из `web-api-service`, если `search-service` не выносится).
**Действия:**
- Создать новый файл `clients/search_client.py`.
- Использовать `httpx.AsyncClient`.
- Определить URL `SEARCH_SERVICE_URL` или `QDRANT_URL` через переменную окружения.
- Реализовать асинхронный метод `async def retrieve_similar_problems(self, problem_id: str, limit: int = 5) -> List[ProblemSchema]` (или `List[str]` для ID).
- Внутри метода выполнить `POST` запрос к `f"{SEARCH_SERVICE_URL}/search/similar"` (или соответствующему эндпоинту Qdrant, например, `f"{QDRANT_URL}/collections/{collection_name}/points/search`) с телом, содержащим `problem_id` и `limit`.
- Обработать ответ и преобразовать его в список Pydantic-моделей `ProblemSchema` (или ID).
- Обработать возможные HTTP-ошибки.
- (Опционально) Добавить таймауты.
**Acceptance:**
- Файл `clients/search_client.py` создан.
- Содержит асинхронный метод `retrieve_similar_problems`.
- Метод корректно формирует и отправляет HTTP-запрос к `search-service` или Qdrant.
- Возвращается список задач (или их ID).

---

(Уточнение к Задаче 8): Создать clients/search_client.py.
Задача 8: Создать HTTP-клиент для search-service (или Qdrant).
Результат: Клиент для вызова search-service или Qdrant напрямую.
### **Задача 10. Обновить `services/answer_service.py` для использования `checker_client` и `DatabaseManager`**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий AnswerService
cat services/answer_service.py
# Вывести обновленный DatabaseManager (если уже создан)
cat database/database_manager.py 2>/dev/null || echo "Файл database/database_manager.py пока не создан"
# Вывести checker_client (если уже создан)
cat clients/checker_client.py 2>/dev/null || echo "Файл clients/checker_client.py пока не создан"
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `services/answer_service.py`, и *результаты* `cat` для `database_manager.py` и `checker_client.py`)

**3. Само задание:**

**Цель:** Обновить `AnswerService`, чтобы он использовал `checker_client` для проверки ответов и `DatabaseManager` (для Supabase) для сохранения результатов.
**Действия:**
- Импортировать `checker_client` и `database_manager`.
- В `AnswerService.__init__`, принять экземпляры `checker_client` и `database_manager` как зависимости.
- В методе `check_answer`:
    - Вызвать `await self.checker_client.check_answer(...)`.
    - Обработать результат (или ошибку) от `checker_client`.
    - Сохранить результат (ответ, правильность) в Supabase через `await self.database_manager.save_answer(...)`.
    - Обновить статус задачи в Supabase через `await self.database_manager.update_task_status(...)`.
    - Сформировать и вернуть `CheckAnswerResponse` на основе данных из `checker_client` и БД.
- Убедиться, что все вызовы `await` корректны.
**Acceptance:**
- `AnswerService` принимает `checker_client` и `database_manager` в `__init__`.
- Метод `check_answer` использует `checker_client` для проверки.
- Метод `check_answer` использует `database_manager` для сохранения результата и обновления статуса.
- Возвращается корректный `CheckAnswerResponse`.

---

Зависит от: Задач 8, 7.

---### **Задача 13. Обновить `api/endpoints/answer.py` для использования обновленного `AnswerService`**

**1. Команды терминала для получения контекста:**

```bash
# Вывести текущий эндпоинт ответа
cat api/endpoints/answer.py
# Вывести обновленный AnswerService (если уже обновлен)
cat services/answer_service.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `api/endpoints/answer.py` и *результаты* `cat services/answer_service.py`)

**3. Само задание:**

**Цель:** Обновить эндпоинт `/answer/check` в `api/endpoints/answer.py`, чтобы он использовал обновленный `AnswerService`.
**Действия:**
- Убедиться, что эндпоинт `POST /answer/check` принимает `CheckAnswerRequest`.
- Убедиться, что эндпоинт получает `AnswerService` через зависимость (`Depends(get_answer_service)`).
- Вызвать `await answer_service.check_answer(...)` с параметрами из запроса.
- Вернуть результат `answer_service.check_answer`, который должен соответствовать `CheckAnswerResponse`.
- Убедиться, что эндпоинт корректно обрабатывает ошибки от `AnswerService`.
**Acceptance:**
- Эндпоинт `POST /answer/check` использует обновленный `AnswerService`.
- Запрос и ответ соответствуют `CheckAnswerRequest` и `CheckAnswerResponse`.
- Результат проверки сохраняется в Supabase.

---### **Задача 15. Обновить `api/endpoints/block.py` для возврата JSON**

**1. Команды терминала для получения контекства:**

```bash
# Вывести текущий эндпоинт блока (предполагается, что он уже обновлен в предыдущих задачах)
cat api/endpoints/block.py
# Вывести обновленный DatabaseManager
cat database/database_manager.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `api/endpoints/block.py` и `database/database_manager.py`)

**3. Само задание:**

**Цель:** Убедиться, что эндпоинт `/problem/{problem_id}` возвращает задачу в формате JSON `ProblemResponse`.
**Действия:**
- Убедиться, что эндпоинт использует `DatabaseManager` (для Supabase) для получения задачи.
- Убедиться, что возвращается Pydantic-модель `ProblemResponse`.
- Убедиться, что `HTMLRenderer` (если он был) удален из этого пути.
**Acceptance:**
- `/problem/{problem_id}` возвращает JSON `ProblemResponse`.
- Задача читается из Supabase.

---
### **Задача 16. Реализовать `require_subscription` зависимость в `api/dependencies.py`**

**1. Команды тернала для получения контекста:**

```bash
# Вывести текущие зависимости
cat api/dependencies.py
# Вывести модели пользователей/подписки (если есть)
grep -A 10 -B 10 "User\|Subscription" models/pydantic_models.py
```

**2. Блок для вставки полученного контекста:**

(Пользователь вставляет содержимое `api/dependencies.py` и *релевантные части* `models/pydantic_models.py`)

**3. Само задание:**

**Цель:** Создать зависимость `require_subscription`, которая проверяет статус подписки пользователя перед доступом к основным функциям.
**Действия:**
- В `api/dependencies.py`:
    - Импортировать `HTTPException`, `status`.
    - Создать асинхронную зависимость `async def require_subscription(db: DatabaseManager = Depends(get_db_manager), user_id: int = Depends(get_current_user_id)) -> bool:` (предполагается, что `get_current_user_id` уже реализована).
    - Внутри `require_subscription`:
        - Получить статус подписки пользователя из Supabase через `db` (например, `subscription = await db.get_user_subscription_status(user_id)`).
        - Если `subscription.status != "active"`, вызвать `raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Subscription required")`.
        - Иначе, вернуть `True`.
- Применить `Depends(require_subscription)` к ключевым эндпоинтам в `api/endpoints/` (например, `start_quiz`, `check_answer`, `get_problem_data`).
**Acceptance:**
- Функция `require_subscription` существует в `api/dependencies.py`.
- Она проверяет статус подписки в Supabase.
- Эндпоинты, требующие подписки, защищены `Depends(require_subscription)`.
- При отсутствии активной подписки возвращается `402 Payment Required`.

Результат: /api/v1/subscribe, require_subscription зависимость.