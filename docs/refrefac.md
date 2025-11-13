Да, конечно. Учитывая проведённую разведку (выводы из `git log`, `git diff`, анализа `pytest` и т.д.), можно уточнить и улучшить формулировки задач, сделав их ещё более точными и контекстно-насыщенными. Вот обновлённый набор атомарных задач:

**Задача 1: Уточнение архитектурных изменений и зависимостей**

1.  **Команды терминала:**
    ```bash
    git log --oneline -10
    git diff HEAD~5 HEAD --name-only | grep -E "\.(py)$" | sort | uniq -c | head -20 # Показать файлы с наибольшим количеством изменений
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    На основе предоставленного лога Git и списка часто изменяемых файлов, уточни основные архитектурные изменения: 1) Введение Clean Architecture (слои domain, application, infrastructure). 2) Введение интерфейсов в domain (например, IDatabaseProvider, IHTMLProcessor, IProblemRepository). 3) Реализация этих интерфейсов адаптерами в infrastructure. 4) Введение application сервисов (например, PageScrapingService). 5) Изменение структуры моделей (Pydantic -> DDD entities). 6) Переход на асинхронность (async/await). Какие зависимости между слоями теперь считаются допустимыми, а какие - нарушением архитектуры (например, application не должен напрямую зависеть от infrastructure)?
    ```

**Задача 2: Анализ и фикс `DatabaseAdapter` и связанных тестов**

1.  **Команды терминала:**
    ```bash
    grep -n "save_answer_status\|get_all_subjects\|get_random_problem_ids" infrastructure/adapters/database_adapter.py domain/interfaces/infrastructure_adapters.py
    cat domain/models/database_models.py | grep -A 10 -B 10 "class DBAnswer"
    cat tests/test_utils_database_manager.py | head -20
    cat tests/utils/test_database_manager.py | head -20
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Проверь, реализованы ли *все* абстрактные методы из `IDatabaseProvider` (`save_answer_status`, `get_all_subjects`, `get_random_problem_ids`) в `DatabaseAdapter`. Убедись, что модель `DBAnswer` содержит поля `is_correct` и `score`, если `save_answer_status` их использует. Определи, какие методы `DatabaseAdapter` теперь асинхронные (async), а какие синхронные (legacy). Обнови тесты `tests/test_utils_database_manager.py` и `tests/utils/test_database_manager.py`, чтобы они вызывали правильные (синхронные) методы и учитывали изменения в структуре `DBAnswer` и `DomainProblem`. Предложи конкретный код для фикса тестов, если они вызывают асинхронные методы как синхронные или наоборот.
    ```

**Задача 3: Фикс `RecursionError` в API и зависимостях**

1.  **Команды терминала:**
    ```bash
    pytest tests/api/test_subjects.py::test_get_available_subjects_success -v --tb=long 2>&1 | grep -A 20 -B 5 "RecursionError\|maximum recursion" # Конкретный трейсбек
    cat api/endpoints/subjects.py
    cat api/dependencies.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    На основе предоставленного трейсбека RecursionError и кода эндпоинта `/subjects` и `dependencies.py`, найди причину бесконечной рекурсии. Возможно, это связано с циклической сериализацией FastAPI при возврате списка строк из `db_manager.get_all_subjects()` или с неправильной настройкой зависимостей (например, циклическая инъекция). Предложи конкретное исправление в `api/endpoints/subjects.py` или `api/dependencies.py`, которое устранит рекурсию.
    ```

**Задача 4: Обновление тестов `BrowserPoolManager`**

1.  **Команды термаала:**
    ```bash
    cat resource_management/browser_pool_manager.py
    cat tests/test_browser_pool_manager.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Сравни новую реализацию `BrowserPoolManager` (использующую `BrowserResourcePool`) с тестами `tests/test_browser_pool_manager.py`. Тесты ожидают внутренние атрибуты `_browsers` и `_queue`, которых больше нет. Перепиши тесты, используя публичный интерфейс `BrowserPoolManager`: `async def get_available_browser()`, `async def return_browser(browser)`, `async def get_stats()`, `async def close_all()`. Предложи конкретный обновлённый код для `tests/test_browser_pool_manager.py`.
    ```

**Задача 5: Исправление тестов `ProblemBuilder` и `Problem`**

1.  **Команды терминала:**
    ```bash
    cat domain/models/problem_schema.py
    cat domain/models/problem_builder.py
    cat tests/test_models_problem_builder.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Сравни сигнатуру `ProblemBuilder.build` с полями `Problem` из `problem_schema.py`. Тесты `tests/test_models_problem_builder.py` передают аргументы, не соответствующие новой схеме (например, возможно `difficulty` вместо `difficulty_level`, `topics` вместо `kes_codes`). Определи конкретные несоответствия, вызывающие `TypeError`. Предложи обновлённый код тестов, передающий аргументы, соответствующие полям `Problem` из `problem_schema.py`.
    ```

**Задача 6: Исправление тестов `HTMLMetadataExtractorAdapter`**

1.  **Команды терминала:**
    ```bash
    cat infrastructure/adapters/html_metadata_extractor_adapter.py
    cat tests/infrastructure/adapters/test_html_metadata_extractor_adapter.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Тесты `tests/infrastructure/adapters/test_html_metadata_extractor_adapter.py` вызывают метод `extract`, которого больше нет в `HTMLMetadataExtractorAdapter`. Метод был переименован в `extract_metadata_from_header`. Обнови тесты, заменив вызовы `adapter.extract` на `adapter.extract_metadata_from_header`. Предложи конкретный обновлённый код для тестов.
    ```

**Задача 7: Исправление `NameError` в `test_metadata_enhancer`**

1.  **Команды терминала:**
    ```bash
    cat domain/services/metadata_enhancer.py
    cat tests/unit/domain/test_metadata_enhancer.py
    cat infrastructure/adapters/specification_adapter.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    В тесте `tests/unit/domain/test_metadata_enhancer.py` происходит `NameError` для `SpecificationAdapter`. Это связано с тем, что `SpecificationAdapter` был перемещён из `services` в `infrastructure.adapters`. Обнови импорт в тестовом файле: `from infrastructure.adapters.specification_adapter import SpecificationAdapter`. Предложи конкретный исправленный импорт.
    ```

**Задача 8: Обновление архитектурных тестов**

1.  **Команды терминала:**
    ```bash
    cat tests/architecture/test_layer_dependencies.py
    find application/ -name "*.py" -exec grep -l "infrastructure" {} \; # Найти возможные нарушения
    find infrastructure/ -name "*.py" -exec grep -l "application" {} \;
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Архитектурные тесты, такие как `test_layer_dependencies`, проверяют, что слои не нарушают зависимости (например, application не должен импортировать из infrastructure). Проверь, нарушаются ли такие правила (например, `PageScrapingService` импортирует `DatabaseAdapter`). Если нарушения обнаружены, перепиши тесты, чтобы они проверяли зависимости через интерфейсы (например, `PageScrapingService` зависит от `IDatabaseProvider`, а не от `DatabaseAdapter`). Предложи обновлённый код для архитектурных тестов.
    ```

**Задача 9: Обновление тестов `QdrantRetrieverAdapter`**

1.  **Команды терминала:**
    ```bash
    cat infrastructure/adapters/qdrant_retriever_adapter.py
    cat tests/test_retriever.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    Тесты `tests/test_retriever.py` мокают `DatabaseAdapter` напрямую. После введения интерфейса `IDatabaseProvider`, тесты должны мокать интерфейс, а не конкретную реализацию. Обнови тесты, чтобы они мокали `IDatabaseProvider` и проверяли, что `QdrantRetrieverAdapter` вызывает методы этого интерфейса (например, `get_problems_by_ids`). Предложи конкретный обновлённый код для тестов.
    ```

**Задача 10: Обновление тестов асинхронных HTML-процессоров**

1.  **Команды терминала:**
    ```bash
    cat processors/html/image_processor.py
    cat processors/html/file_link_processor.py
    cat tests/test_processors_html_data.py
    ```
2.  **Плейсхолдер для контекста:** (Вставь сюда вывод команд выше)
3.  **Запрос к LLM:** ```
    HTML-процессоры (`ImageScriptProcessor`, `FileLinkProcessor`, и др.) теперь имеют асинхронный метод `process`. Тесты `tests/test_processors_html_data.py` вызывают их синхронно. Обнови тесты, чтобы они вызывали `await processor.process(...)` и правильно передавали параметры в `context`. Исправь `TypeError` связанные с неправильной распаковкой корутин. Предложи конкретный обновлённый код для тестов.
    ```
