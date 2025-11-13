
---

**Задача 6. Перемещение утилит с доменной логикой из utils/**

**1. Команды тернала для получения контекста:**
```bash
cat utils/element_pairer.py
cat utils/metadata_extractor.py
grep -r "ElementPairer\|MetadataExtractor" . --include="*.py" --exclude-dir=venv
find processors/ -name "*.py" -exec grep -l "ElementPairer\|MetadataExtractor" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/element_pairer.py
cat utils/metadata_extractor.py
grep -r "ElementPairer\|MetadataExtractor" . --include="*.py" --exclude-dir=venv
find processors/ -name "*.py" -exec grep -l "ElementPairer\|MetadataExtractor" {} \;

**3. Само задание:**

**Цель:** Переместить утилиты `ElementPairer` и `MetadataExtractor`, которые содержат логику, специфичную для обработки HTML задач ФИПИ, в соответствующий архитектурный уровень (возможно, инфраструктурный слой), чтобы улучшить структуру проекта.

**Действия:**
- Оценить логику в `utils/element_pairer.py` и `utils/metadata_extractor.py`. Определить, является ли она чисто инфраструктурной (работа с HTML/XML) или содержит элементы доменной логики.
- Если логика исключительно инфраструктурная, переместить файлы в `infrastructure/adapters/` (например, `infrastructure/adapters/html_pairer_adapter.py`, `infrastructure/adapters/html_metadata_extractor_adapter.py`).
- Если логика содержит доменные аспекты, рассмотреть, можно ли выделить ядро в доменные сервисы или упростить до инфраструктурной.
- Обновить все импорты и использования `ElementPairer` и `MetadataExtractor` в проекте (например, в `processors/page_processor.py`, `infrastructure/adapters/block_processor_adapter.py` или других местах) на новые пути.
- Убедиться, что функциональность обработки HTML не изменилась.

**Acceptance Criteria:**
- Файлы `element_pairer.py` и `metadata_extractor.py` перемещены из `utils/` в соответствующий уровень (предположительно `infrastructure/adapters/`).
- Все импорты в проекте обновлены и ссылаются на новые местоположения.
- Функциональность обработки HTML (например, парсинг, извлечение КЭС/КОС) работает корректно.
- Структура проекта отражает более точное размещение компонентов по архитектурным слоям.
- Все тесты, зависящие от этих компонентов, проходят успешно.

**Задача 7. Проверка и устранение циклических зависимостей**

**1. Команды терминала для получения контекста:**
```bash
pip install pydeps
pydeps . --show-deps --max-bacon 2 --pylib --exclude-exact pytest,fastapi,playwright,sqlalchemy,bs4,uvicorn,jinja2,requests,qdrant_client | grep -A 10 -B 10 "circular\|cycle"
find . -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -i "ImportError\|circular"
grep -r "from iXe" . --include="*.py" --exclude-dir=venv  # Проверить на относительные/абсолютные импорты
```

**2. Блок для вставки полученного контекста:**

pip install pydeps
pydeps . --show-deps --max-bacon 2 --pylib --exclude-exact pytest,fastapi,playwright,sqlalchemy,bs4,uvicorn,jinja2,requests,qdrant_client | grep -A 10 -B 10 "circular\|cycle"
find . -name "*.py" -exec python -m py_compile {} \; 2>&1 | grep -i "ImportError\|circular"
grep -r "from iXe" . --include="*.py" --exclude-dir=venv  # Проверить на относительные/абсолютные импорты

**3. Само задание:**

**Цель:** Провести анализ проекта на наличие циклических импортов и устранить все найденные нарушения архитектурных границ.

**Действия:**
- Использовать инструмент `pydeps` или аналогичный для анализа графа зависимостей проекта.
- Запустить проверку синтаксиса и импортов всех Python-файлов с помощью `python -m py_compile`.
- Вручную проанализировать вывод инструментов на предмет циклических зависимостей (например, A импортирует B, B импортирует A; или A импортирует B, B импортирует C, C импортирует A).
- Также проверить на наличие неправильных абсолютных импортов (типа `from iXe.some_module import ...` вместо относительных или корректных относительных).
- Устранить любые найденные циклы, возможно, через введение новых интерфейсов (портов) в доменном слое или перенос кода в более подходящий уровень архитектуры.
- Убедиться, что все импорты соответствуют структуре Clean Architecture (верхние уровни зависят от абстракций нижних, а не от их конкретных реализаций).

**Acceptance Criteria:**
- Инструменты анализа зависимостей (`pydeps`, `python -m py_compile`) не выявляют циклических импортов.
- Все импорты в проекте соответствуют структуре Clean Architecture (домен не зависит от инфраструктуры, приложение зависит от домена, инфраструктура зависит от домена и т.д.).
- Все тесты проекта проходят успешно после устранения циклов.

---

**Задача 8. Создание архитектурных тестов**

**1. Команды терминала для получения контекста:**
```bash
find tests/ -name "*architecture*" -o -name "*layer*" -o -name "*dependency*"
ls -la tests/
pip install pytest-archon archunitpy
cat << EOF > /tmp/test_example.py
from application.services.task_processing_service import TaskProcessingService
from domain.interfaces.task_inferer import ITaskNumberInferer
EOF
python -m pytest --collect-only /tmp/test_example.py 2>/dev/null || echo "pytest установлен"
```

**2. Блок для вставки полученного контекста:**

find tests/ -name "*architecture*" -o -name "*layer*" -o -name "*dependency*"
ls -la tests/
pip install pytest-archon archunitpy
cat << EOF > /tmp/test_example.py
from application.services.task_processing_service import TaskProcessingService
from domain.interfaces.task_inferer import ITaskNumberInferer
EOF
python -m pytest --collect-only /tmp/test_example.py 2>/dev/null || echo "pytest установлен"

**3. Само задание:**

**Цель:** Написать автоматизированные тесты, проверяющие соблюдение архитектурных принципов Clean Architecture, чтобы предотвратить регрессии в будущем.

**Действия:**
- Установить библиотеку для архитектурных тестов (например, `pytest-archon` или `archunitpy`).
- Создать директорию `tests/architecture/`.
- Написать тесты, проверяющие:
  - Что `domain/` не зависит от `application/`, `infrastructure/`, `services/`, `api/`, `utils/`.
  - Что `application/` зависит только от `domain/` и не зависит от `infrastructure/`, `api/`, `utils/` напрямую (только через интерфейсы).
  - Что `infrastructure/` зависит от `domain/` и может зависеть от внешних библиотек, но не от `api/`, `application/` напрямую (только через интерфейсы).
  - Что `api/` зависит от `application/`, `infrastructure/` и `domain/` (для моделей/интерфейсов), но не от `utils/` напрямую (только через `services/` или `infrastructure/` через DI).
  - Что инфраструктурные адаптеры (например, в `infrastructure/adapters/`) реализуют соответствующие доменные интерфейсы.
- Использовать возможности выбранной библиотеки для описания правил зависимостей (например, `assert that modules().that().reside_in_a_package('domain..') should().not_depend_on_modules_that().reside_in_a_package('infrastructure..')`).
- Интегрировать архитектурные тесты в основной набор тестов (`pytest`).

**Acceptance Criteria:**
- Существует директория `tests/architecture/`.
- Архитектурные тесты успешно проходят при запуске `pytest`.
- Тесты проверяют ключевые архитектурные границы, описанные в Clean Architecture.
- При попытке добавить код, нарушающий архитектурные правила (например, импорт из `domain/` в `infrastructure/`), соответствующие архитектурные тесты падают с ошибкой.

**Задача 11. Реализация интерфейса IProblemRetriever и IDatabaseProvider в доменном слое**

**1. Команды терминала для получения контекста:**
```bash
find domain/interfaces/ -name "*.py" -exec grep -l "ProblemRetriever\|DatabaseProvider" {} \;
cat utils/retriever.py | head -30
cat utils/database_manager.py | head -30
grep -r "QdrantProblemRetriever\|DatabaseManager" services/ --include="*.py"
```

**2. Блок для вставки полученного контекста:**

find domain/interfaces/ -name "*.py" -exec grep -l "ProblemRetriever\|DatabaseProvider" {} \;
cat utils/retriever.py | head -30
cat utils/database_manager.py | head -30
grep -r "QdrantProblemRetriever\|DatabaseManager" services/ --include="*.py"

**3. Само задание:**

**Цель:** Создать недостающие доменные интерфейсы `IProblemRetriever` и `IDatabaseProvider` для адаптеров `QdrantProblemRetriever` и `DatabaseManager`, чтобы завершить формализацию инфраструктурных зависимостей через интерфейсы в доменном слое.

**Действия:**
- Создать или обновить файл `domain/interfaces/infrastructure_adapters.py` (или создать отдельные файлы `domain/interfaces/problem_retriever.py` и `domain/interfaces/database_provider.py`).
- Определить интерфейс `IProblemRetriever` с методами, необходимыми для поиска задач (например, `retrieve_problems`, `retrieve_problem_by_id`).
- Определить интерфейс `IDatabaseProvider` с методами, необходимыми для взаимодействия с БД (например, `get_session`, `save_entity`, `query_entity`).
- Обновить `QdrantProblemRetriever` (в `utils/` или `infrastructure/adapters/` после задачи 5), чтобы он реализовывал `IProblemRetriever`.
- Обновить `DatabaseManager` (в `utils/` или `infrastructure/adapters/` после задачи 5), чтобы он реализовывал `IDatabaseProvider`.
- Обновить `QuizService` и `AnswerService`, чтобы они зависели от `IProblemRetriever` и `IDatabaseProvider` вместо конкретных классов.
- Обновить `api/dependencies.py`, чтобы внедрять нужные реализации через DI.

**Acceptance Criteria:**
- Интерфейсы `IProblemRetriever` и `IDatabaseProvider` существуют в `domain/interfaces/`.
- `QdrantProblemRetriever` реализует `IProblemRetriever`.
- `DatabaseManager` реализует `IDatabaseProvider`.
- `QuizService` и `AnswerService` зависят от интерфейсов, а не от конкретных классов.
- Все зависимости корректно инъецируются через `api/dependencies.py`.
- Все тесты проходят успешно.

---

**Задача 12. Создание и тестирование спецификаций для новых инфраструктурных адаптеров**

**1. Команды терминала для получения контекста:**
```bash
find tests/ -name "*test*answer_checker*" -o -name "*test*local_storage*" -o -name "*test*database_manager*" -o -name "*test*retriever*"
ls -la tests/infrastructure/
```

**2. Блок для вставки полученного контекста:**

find tests/ -name "*test*answer_checker*" -o -name "*test*local_storage*" -o -name "*test*database_manager*" -o -name "*test*retriever*"
ls -la tests/infrastructure/

**3. Само задание:**

**Цель:** Написать полные юнит- и интеграционные тесты для новых инфраструктурных адаптеров (`FIPIAnswerChecker`, `LocalStorage`, `DatabaseManager`, `QdrantProblemRetriever` после их формализации в задаче 5), чтобы обеспечить их надежность и корректную работу через интерфейсы.

**Действия:**
- Создать директорию `tests/infrastructure/adapters/`.
- Для каждого адаптера (`answer_checker_adapter`, `local_storage_adapter`, `database_adapter`, `qdrant_retriever_adapter`) создать отдельный файл тестов.
- Написать юнит-тесты, проверяющие логику каждого адаптера в изоляции, подставляя моки внешних зависимостей (например, мок Playwright для `FIPIAnswerChecker`, мок файловой системы для `LocalStorage`, мок Qdrant для `QdrantProblemRetriever`).
- Написать интеграционные тесты, проверяющие взаимодействие адаптеров с реальными внешними системами (если возможно в тестовой среде) или с тестовыми контейнерами (Docker).
- Убедиться, что тесты проверяют как успешные сценарии, так и обработку ошибок.
- Обновить `pytest.ini` или конфигурацию, чтобы тесты для `infrastructure/adapters` были включены в основной запуск.

**Acceptance Criteria:**
- Существует директория `tests/infrastructure/adapters/` с тестами для каждого адаптера.
- Юнит-тесты для адаптеров проходят успешно, используя моки.
- Интеграционные тесты для адаптеров проходят успешно (при доступности внешних систем или контейнеров).
- Покрытие тестами для адаптеров > 85%.
- Все тесты интегрируются в основной CI/CD pipeline.

**Задача 13. Создание интерфейса ITaskNumberInfererProvider и обновление TaskNumberInfererAdapter**

**1. Команды терминала для получения контекста:**
```bash
cat domain/interfaces/task_inferer.py
cat infrastructure/adapters/task_number_inferer_adapter.py
grep -r "TaskNumberInfererAdapter" application/ --include="*.py"
grep -r "ITaskNumberInferer" domain/interfaces/ --include="*.py"
```

**2. Блок для вставки полученного контекста:**

cat domain/interfaces/task_inferer.py
cat infrastructure/adapters/task_number_inferer_adapter.py
grep -r "TaskNumberInfererAdapter" application/ --include="*.py"
grep -r "ITaskNumberInferer" domain/interfaces/ --include="*.py"

**3. Само задание:**

**Цель:** Убедиться, что `TaskNumberInfererAdapter` формально реализует интерфейс `ITaskNumberInferer` и использовать его через DI в `TaskProcessingService`.

**Действия:**
- Проверить, что `TaskNumberInfererAdapter` в `infrastructure/adapters/task_number_inferer_adapter.py` наследуется от `ITaskNumberInferer` из `domain.interfaces.task_inferer`.
- Если наследования нет, добавить его: `class TaskNumberInfererAdapter(ITaskNumberInferer):`.
- Убедиться, что сигнатура метода `infer` в `TaskNumberInfererAdapter` соответствует интерфейсу.
- Обновить `TaskProcessingService` в `application/services/task_processing_service.py`, чтобы он принимал `task_inferer: ITaskNumberInferer` через конструктор.
- Обновить `api/dependencies.py`, чтобы внедрять `TaskNumberInfererAdapter` как реализацию `ITaskNumberInferer` в `TaskProcessingService`.

**Acceptance Criteria:**
- `TaskNumberInfererAdapter` наследуется от `ITaskNumberInferer`.
- `TaskProcessingService` зависит от интерфейса `ITaskNumberInferer`.
- DI в `api/dependencies.py` корректно связывает `ITaskNumberInferer` с `TaskNumberInfererAdapter`.
- Юнит-тесты для `TaskProcessingService` могут использовать мок `ITaskNumberInferer`.

---

**Задача 14. Создание интерфейса IAnswerTypeProvider и обновление AnswerTypeService**

**1. Команды терминала для получения контекста:**
```bash
cat domain/services/answer_type_detector.py
grep -r "AnswerTypeService" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "AnswerType" {} \;
```

**2. Блок для вставки полученного контекста:**

cat domain/services/answer_type_detector.py
grep -r "AnswerTypeService" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "AnswerType" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IAnswerTypeProvider` для `AnswerTypeService` и обновить зависимости, чтобы обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/answer_type_provider.py`.
- Определить интерфейс `IAnswerTypeProvider` с методом `detect_answer_type(self, html_content: str) -> str`.
- Обновить `AnswerTypeService` в `domain/services/answer_type_detector.py`, чтобы он реализовывал `IAnswerTypeProvider`: `class AnswerTypeService(IAnswerTypeProvider):`.
- Убедиться, что сигнатура метода `detect_answer_type` соответствует интерфейсу.
- Найти все места, где используется `AnswerTypeService` (например, в `infrastructure/adapters/block_processor_adapter.py`, `application/services/html_processing_service.py`).
- Обновить эти компоненты, чтобы они зависели от интерфейса `IAnswerTypeProvider` вместо конкретного класса `AnswerTypeService`.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `AnswerTypeService` как реализацию `IAnswerTypeProvider`.

**Acceptance Criteria:**
- Интерфейс `IAnswerTypeProvider` существует в `domain/interfaces/`.
- `AnswerTypeService` реализует `IAnswerTypeProvider`.
- Компоненты, использующие `AnswerTypeService`, зависят от интерфейса `IAnswerTypeProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 15. Создание интерфейса ISkillGraphProvider и обновление InMemorySkillGraph**

**1. Команды терминала для получения контекста:**
```bash
cat utils/skill_graph.py | head -30
grep -r "InMemorySkillGraph" services/ --include="*.py"
grep -r "InMemorySkillGraph" api/ --include="*.py"
find domain/interfaces/ -name "*.py" -exec grep -l "SkillGraph\|Skill" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/skill_graph.py | head -30
grep -r "InMemorySkillGraph" services/ --include="*.py"
grep -r "InMemorySkillGraph" api/ --include="*.py"
find domain/interfaces/ -name "*.py" -exec grep -l "SkillGraph\|Skill" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `ISkillGraphProvider` для `InMemorySkillGraph` и обновить зависимости `QuizService`, чтобы обеспечить соблюдение DIP и подготовить систему к возможной замене реализации графа навыков.

**Действия:**
- Создать файл `domain/interfaces/skill_graph_provider.py`.
- Определить интерфейс `ISkillGraphProvider` с методами, необходимыми для работы с графом навыков (например, `update_user_skills`, `get_next_task_recommendation`, `get_skill_status`).
- Обновить `InMemorySkillGraph` в `utils/skill_graph.py`, чтобы он реализовывал `ISkillGraphProvider`: `class InMemorySkillGraph(ISkillGraphProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Обновить `QuizService` в `services/quiz_service.py`, чтобы он принимал `skill_graph: ISkillGraphProvider` через конструктор вместо конкретного `InMemorySkillGraph`.
- Обновить `api/dependencies.py`, чтобы внедрять `InMemorySkillGraph` как реализацию `ISkillGraphProvider` в `QuizService`.
- Рассмотреть возможность перемещения `InMemorySkillGraph` из `utils/` в `infrastructure/adapters/skill_graph_adapter.py` (после задачи 6), если это логично с архитектурной точки зрения.

**Acceptance Criteria:**
- Интерфейс `ISkillGraphProvider` существует в `domain/interfaces/`.
- `InMemorySkillGraph` реализует `ISkillGraphProvider`.
- `QuizService` зависит от интерфейса `ISkillGraphProvider`.
- DI в `api/dependencies.py` корректно связывает `ISkillGraphProvider` с `InMemorySkillGraph` (или его новым местоположением).
- Все тесты, использующие `QuizService`, проходят успешно (возможно, с обновлением моков).

---

**Задача 16. Обновление PageProcessingOrchestrator для использования новых интерфейсов**

**1. Команды тернала для получения контекста:**
```bash
cat processors/page_processor.py  # после задачи 2
grep -r "AnswerTypeService\|MetadataExtractionService" processors/page_processor.py
```

**2. Блок для вставки полученного контекста:**

cat processors/page_processor.py  # после задачи 2
grep -r "AnswerTypeService\|MetadataExtractionService" processors/page_processor.py

**3. Само задание:**

**Цель:** Обновить `PageProcessingOrchestrator`, чтобы он использовал интерфейсы `IAnswerTypeProvider` и `ISpecificationProvider` (после задачи 4) вместо конкретных классов, тем самым полностью устранив нарушения DIP в этом компоненте.

**Действия:**
- После выполнения задач 4 и 14, обновить `PageProcessingOrchestrator` в `processors/page_processor.py`.
- Изменить конструктор, чтобы он принимал `answer_type_provider: IAnswerTypeProvider` и `specification_provider: ISpecificationProvider` вместо конкретных `AnswerTypeService` и `SpecificationService`.
- Обновить `api/dependencies.py` или место создания `PageProcessingOrchestrator`, чтобы передавать ему соответствующие реализации интерфейсов.
- Убедиться, что `PageProcessingOrchestrator` больше не импортирует конкретные реализации `AnswerTypeService` или `SpecificationService`.
- Вызвать методы через интерфейсы (например, `self.answer_type_provider.detect_answer_type(...)`).

**Acceptance Criteria:**
- `PageProcessingOrchestrator` принимает `IAnswerTypeProvider` и `ISpecificationProvider` через конструктор.
- `PageProcessingOrchestrator` не импортирует и не зависит от конкретных классов `AnswerTypeService` или `SpecificationService`.
- `PageProcessingOrchestrator` использует методы через интерфейсы.
- Все интеграционные и функциональные тесты, использующие `PageProcessingOrchestrator`, проходят успешно.
- DI в `api/dependencies.py` (или другом месте) корректно передает реализации интерфейсов.

**Задача 17. Создание интерфейса IBrowserResourceProvider и обновление BrowserManager**

**1. Команды терминала для получения контекста:**
```bash
cat resource_management/browser_manager.py | head -30
grep -r "BrowserManager\|IBrowserResource" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "BrowserManager\|BrowserResource" {} \;
```

**2. Блок для вставки полученного контекста:**

cat resource_management/browser_manager.py | head -30
grep -r "BrowserManager\|IBrowserResource" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "BrowserManager\|BrowserResource" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IBrowserResourceProvider` для `BrowserManager` и обновить зависимости компонентов, использующих браузер (например, `FIPIAnswerChecker`), чтобы обеспечить соблюдение DIP и улучшить тестируемость.

**Действия:**
- Создать файл `domain/interfaces/browser_resource_provider.py`.
- Определить интерфейс `IBrowserResourceProvider` с методами, необходимыми для управления браузерными ресурсами (например, `get_page_content`, `get_general_page`, `close`).
- Обновить `BrowserManager` в `resource_management/browser_manager.py`, чтобы он реализовывал `IBrowserResourceProvider`: `class BrowserManager(IBrowserResourceProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Обновить `FIPIAnswerChecker` в `utils/answer_checker.py` (или `infrastructure/adapters/answer_checker_adapter.py` после задачи 5), чтобы он принимал `browser_provider: IBrowserResourceProvider` через конструктор вместо конкретного `BrowserManager`.
- Обновить `api/dependencies.py`, чтобы внедрять `BrowserManager` как реализацию `IBrowserResourceProvider` в `FIPIAnswerChecker` (через DI-цепочку, возможно, через `get_answer_checker`).

**Acceptance Criteria:**
- Интерфейс `IBrowserResourceProvider` существует в `domain/interfaces/`.
- `BrowserManager` реализует `IBrowserResourceProvider`.
- `FIPIAnswerChecker` зависит от интерфейса `IBrowserResourceProvider`.
- DI в `api/dependencies.py` корректно связывает `IBrowserResourceProvider` с `BrowserManager`.
- Юнит-тесты для `FIPIAnswerChecker` могут использовать мок `IBrowserResourceProvider`.
- Все интеграционные тесты проходят успешно.

---

**Задача 18. Обновление FIPIScraper для использования новых интерфейсов**

**1. Команды терминала для получения контекста:**
```bash
cat scraper/fipi_scraper.py | head -40
grep -r "PageProcessingOrchestrator\|TaskNumberInfererAdapter" scraper/fipi_scraper.py
```

**2. Блок для вставки полученного контекста:**

cat scraper/fipi_scraper.py | head -40
grep -r "PageProcessingOrchestrator\|TaskNumberInfererAdapter" scraper/fipi_scraper.py

**3. Само задание:**

**Цель:** Обновить `FIPIScraper`, чтобы он использовал интерфейсы (например, `IHTMLProcessor` через `PageProcessingOrchestrator` после задачи 16, `ITaskNumberInfererProvider` через `PageProcessingOrchestrator`) вместо конкретных реализаций, улучшив архитектурное разделение.

**Действия:**
- После обновления `PageProcessingOrchestrator` (задача 16) и других зависимостей, обновить `FIPIScraper` в `scraper/fipi_scraper.py`.
- Убедиться, что зависимости, передаваемые в `PageProcessingOrchestrator` внутри `FIPIScraper`, соответствуют интерфейсам, а не конкретным классам.
- Это может включать передачу правильных реализаций `IHTMLProcessor`, `IAnswerTypeProvider`, `ISpecificationProvider` и т.д. через конструктор `PageProcessingOrchestrator`.
- Проверить, что `FIPIScraper` сам не нарушает DIP, используя конкретные реализации напрямую (вне `PageProcessingOrchestrator`).

**Acceptance Criteria:**
- `FIPIScraper` передает в `PageProcessingOrchestrator` зависимости, соответствующие интерфейсам.
- `FIPIScraper` не зависит напрямую от конкретных инфраструктурных реализаций (вне `PageProcessingOrchestrator`).
- Функциональность скрапинга сохраняется.
- Все интеграционные тесты, использующие `FIPIScraper`, проходят успешно.

**Задача 19. Создание интерфейса IAssetDownloaderProvider и обновление AssetDownloader**

**1. Команды терминала для получения контекста:**
```bash
cat utils/downloader.py | head -30
grep -r "AssetDownloader" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "AssetDownloader\|Downloader" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/downloader.py | head -30
grep -r "AssetDownloader" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "AssetDownloader\|Downloader" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IAssetDownloaderProvider` для `AssetDownloader` и обновить зависимости компонентов, использующих загрузку ассетов (например, `BlockProcessorAdapter`), чтобы обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/asset_downloader_provider.py`.
- Определить интерфейс `IAssetDownloaderProvider` с методами, необходимыми для скачивания файлов и изображений (например, `download_image`, `download_file`, `download_assets_from_html`).
- Обновить `AssetDownloader` в `utils/downloader.py`, чтобы он реализовывал `IAssetDownloaderProvider`: `class AssetDownloader(IAssetDownloaderProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти все компоненты, использующие `AssetDownloader` (например, в `infrastructure/adapters/block_processor_adapter.py`, `processors/page_processor.py`).
- Обновить эти компоненты, чтобы они принимали `asset_downloader: IAssetDownloaderProvider` через конструктор или методы, а не создавали `AssetDownloader` напрямую.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `AssetDownloader` как реализацию `IAssetDownloaderProvider`.

**Acceptance Criteria:**
- Интерфейс `IAssetDownloaderProvider` существует в `domain/interfaces/`.
- `AssetDownloader` реализует `IAssetDownloaderProvider`.
- Компоненты, использующие `AssetDownloader`, зависят от интерфейса `IAssetDownloaderProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 20. Обновление HTML-процессоров для реализации IHTMLProcessor**

**1. Команды тернала для получения контекста:**
```bash
find processors/html/ -name "*.py" -exec grep -l "class.*Processor" {} \;
cat processors/html/image_processor.py | head -20
grep -r "IHTMLProcessor" processors/html/ --include="*.py"
```

**2. Блок для вставки полученного контекста:**

find processors/html/ -name "*.py" -exec grep -l "class.*Processor" {} \;
cat processors/html/image_processor.py | head -20
grep -r "IHTMLProcessor" processors/html/ --include="*.py"

**3. Само задание:**

**Цель:** Убедиться, что все конкретные HTML-процессоры (например, `ImageScriptProcessor`, `FileLinkProcessor`, `TaskInfoProcessor` и т.д.) в `processors/html/` формально реализуют интерфейс `IHTMLProcessor`, определенный в доменном слое, и обновить их сигнатуры методов при необходимости.

**Действия:**
- Для каждого процессора в `processors/html/` (например, `image_processor.py`, `file_link_processor.py`, `task_info_processor.py`, `input_field_remover.py`, `mathml_remover.py`, `unwanted_element_remover.py`):
  - Убедиться, что он импортирует `IHTMLProcessor` из `domain.interfaces.html_processor`.
  - Убедиться, что он наследуется от `IHTMLProcessor`: `class ImageScriptProcessor(IHTMLProcessor):`.
  - Убедиться, что сигнатура его метода `process` (или `process_html_block`, в зависимости от интерфейса) соответствует `IHTMLProcessor`.
  - Если сигнатура отличается, обновить метод и соответствующие вызовы.
- Проверить, что `BlockProcessorAdapter` (или `PageProcessingOrchestrator` до задачи 2) корректно вызывает методы этих процессоров через интерфейс или использует их в соответствии с архитектурой (например, через pipeline).

**Acceptance Criteria:**
- Все HTML-процессоры в `processors/html/` наследуются от `IHTMLProcessor`.
- Сигнатуры методов процессоров соответствуют `IHTMLProcessor`.
- Все тесты, зависящие от HTML-процессоров, проходят успешно.
- Архитектурные тесты не выявляют нарушений зависимостей.

**Задача 21. Создание интерфейса IElementPairerProvider и обновление ElementPairer**

**1. Команды терминала для получения контекста:**
```bash
cat utils/element_pairer.py | head -30
grep -r "ElementPairer" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ElementPairer\|Pairer" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/element_pairer.py | head -30
grep -r "ElementPairer" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ElementPairer\|Pairer" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IElementPairerProvider` для `ElementPairer` и обновить зависимости компонентов, использующих парсер элементов (например, `PageProcessingOrchestrator` или `BlockProcessorAdapter` после задачи 6), чтобы обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/element_pairer_provider.py`.
- Определить интерфейс `IElementPairerProvider` с методом, необходимым для парсинга HTML элементов (например, `pair(self, soup: BeautifulSoup) -> List[Tuple[Tag, Tag]]`).
- Обновить `ElementPairer` в `utils/element_pairer.py` (или `infrastructure/adapters/` после задачи 6), чтобы он реализовывал `IElementPairerProvider`: `class ElementPairer(IElementPairerProvider):`.
- Убедиться, что сигнатура метода `pair` соответствует интерфейсу.
- Найти компонент, использующий `ElementPairer` (предположительно `PageProcessingOrchestrator` или `BlockProcessorAdapter`).
- Обновить этот компонент, чтобы он принимал `element_pairer: IElementPairerProvider` через конструктор.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `ElementPairer` как реализацию `IElementPairerProvider`.

**Acceptance Criteria:**
- Интерфейс `IElementPairerProvider` существует в `domain/interfaces/`.
- `ElementPairer` реализует `IElementPairerProvider`.
- Компонент, использующий `ElementPairer`, зависит от интерфейса `IElementPairerProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 22. Создание интерфейса IMetadataExtractorProvider и обновление MetadataExtractor**

**1. Команды терминала для получения контекста:**
```bash
cat utils/metadata_extractor.py | head -30
grep -r "MetadataExtractor" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "MetadataExtractor\|Metadata" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/metadata_extractor.py | head -30
grep -r "MetadataExtractor" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "MetadataExtractor\|Metadata" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IMetadataExtractorProvider` для `MetadataExtractor` и обновить зависимости компонентов, использующих извлечение метаданных (например, `BlockProcessorAdapter` или `PageProcessingOrchestrator`), чтобы обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/metadata_extractor_provider.py`.
- Определить интерфейс `IMetadataExtractorProvider` с методами, необходимыми для извлечения метаданных из HTML (например, `extract_metadata_from_header`, `extract_kes_codes`, `extract_kos_codes`).
- Обновить `MetadataExtractor` в `utils/metadata_extractor.py` (или `infrastructure/adapters/` после задачи 6), чтобы он реализовывал `IMetadataExtractorProvider`: `class MetadataExtractor(IMetadataExtractorProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компонент, использующий `MetadataExtractor` (предположительно `BlockProcessorAdapter` или `PageProcessingOrchestrator`).
- Обновить этот компонент, чтобы он принимал `metadata_extractor: IMetadataExtractorProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `MetadataExtractor` как реализацию `IMetadataExtractorProvider`.

**Acceptance Criteria:**
- Интерфейс `IMetadataExtractorProvider` существует в `domain/interfaces/`.
- `MetadataExtractor` реализует `IMetadataExtractorProvider`.
- Компонент, использующий `MetadataExtractor`, зависит от интерфейса `IMetadataExtractorProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 23. Создание интерфейса IProblemBuilderProvider и обновление ProblemBuilder**

**1. Команды терминала для получения контекста:**
```bash
cat models/problem_builder.py | head -30
grep -r "ProblemBuilder" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ProblemBuilder" {} \;
```

**2. Блок для вставки полученного контекста:**

cat models/problem_builder.py | head -30
grep -r "ProblemBuilder" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ProblemBuilder" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IProblemBuilderProvider` для `ProblemBuilder` и обновить зависимости компонентов, использующих построение задач (например, `BlockProcessorAdapter`, `PageProcessingOrchestrator`), чтобы обеспечить соблюдение DIP и формализовать этот процесс как инфраструктурную операцию.

**Действия:**
- Создать файл `domain/interfaces/problem_builder_provider.py`.
- Определить интерфейс `IProblemBuilderProvider` с методами, необходимыми для построения объектов `Problem` (например, `build_problem`, `create_from_dict`, `validate_problem_data`).
- Обновить `ProblemBuilder` в `models/problem_builder.py`, чтобы он реализовывал `IProblemBuilderProvider`: `class ProblemBuilder(IProblemBuilderProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие `ProblemBuilder` (предположительно `BlockProcessorAdapter` или `PageProcessingOrchestrator`).
- Обновить эти компоненты, чтобы они принимали `problem_builder: IProblemBuilderProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `ProblemBuilder` как реализацию `IProblemBuilderProvider`.

**Acceptance Criteria:**
- Интерфейс `IProblemBuilderProvider` существует в `domain/interfaces/`.
- `ProblemBuilder` реализует `IProblemBuilderProvider`.
- Компоненты, использующие `ProblemBuilder`, зависят от интерфейса `IProblemBuilderProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 24. Обновление HTMLProcessingService и TaskProcessingService для использования новых интерфейсов**

**1. Команды терминала для получения контекста:**
```bash
cat application/services/html_processing_service.py
cat application/services/task_processing_service.py
grep -r "HTMLProcessingService\|TaskProcessingService" . --include="*.py" --exclude-dir=venv
```

**2. Блок для вставки полученного контекста:**

cat application/services/html_processing_service.py
cat application/services/task_processing_service.py
grep -r "HTMLProcessingService\|TaskProcessingService" . --include="*.py" --exclude-dir=venv

**3. Само задание:**

**Цель:** Обновить прикладные сервисы `HTMLProcessingService` и `TaskProcessingService`, чтобы они использовали все новые интерфейсы, внедренные в предыдущих задачах, и зависели только от абстракций из доменного слоя.

**Действия:**
- Для `HTMLProcessingService`: Убедиться, что он принимает `html_processor: IHTMLProcessor` и, при необходимости, другие интерфейсы (например, `asset_downloader: IAssetDownloaderProvider`, `element_pairer: IElementPairerProvider`, `metadata_extractor: IMetadataExtractorProvider`, `problem_builder: IProblemBuilderProvider`) через конструктор.
- Для `TaskProcessingService`: Убедиться, что он принимает `task_inferer: ITaskNumberInferer` и `task_classifier: ITaskClassifier` через конструктор.
- Убедиться, что оба сервиса не импортируют и не зависят от конкретных инфраструктурных реализаций напрямую.
- Обновить `api/dependencies.py`, чтобы внедрять правильные реализации интерфейсов в эти сервисы.
- Убедиться, что все методы сервисов используют зависимости через интерфейсы.

**Acceptance Criteria:**
- `HTMLProcessingService` зависит только от интерфейсов из `domain/interfaces/`.
- `TaskProcessingService` зависит только от интерфейсов из `domain/interfaces/`.
- `api/dependencies.py` корректно внедряет реализации интерфейсов в сервисы.
- Все юнит- и интеграционные тесты для сервисов проходят успешно.
- Архитектурные тесты не выявляют нарушений зависимостей.

**Задача 27. Создание интерфейса ISubjectSpecificationProvider и обновление SubjectMapping**

**1. Команды терминала для получения контекста:**
```bash
cat utils/subject_mapping.py
grep -r "subject_mapping\|SubjectMapping\|subject.*spec" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Subject\|spec" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/subject_mapping.py
grep -r "subject_mapping\|SubjectMapping\|subject.*spec" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Subject\|spec" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `ISubjectSpecificationProvider` для компонента, управляющего сопоставлением предметов и спецификаций (например, `SubjectMapping` или логики в `SpecificationService`), чтобы изолировать эту доменную информацию и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/subject_specification_provider.py`.
- Определить интерфейс `ISubjectSpecificationProvider` с методами для получения информации о предметах и их спецификациях (например, `get_subject_list`, `get_spec_for_subject`, `get_subject_code`, `validate_subject`).
- Найти компонент, отвечающий за сопоставление предметов (например, `utils/subject_mapping.py` или логика внутри `SpecificationService`/`SpecificationAdapter`).
- Если `SubjectMapping` - отдельный класс, обновить его, чтобы он реализовывал `ISubjectSpecificationProvider`.
- Если логика встроена в `SpecificationService`, возможно, вынести её в отдельный класс, реализующий `ISubjectSpecificationProvider`.
- Обновить компоненты, использующие сопоставление предметов (например, `FIPIScraper`, `QuizService`, `api/endpoints/`), чтобы они зависели от `ISubjectSpecificationProvider`.
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию.

**Acceptance Criteria:**
- Интерфейс `ISubjectSpecificationProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за сопоставление предметов, реализует `ISubjectSpecificationProvider`.
- Компоненты, использующие сопоставление предметов, зависят от интерфейса `ISubjectSpecificationProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 28. Создание интерфейса IProblemStorageProvider и обновление ProblemStorage**

**1. Команды терминала для получения контекста:**
```bash
cat utils/problem_storage.py
grep -r "ProblemStorage\|problem.*storage\|save.*problem\|load.*problem" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Storage\|Problem.*save\|Problem.*load" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/problem_storage.py
grep -r "ProblemStorage\|problem.*storage\|save.*problem\|load.*problem" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Storage\|Problem.*save\|Problem.*load" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IProblemStorageProvider` для компонента, отвечающего за хранение задач (например, `ProblemStorage`), чтобы изолировать инфраструктурные детали сохранения/загрузки задач и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/problem_storage_provider.py`.
- Определить интерфейс `IProblemStorageProvider` с методами для сохранения и загрузки задач (например, `save_problem`, `load_problem`, `save_batch`, `load_batch`, `check_exists`).
- Обновить `ProblemStorage` в `utils/problem_storage.py` (или `infrastructure/adapters/problem_storage_adapter.py`, если будет перемещен), чтобы он реализовывал `IProblemStorageProvider`: `class ProblemStorage(IProblemStorageProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие `ProblemStorage` (например, компоненты скрапинга, обработки, тестирования).
- Обновить эти компоненты, чтобы они принимали `problem_storage: IProblemStorageProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `ProblemStorage` как реализацию `IProblemStorageProvider`.

**Acceptance Criteria:**
- Интерфейс `IProblemStorageProvider` существует в `domain/interfaces/`.
- `ProblemStorage` реализует `IProblemStorageProvider`.
- Компоненты, использующие `ProblemStorage`, зависят от интерфейса `IProblemStorageProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 29. Создание интерфейса IFIPIUrlProvider и обновление FIPIUrls**

**1. Команды терминала для получения контекста:**
```bash
cat utils/fipi_urls.py
grep -r "fipi_urls\|FIPI_URL\|FIPI_BASE_URL\|FIPI_QUESTIONS_URL" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "FIPI_URL\|UrlProvider" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/fipi_urls.py
grep -r "fipi_urls\|FIPI_URL\|FIPI_BASE_URL\|FIPI_QUESTIONS_URL" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "FIPI_URL\|UrlProvider" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IFIPIUrlProvider` для компонента, управляющего URL-адресами ФИПИ (например, `fipi_urls.py`), чтобы централизовать и изолировать управление адресами и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/fipi_url_provider.py`.
- Определить интерфейс `IFIPIUrlProvider` с методами для получения различных URL-адресов (например, `get_base_url`, `get_questions_url`, `get_subject_url`, `get_task_url`).
- Обновить `fipi_urls.py` (возможно, вынеся константы в класс), чтобы он реализовывал `IFIPIUrlProvider`: `class FIPIUrls(IFIPIUrlProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие URL-адреса ФИПИ (например, `FIPIScraper`, `FIPIAnswerChecker`).
- Обновить эти компоненты, чтобы они принимали `fipi_url_provider: IFIPIUrlProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `FIPIUrls` как реализацию `IFIPIUrlProvider`.

**Acceptance Criteria:**
- Интерфейс `IFIPIUrlProvider` существует в `domain/interfaces/`.
- Компонент, управляющий URL-адресами (например, `FIPIUrls`), реализует `IFIPIUrlProvider`.
- Компоненты, использующие URL-адреса ФИПИ, зависят от интерфейса `IFIPIUrlProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 30. Создание интерфейса ITaskIdGeneratorProvider и обновление TaskIdUtils**

**1. Команды терминала для получения контекста:**
```bash
cat utils/task_id_utils.py
grep -r "task_id_utils\|task.*id.*gen\|generate.*task" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "TaskId\|IdGen" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/task_id_utils.py
grep -r "task_id_utils\|task.*id.*gen\|generate.*task" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "TaskId\|IdGen" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `ITaskIdGeneratorProvider` для компонента, отвечающего за генерацию идентификаторов задач (например, `TaskIdUtils`), чтобы изолировать логику генерации идентификаторов и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/task_id_generator_provider.py`.
- Определить интерфейс `ITaskIdGeneratorProvider` с методами для генерации и валидации идентификаторов задач (например, `generate_task_id`, `validate_task_id`, `create_unique_id`).
- Обновить `TaskIdUtils` в `utils/task_id_utils.py` (или `infrastructure/adapters/task_id_generator_adapter.py`, если будет перемещен), чтобы он реализовывал `ITaskIdGeneratorProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие генерацию идентификаторов задач (например, `ProblemBuilder`, `BlockProcessorAdapter`, `PageProcessingOrchestrator`).
- Обновить эти компоненты, чтобы они принимали `task_id_generator: ITaskIdGeneratorProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `TaskIdUtils` как реализацию `ITaskIdGeneratorProvider`.

**Acceptance Criteria:**
- Интерфейс `ITaskIdGeneratorProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за генерацию идентификаторов задач (например, `TaskIdUtils`), реализует `ITaskIdGeneratorProvider`.
- Компоненты, использующие генерацию идентификаторов задач, зависят от интерфейса `ITaskIdGeneratorProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 31. Создание интерфейса IQuizResultProcessor и обновление обработки результатов викторин**

**1. Команды терминала для получения контекста:**
```bash
grep -r "result\|score\|answer.*result\|quiz.*result" services/quiz_service.py --include="*.py" --exclude-dir=venv
grep -r "check_answer\|result" services/answer_service.py --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "result\|score" {} \; --exclude-dir=venv | grep -E "(service|processor|handler)"
```

**2. Блок для вставки полученного контекста:**

grep -r "result\|score\|answer.*result\|quiz.*result" services/quiz_service.py --include="*.py" --exclude-dir=venv
grep -r "check_answer\|result" services/answer_service.py --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "result\|score" {} \; --exclude-dir=venv | grep -E "(service|processor|handler)"

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizResultProcessor` для компонента, отвечающего за обработку результатов викторин и ответов пользователей, чтобы изолировать логику анализа результатов и обновления прогресса, обеспечив соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_result_processor.py`.
- Определить интерфейс `IQuizResultProcessor` с методами для обработки результатов (например, `process_answer_result`, `update_user_progress`, `calculate_score`, `determine_next_step`, `generate_feedback`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizResultProcessor` в `application/services/` или `infrastructure/adapters/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizResultProcessor`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие обработку результатов (например, `AnswerService`, `QuizService`, возможно, API endpoints).
- Обновить эти компоненты, чтобы они принимали `quiz_result_processor: IQuizResultProcessor` через конструктор или методы.
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию `IQuizResultProcessor`.

**Acceptance Criteria:**
- Интерфейс `IQuizResultProcessor` существует в `domain/interfaces/`.
- Компонент, отвечающий за обработку результатов, реализует `IQuizResultProcessor`.
- Компоненты, использующие обработку результатов, зависят от интерфейса `IQuizResultProcessor`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 32. Создание интерфейса ICacheProvider и обновление LocalStorage как кэша**

**1. Команды терминала для получения контекста:**
```bash
cat utils/local_storage.py | head -30
grep -r "LocalStorage\|cache\|store.*local" . --include="*.py" --exclude-dir=venv
find services/interfaces.py -name "*.py" -exec grep -l "Cache" {} \; # до выполнения задачи 3
```

**2. Блок для вставки полученного контекста:**

cat utils/local_storage.py | head -30
grep -r "LocalStorage\|cache\|store.*local" . --include="*.py" --exclude-dir=venv
find services/interfaces.py -name "*.py" -exec grep -l "Cache" {} \; # до выполнения задачи 3

**3. Само задание:**

**Цель:** Убедиться, что `LocalStorage` формально реализует интерфейс `ICacheProvider` (после его перемещения в `domain/interfaces/` в задаче 3) и используется как кэш в приложении, обеспечив соблюдение DIP.

**Действия:**
- После выполнения задачи 3, когда `ICacheProvider` будет в `domain/interfaces/infrastructure_adapters.py`:
- Обновить `LocalStorage` в `utils/local_storage.py` (или `infrastructure/adapters/local_storage_adapter.py` после задачи 5), чтобы он реализовывал `ICacheProvider`: `class LocalStorage(ICacheProvider):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу `ICacheProvider`.
- Найти компоненты, использующие `LocalStorage` (например, `AnswerService`).
- Убедиться, что зависимости внедряются через интерфейс `ICacheProvider` (после обновления DI в задаче 3).
- Проверить, что `LocalStorage` используется строго в соответствии с контрактом `ICacheProvider`.

**Acceptance Criteria:**
- `LocalStorage` реализует `ICacheProvider` из `domain.interfaces.infrastructure_adapters`.
- Компоненты, использующие `LocalStorage`, зависят от интерфейса `ICacheProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 33. Создание интерфейса IQuizFeedbackGenerator и обновление генерации обратной связи**

**1. Команды терминала для получения контекста:**
```bash
grep -r "feedback\|comment\|explanation\|hint" services/ --include="*.py" --exclude-dir=venv
grep -r "feedback\|comment\|explanation\|hint" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "feedback\|explanation" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "feedback\|comment\|explanation\|hint" services/ --include="*.py" --exclude-dir=venv
grep -r "feedback\|comment\|explanation\|hint" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "feedback\|explanation" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizFeedbackGenerator` для компонента, отвечающего за генерацию обратной связи для пользователя по результатам викторины или ответам, чтобы изолировать логику формирования педагогической обратной связи и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_feedback_generator.py`.
- Определить интерфейс `IQuizFeedbackGenerator` с методами для генерации обратной связи (например, `generate_task_feedback`, `generate_quiz_summary`, `provide_explanation`, `suggest_next_steps`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizFeedbackGenerator` в `application/services/` или `domain/services/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizFeedbackGenerator`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие генерацию обратной связи (например, `AnswerService`, `QuizService`, возможно, API endpoints для получения результата).
- Обновить эти компоненты, чтобы они принимали `quiz_feedback_generator: IQuizFeedbackGenerator` через конструктор или методы.
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию `IQuizFeedbackGenerator`.

**Acceptance Criteria:**
- Интерфейс `IQuizFeedbackGenerator` существует в `domain/interfaces/`.
- Компонент, отвечающий за генерацию обратной связи, реализует `IQuizFeedbackGenerator`.
- Компоненты, использующие генерацию обратной связи, зависят от интерфейса `IQuizFeedbackGenerator`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 34. Создание интерфейса IUserProgressTracker и обновление отслеживания прогресса пользователя**

**1. Команды терминала для получения контекста:**
```bash
grep -r "progress\|user.*stat\|track\|history" services/ --include="*.py" --exclude-dir=venv
grep -r "progress\|user.*stat\|track\|history" models/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "progress\|statistic\|history" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "progress\|user.*stat\|track\|history" services/ --include="*.py" --exclude-dir=venv
grep -r "progress\|user.*stat\|track\|history" models/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "progress\|statistic\|history" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IUserProgressTracker` для компонента, отвечающего за отслеживание и хранение прогресса пользователя, чтобы изолировать логику управления пользовательским прогрессом и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/user_progress_tracker.py`.
- Определить интерфейс `IUserProgressTracker` с методами для отслеживания и получения прогресса (например, `update_task_progress`, `get_user_progress`, `get_topic_mastery`, `save_session_result`, `get_learning_history`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `UserProgressTracker` в `application/services/` или `infrastructure/adapters/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IUserProgressTracker`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие отслеживание прогресса (например, `QuizService`, `AnswerService`, `QuizResultProcessor`, возможно, API endpoints для получения статистики).
- Обновить эти компоненты, чтобы они принимали `user_progress_tracker: IUserProgressTracker` через конструктор или методы.
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию `IUserProgressTracker`.

**Acceptance Criteria:**
- Интерфейс `IUserProgressTracker` существует в `domain/interfaces/`.
- Компонент, отвечающий за отслеживание прогресса, реализует `IUserProgressTracker`.
- Компоненты, использующие отслеживание прогресса, зависят от интерфейса `IUserProgressTracker`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 35. Создание интерфейса ISearchProvider и обновление QdrantProblemRetriever как поискового компонента**

**1. Команды терминала для получения контекста:**
```bash
cat utils/retriever.py | head -30
grep -r "QdrantProblemRetriever\|search\|retrieve" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ProblemRetriever\|Search" {} \;  # после задачи 11
```

**2. Блок для вставки полученного контекста:**

cat utils/retriever.py | head -30
grep -r "QdrantProblemRetriever\|search\|retrieve" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ProblemRetriever\|Search" {} \;  # после задачи 11

**3. Само задание:**

**Цель:** Убедиться, что `QdrantProblemRetriever` формально реализует интерфейс `IProblemRetriever` (созданный в задаче 11, возможно, с переименованием в `ISearchProvider` или включением поисковой функциональности), и используется строго через этот интерфейс, обеспечив соблюдение DIP.

**Действия:**
- После выполнения задачи 11, когда `IProblemRetriever` (или `ISearchProvider`) будет в `domain/interfaces/`:
- Обновить `QdrantProblemRetriever` в `utils/retriever.py` (или `infrastructure/adapters/qdrant_retriever_adapter.py` после задачи 5), чтобы он реализовывал `IProblemRetriever`: `class QdrantProblemRetriever(IProblemRetriever):`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу `IProblemRetriever`.
- Найти компоненты, использующие `QdrantProblemRetriever` (например, `QuizService`).
- Убедиться, что зависимости внедряются через интерфейс `IProblemRetriever` (после обновления DI в задаче 11).
- Проверить, что `QdrantProblemRetriever` используется строго в соответствии с контрактом `IProblemRetriever`.

**Acceptance Criteria:**
- `QdrantProblemRetriever` реализует `IProblemRetriever` из `domain.interfaces.infrastructure_adapters` (или соответствующего файла).
- Компоненты, использующие `QdrantProblemRetriever`, зависят от интерфейса `IProblemRetriever`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 36. Создание интерфейса IModelAdapterProvider и обновление ModelAdapter**

**1. Команды тернала для получения контекста:**
```bash
cat utils/model_adapter.py
grep -r "ModelAdapter\|model.*adapt\|adapter.*model" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ModelAdapter\|Adapter" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/model_adapter.py
grep -r "ModelAdapter\|model.*adapt\|adapter.*model" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "ModelAdapter\|Adapter" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IModelAdapterProvider` для компонента `ModelAdapter`, чтобы формализовать его роль как адаптера между различными моделями данных и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/model_adapter_provider.py`.
- Определить интерфейс `IModelAdapterProvider` с методами для преобразования между моделями (например, `adapt_problem_to_api`, `adapt_api_to_problem`, `adapt_quiz_result`, `convert_to_domain_model`).
- Обновить `ModelAdapter` в `utils/model_adapter.py` (или `infrastructure/adapters/model_adapter.py`, если будет перемещен), чтобы он реализовывал `IModelAdapterProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие `ModelAdapter` (например, API endpoints, сервисы при конвертации данных).
- Обновить эти компоненты, чтобы они принимали `model_adapter: IModelAdapterProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `ModelAdapter` как реализацию `IModelAdapterProvider`.

**Acceptance Criteria:**
- Интерфейс `IModelAdapterProvider` существует в `domain/interfaces/`.
- `ModelAdapter` реализует `IModelAdapterProvider`.
- Компоненты, использующие `ModelAdapter`, зависят от интерфейса `IModelAdapterProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 37. Создание интерфейса IVectorIndexerProvider и обновление VectorIndexer**

**1. Команды терминала для получения контекста:**
```bash
cat utils/vector_indexer.py | head -30
grep -r "VectorIndexer\|vector.*index\|index.*vector\|qdrant.*index" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Vector\|Index" {} \;
```

**2. Блок для вставки полученного контекста:**

cat utils/vector_indexer.py | head -30
grep -r "VectorIndexer\|vector.*index\|index.*vector\|qdrant.*index" . --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "Vector\|Index" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IVectorIndexerProvider` для компонента `VectorIndexer`, чтобы формализовать его роль как инфраструктурного адаптера для векторной индексации задач и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/vector_indexer_provider.py`.
- Определить интерфейс `IVectorIndexerProvider` с методами для векторной индексации (например, `index_problems`, `update_index`, `delete_from_index`, `rebuild_index`).
- Обновить `VectorIndexer` в `utils/vector_indexer.py` (или `infrastructure/adapters/vector_indexer_adapter.py`, если будет перемещен), чтобы он реализовывал `IVectorIndexerProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие `VectorIndexer` (например, скрипты миграции, обновления, возможно, части скрапинга или обработки).
- Обновить эти компоненты, чтобы они принимали `vector_indexer: IVectorIndexerProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять `VectorIndexer` как реализацию `IVectorIndexerProvider`.

**Acceptance Criteria:**
- Интерфейс `IVectorIndexerProvider` существует в `domain/interfaces/`.
- `VectorIndexer` реализует `IVectorIndexerProvider`.
- Компоненты, использующие `VectorIndexer`, зависят от интерфейса `IVectorIndexerProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 38. Создание интерфейса IQuizSessionManager и обновление управления сессиями викторин**

**1. Команды терминала для получения контекста:**
```bash
grep -r "session\|quiz.*start\|quiz.*end\|active.*quiz" services/ --include="*.py" --exclude-dir=venv
grep -r "session\|quiz.*start\|quiz.*end\|active.*quiz" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "session\|QuizSession" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "session\|quiz.*start\|quiz.*end\|active.*quiz" services/ --include="*.py" --exclude-dir=venv
grep -r "session\|quiz.*start\|quiz.*end\|active.*quiz" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "session\|QuizSession" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizSessionManager` для компонента, отвечающего за управление сессиями викторин (начало, окончание, сохранение состояния), чтобы изолировать логику управления сессиями и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_session_manager.py`.
- Определить интерфейс `IQuizSessionManager` с методами для управления сессиями (например, `start_quiz_session`, `end_quiz_session`, `get_current_session_state`, `save_session_progress`, `load_session_data`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizSessionManager` в `application/services/` или `infrastructure/adapters/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizSessionManager`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, использующие управление сессиями (например, `QuizService`, API endpoints для `/start`, `/next`, `/submit`).
- Обновить эти компоненты, чтобы они принимали `quiz_session_manager: IQuizSessionManager` через конструктор или методы.
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию `IQuizSessionManager`.

**Acceptance Criteria:**
- Интерфейс `IQuizSessionManager` существует в `domain/interfaces/`.
- Компонент, отвечающий за управление сессиями, реализует `IQuizSessionManager`.
- Компоненты, использующие управление сессиями, зависят от интерфейса `IQuizSessionManager`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 39. Создание интерфейса IExternalResourceValidator и обновление проверки внешних ресурсов**

**1. Команды терминала для получения контекста:**
```bash
grep -r "validate\|check.*url\|resource.*health\|external.*check" . --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "validate\|health" {} \; --exclude-dir=venv | grep -v "test"
find services/ -name "*.py" -exec grep -i "check\|validate" {} \;
```

**2. Блок для вставки полученного контекста:**

grep -r "validate\|check.*url\|resource.*health\|external.*check" . --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "validate\|health" {} \; --exclude-dir=venv | grep -v "test"
find services/ -name "*.py" -exec grep -i "check\|validate" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IExternalResourceValidator` для компонента, отвечающего за проверку доступности и валидность внешних ресурсов (например, URL задач ФИПИ, изображений), чтобы изолировать эту инфраструктурную логику и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/external_resource_validator.py`.
- Определить интерфейс `IExternalResourceValidator` с методами для проверки ресурсов (например, `validate_url_accessibility`, `check_resource_integrity`, `validate_image_url`, `ping_external_service`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `ExternalResourceValidator` в `infrastructure/adapters/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IExternalResourceValidator`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые могут использовать валидацию внешних ресурсов (например, компоненты обработки HTML при извлечении изображений/файлов, скрапинга).
- Обновить эти компоненты, чтобы они принимали `external_resource_validator: IExternalResourceValidator` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IExternalResourceValidator`.

**Acceptance Criteria:**
- Интерфейс `IExternalResourceValidator` существует в `domain/interfaces/`.
- Компонент, отвечающий за валидацию внешних ресурсов, реализует `IExternalResourceValidator`.
- Компоненты, использующие валидацию внешних ресурсов, зависят от интерфейса `IExternalResourceValidator`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 40. Создание интерфейса IContentRendererProvider и обновление рендеринга контента задач**

**1. Команды терминала для получения контекста:**
```bash
grep -r "render\|html.*render\|content.*to.*html\|display.*problem" . --include="*.py" --exclude-dir=venv
find processors/ -name "*.py" -exec grep -i "render\|html\|display" {} \;
find api/endpoints/ -name "*.py" -exec grep -i "render\|html\|display" {} \;
find . -name "*.py" -exec grep -l "ui\|template\|jinja" {} \; --exclude-dir=venv
```

**2. Блок для вставки полученного контекста:**

grep -r "render\|html.*render\|content.*to.*html\|display.*problem" . --include="*.py" --exclude-dir=venv
find processors/ -name "*.py" -exec grep -i "render\|html\|display" {} \;
find api/endpoints/ -name "*.py" -exec grep -i "render\|html\|display" {} \;
find . -name "*.py" -exec grep -l "ui\|template\|jinja" {} \; --exclude-dir=venv

**3. Само задание:**

**Цель:** Создать интерфейс `IContentRendererProvider` для компонента, отвечающего за преобразование задачи в HTML или другой формат для отображения пользователю, чтобы изолировать логику рендеринга и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/content_renderer_provider.py`.
- Определить интерфейс `IContentRendererProvider` с методами для рендеринга контента (например, `render_problem_html`, `render_problem_to_offline_html`, `apply_theme`, `sanitize_content_for_display`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `ContentRenderer` в `application/services/` или `infrastructure/adapters/`, возможно, используя `ui_components.py`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IContentRendererProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые используют рендеринг контента (например, API endpoints, компоненты генерации оффлайн HTML).
- Обновить эти компоненты, чтобы они принимали `content_renderer: IContentRendererProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IContentRendererProvider`.

**Acceptance Criteria:**
- Интерфейс `IContentRendererProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за рендеринг контента, реализует `IContentRendererProvider`.
- Компоненты, использующие рендеринг контента, зависят от интерфейса `IContentRendererProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 41. Создание интерфейса ISpecificationValidatorProvider и обновление валидации спецификаций**

**1. Команды терминала для получения контекста:**
```bash
grep -r "spec.*valid\|validate.*spec\|check.*spec" . --include="*.py" --exclude-dir=venv
find data/specs/ -name "*.json" -exec head -5 {} \;  # Посмотреть структуру спецификаций
find . -name "*.py" -exec grep -l "spec" {} \; --exclude-dir=venv | grep -E "(service|adapter|utils)"
```

**2. Блок для вставки полученного контекста:**

grep -r "spec.*valid\|validate.*spec\|check.*spec" . --include="*.py" --exclude-dir=venv
find data/specs/ -name "*.json" -exec head -5 {} \;  # Посмотреть структуру спецификаций
find . -name "*.py" -exec grep -l "spec" {} \; --exclude-dir=venv | grep -E "(service|adapter|utils)"

**3. Само задание:**

**Цель:** Создать интерфейс `ISpecificationValidatorProvider` для компонента, отвечающего за валидацию структуры и содержания файлов спецификаций ФИПИ (например, `ege_2026_math_spec.json`), чтобы изолировать эту логику и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/specification_validator_provider.py`.
- Определить интерфейс `ISpecificationValidatorProvider` с методами для валидации спецификаций (например, `validate_spec_structure`, `validate_kes_codes`, `validate_task_numbers`, `check_spec_consistency`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `SpecificationValidator` в `infrastructure/adapters/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `ISpecificationValidatorProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые могут использовать валидацию спецификаций (например, `SpecificationAdapter`, скрипты загрузки/проверки спецификаций).
- Обновить эти компоненты, чтобы они принимали `specification_validator: ISpecificationValidatorProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `ISpecificationValidatorProvider`.

**Acceptance Criteria:**
- Интерфейс `ISpecificationValidatorProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за валидацию спецификаций, реализует `ISpecificationValidatorProvider`.
- Компоненты, использующие валидацию спецификаций, зависят от интерфейса `ISpecificationValidatorProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 42. Создание интерфейса ITaskDifficultyEstimatorProvider и обновление оценки сложности задач**

**1. Команды терминала для получения контекста:**
```bash
grep -r "difficulty\|hard\|easy\|complex\|estimate.*task" . --include="*.py" --exclude-dir=venv
grep -r "difficulty_level\|max_score" services/quiz_service.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "difficulty\|Task.*Estim" {} \;
```

**2. Блок для вставки полученного контекста:**

grep -r "difficulty\|hard\|easy\|complex\|estimate.*task" . --include="*.py" --exclude-dir=venv
grep -r "difficulty_level\|max_score" services/quiz_service.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "difficulty\|Task.*Estim" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `ITaskDifficultyEstimatorProvider` для компонента, отвечающего за оценку сложности задач на основе различных факторов (КЭС-коды, тип задачи, длина текста и т.д.), чтобы изолировать эту логику и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/task_difficulty_estimator_provider.py`.
- Определить интерфейс `ITaskDifficultyEstimatorProvider` с методами для оценки сложности (например, `estimate_difficulty`, `get_complexity_factors`, `classify_by_difficulty`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `TaskDifficultyEstimator` в `domain/services/` или `application/services/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `ITaskDifficultyEstimatorProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые используют оценку сложности (например, `TaskClassifierAdapter`, `QuizService`, `QuizScheduler`).
- Обновить эти компоненты, чтобы они принимали `task_difficulty_estimator: ITaskDifficultyEstimatorProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `ITaskDifficultyEstimatorProvider`.

**Acceptance Criteria:**
- Интерфейс `ITaskDifficultyEstimatorProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за оценку сложности, реализует `ITaskDifficultyEstimatorProvider`.
- Компоненты, использующие оценку сложности, зависят от интерфейса `ITaskDifficultyEstimatorProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 43. Создание интерфейса IAnswerValidatorProvider и обновление валидации ответов**

**1. Команды терминала для получения контекста:**
```bash
grep -r "validate.*answer\|answer.*valid\|check.*answer\|verify.*answer" . --include="*.py" --exclude-dir=venv
grep -r "FIPIAnswerChecker\|check_answer" services/answer_service.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "answer.*valid\|Answer.*Check" {} \;
```

**2. Блок для вставки полученного контекста:**

grep -r "validate.*answer\|answer.*valid\|check.*answer\|verify.*answer" . --include="*.py" --exclude-dir=venv
grep -r "FIPIAnswerChecker\|check_answer" services/answer_service.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "answer.*valid\|Answer.*Check" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IAnswerValidatorProvider` для компонента, отвечающего за валидацию и проверку пользовательских ответов (включая взаимодействие с ФИПИ), чтобы изолировать эту инфраструктурную логику и обеспечить соблюдение DIP. Это может быть формализация существующего `FIPIAnswerChecker`.

**Действия:**
- Создать файл `domain/interfaces/answer_validator_provider.py`.
- Определить интерфейс `IAnswerValidatorProvider` с методами для проверки ответов (например, `validate_answer_format`, `check_answer_correctness`, `get_detailed_feedback`).
- После задачи 17, когда `FIPIAnswerChecker` будет реализовывать `IBrowserResourceProvider`, обновить его (или создать новый адаптер), чтобы он также реализовывал `IAnswerValidatorProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу `IAnswerValidatorProvider`.
- Найти компоненты, которые используют проверку ответов (например, `AnswerService`).
- Обновить `AnswerService`, чтобы он зависел от `IAnswerValidatorProvider` вместо конкретного `FIPIAnswerChecker`.
- Обновить `api/dependencies.py`, чтобы внедрять `FIPIAnswerChecker` (или новый адаптер) как реализацию обоих интерфейсов (`IBrowserResourceProvider` и `IAnswerValidatorProvider`) в `AnswerService`.

**Acceptance Criteria:**
- Интерфейс `IAnswerValidatorProvider` существует в `domain/interfaces/`.
- Компонент проверки ответов (например, `FIPIAnswerChecker` или новый адаптер) реализует `IAnswerValidatorProvider`.
- `AnswerService` зависит от интерфейса `IAnswerValidatorProvider`.
- DI корректно работает с новой структурой, внедряя реализацию через `get_answer_checker`.
- Все тесты проходят успешно.

---

**Задача 44. Создание интерфейса IQuizScorerProvider и обновление подсчета очков викторины**

**1. Команды терминала для получения контекста:**
```bash
grep -r "score\|point\|calculate.*score\|quiz.*score" services/ --include="*.py" --exclude-dir=venv
grep -r "max_score\|difficulty" models/problem_schema.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "score\|point\|Quiz.*Scor" {} \;
```

**2. Блок для вставки полученного контекста:**

grep -r "score\|point\|calculate.*score\|quiz.*score" services/ --include="*.py" --exclude-dir=venv
grep -r "max_score\|difficulty" models/problem_schema.py --include="*.py" --exclude-dir=venv
find domain/interfaces/ -name "*.py" -exec grep -l "score\|point\|Quiz.*Scor" {} \;

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizScorerProvider` для компонента, отвечающего за подсчет очков за задачи и викторины на основе сложности, правильности и других факторов, чтобы изолировать эту логику и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_scorer_provider.py`.
- Определить интерфейс `IQuizScorerProvider` с методами для подсчета очков (например, `calculate_task_score`, `calculate_quiz_total_score`, `apply_scoring_rules`, `get_score_for_difficulty`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizScorer` в `application/services/` или `domain/services/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizScorerProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые используют подсчет очков (например, `AnswerService`, `QuizResultProcessor`, `QuizService`).
- Обновить эти компоненты, чтобы они принимали `quiz_scorer: IQuizScorerProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IQuizScorerProvider`.

**Acceptance Criteria:**
- Интерфейс `IQuizScorerProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за подсчет очков, реализует `IQuizScorerProvider`.
- Компоненты, использующие подсчет очков, зависят от интерфейса `IQuizScorerProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 45. Создание интерфейса IQuizRuleEngineProvider и обновление применения правил викторины**

**1. Команды терминала для получения контекста:**
```bash
grep -r "rule\|condition\|quiz.*rule\|if.*quiz\|logic.*quiz" services/ --include="*.py" --exclude-dir=venv
grep -r "rule\|condition\|quiz.*rule\|if.*quiz\|logic.*quiz" application/services/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "rule\|condition\|logic" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "rule\|condition\|quiz.*rule\|if.*quiz\|logic.*quiz" services/ --include="*.py" --exclude-dir=venv
grep -r "rule\|condition\|quiz.*rule\|if.*quiz\|logic.*quiz" application/services/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "rule\|condition\|logic" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizRuleEngineProvider` для компонента, отвечающего за применение бизнес-правил викторины (например, ограничение количества задач по теме, чередование типов задач, адаптивная сложность), чтобы изолировать эту логику и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_rule_engine_provider.py`.
- Определить интерфейс `IQuizRuleEngineProvider` с методами для применения правил (например, `apply_quiz_generation_rules`, `validate_task_selection`, `check_topic_balance`, `enforce_difficulty_progression`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizRuleEngine` в `application/services/` или `domain/services/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizRuleEngineProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые используют применение правил (например, `QuizService`, `QuizScheduler`, `QuizSessionManager`).
- Обновить эти компоненты, чтобы они принимали `quiz_rule_engine: IQuizRuleEngineProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IQuizRuleEngineProvider`.

**Acceptance Criteria:**
- Интерфейс `IQuizRuleEngineProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за применение правил викторины, реализует `IQuizRuleEngineProvider`.
- Компоненты, использующие применение правил, зависят от интерфейса `IQuizRuleEngineProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 46. Создание интерфейса IUserAuthenticationProvider и обновление аутентификации пользователей**

**1. Команды терминала для получения контекста:**
```bash
grep -r "auth\|login\|user.*auth\|authenticate\|session.*user" . --include="*.py" --exclude-dir=venv
find api/ -name "*.py" -exec grep -i "auth\|user" {} \; | grep -v "test"
find services/ -name "*.py" -exec grep -i "auth\|user" {} \; | grep -v "test"
find . -name "*.py" -exec grep -l "auth" {} \; --exclude-dir=venv | grep -v "test" | head -10
```

**2. Блок для вставки полученного контекста:**

grep -r "auth\|login\|user.*auth\|authenticate\|session.*user" . --include="*.py" --exclude-dir=venv
find api/ -name "*.py" -exec grep -i "auth\|user" {} \; | grep -v "test"
find services/ -name "*.py" -exec grep -i "auth\|user" {} \; | grep -v "test"
find . -name "*.py" -exec grep -l "auth" {} \; --exclude-dir=venv | grep -v "test" | head -10

**3. Само задание:**

**Цель:** Создать интерфейс `IUserAuthenticationProvider` для компонента, отвечающего за аутентификацию и управление сессиями пользователей, чтобы изолировать эту инфраструктурную логику, обеспечить соблюдение DIP и подготовить систему к будущей реализации полноценной аутентификации (даже если сейчас она упрощена или отсутствует).

**Действия:**
- Создать файл `domain/interfaces/user_authentication_provider.py`.
- Определить интерфейс `IUserAuthenticationProvider` с методами для аутентификации (например, `authenticate_user`, `create_user_session`, `validate_session_token`, `logout_user`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `UserAuthenticationProvider` в `infrastructure/adapters/` или `application/services/`). Если аутентификация пока не реализована, создать заглушку.
- Обновить найденный/созданный компонент, чтобы он реализовывал `IUserAuthenticationProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые могут использовать аутентификацию (например, API endpoints, `QuizService`, `AnswerService`, `UserProgressTracker`).
- Обновить эти компоненты, чтобы они принимали `user_authentication: IUserAuthenticationProvider` через конструктор или методы (через DI или как параметр в методах).
- Обновить `api/dependencies.py`, чтобы внедрять подходящую реализацию `IUserAuthenticationProvider`.

**Acceptance Criteria:**
- Интерфейс `IUserAuthenticationProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за аутентификацию (даже если это заглушка), реализует `IUserAuthenticationProvider`.
- Компоненты, использующие аутентификацию, зависят от интерфейса `IUserAuthenticationProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.


**Задача 47. Создание интерфейса IQuizReportGeneratorProvider и обновление генерации отчетов по викторинам**

**1. Команды терминала для получения контекста:**
```bash
grep -r "report\|export\|statistic.*quiz\|quiz.*summary\|analytics" services/ --include="*.py" --exclude-dir=venv
grep -r "report\|export\|statistic.*quiz\|quiz.*summary\|analytics" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "report\|export\|analytics" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "report\|export\|statistic.*quiz\|quiz.*summary\|analytics" services/ --include="*.py" --exclude-dir=venv
grep -r "report\|export\|statistic.*quiz\|quiz.*summary\|analytics" api/endpoints/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "report\|export\|analytics" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IQuizReportGeneratorProvider` для компонента, отвечающего за генерацию отчетов и аналитики по результатам викторин, чтобы изолировать логику формирования отчетов и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/quiz_report_generator_provider.py`.
- Определить интерфейс `IQuizReportGeneratorProvider` с методами для генерации отчетов (например, `generate_quiz_report`, `get_user_statistics`, `export_results`, `create_analytics_summary`, `get_topic_performance_report`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `QuizReportGenerator` в `application/services/` или `domain/services/`).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IQuizReportGeneratorProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые используют генерацию отчетов (например, API endpoints для получения статистики, `QuizService`, `UserProgressTracker`).
- Обновить эти компоненты, чтобы они принимали `quiz_report_generator: IQuizReportGeneratorProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IQuizReportGeneratorProvider`.

**Acceptance Criteria:**
- Интерфейс `IQuizReportGeneratorProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за генерацию отчетов, реализует `IQuizReportGeneratorProvider`.
- Компоненты, использующие генерацию отчетов, зависят от интерфейса `IQuizReportGeneratorProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

---

**Задача 48. Создание интерфейса IContentSanitizerProvider и обновление очистки контента задач**

**1. Команды терминала для получения контекста:**
```bash
grep -r "sanitize\|clean.*html\|xss\|security.*html\|escape" processors/ --include="*.py" --exclude-dir=venv
grep -r "sanitize\|clean.*html\|xss\|security.*html\|escape" utils/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "sanitize\|clean\|security" {} \; --exclude-dir=venv | grep -v "test"
```

**2. Блок для вставки полученного контекста:**

grep -r "sanitize\|clean.*html\|xss\|security.*html\|escape" processors/ --include="*.py" --exclude-dir=venv
grep -r "sanitize\|clean.*html\|xss\|security.*html\|escape" utils/ --include="*.py" --exclude-dir=venv
find . -name "*.py" -exec grep -l "sanitize\|clean\|security" {} \; --exclude-dir=venv | grep -v "test"

**3. Само задание:**

**Цель:** Создать интерфейс `IContentSanitizerProvider` для компонента, отвечающего за очистку HTML-контента задач от потенциально опасных элементов (XSS, нежелательные теги), чтобы изолировать эту важную инфраструктурную логику безопасности и обеспечить соблюдение DIP.

**Действия:**
- Создать файл `domain/interfaces/content_sanitizer_provider.py`.
- Определить интерфейс `IContentSanitizerProvider` с методами для очистки контента (например, `sanitize_html_content`, `remove_dangerous_tags`, `escape_user_input`, `validate_safe_html`).
- Найти или создать компонент, который будет реализовывать эту логику (например, `ContentSanitizer` в `infrastructure/adapters/` или `utils/` как адаптер).
- Обновить найденный/созданный компонент, чтобы он реализовывал `IContentSanitizerProvider`.
- Убедиться, что сигнатуры методов соответствуют интерфейсу.
- Найти компоненты, которые могут использовать очистку контента (например, `BlockProcessorAdapter`, `ContentRendererProvider`, процессоры HTML в `processors/html/`).
- Обновить эти компоненты, чтобы они принимали `content_sanitizer: IContentSanitizerProvider` через конструктор или методы.
- Обновить `api/dependencies.py` или `application/services/`, чтобы внедрять подходящую реализацию `IContentSanitizerProvider`.

**Acceptance Criteria:**
- Интерфейс `IContentSanitizerProvider` существует в `domain/interfaces/`.
- Компонент, отвечающий за очистку контента, реализует `IContentSanitizerProvider`.
- Компоненты, использующие очистку контента, зависят от интерфейса `IContentSanitizerProvider`.
- DI корректно работает с новой структурой.
- Все тесты проходят успешно.

**Задача 49. Создание интерфейса IFileStorageProvider и обновление FileStorage**

Создать `IFileStorageProvider` в `domain/interfaces/` и обновить `FileStorage` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих файловое хранилище.

**Задача 50. Создание интерфейса IEmailProvider и обновление EmailService**

Создать `IEmailProvider` в `domain/interfaces/` и обновить `EmailService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих отправку email (например, уведомления).

**Задача 51. Создание интерфейса ISMSProvider и обновление SMSService**

Создать `ISMSProvider` в `domain/interfaces/` и обновить `SMSService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих отправку SMS (например, уведомления).

**Задача 52. Создание интерфейса ICacheManagerProvider и обновление CacheManager**

Создать `ICacheManagerProvider` в `domain/interfaces/` и обновить `CacheManager` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих кэширование.

**Задача 53. Создание интерфейса IRateLimiterProvider и обновление RateLimiter**

Создать `IRateLimiterProvider` в `domain/interfaces/` и обновить `RateLimiter` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих ограничение частоты запросов (например, API endpoints).

**Задача 54. Создание интерфейса IEventPublisherProvider и обновление EventPublisher**

Создать `IEventPublisherProvider` в `domain/interfaces/` и обновить `EventPublisher` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, публикующих события (например, `AnswerService`, `QuizService`).

**Задача 55. Создание интерфейса IEventSubscriberProvider и обновление EventSubscriber**

Создать `IEventSubscriberProvider` в `domain/interfaces/` и обновить `EventSubscriber` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, подписывающихся на события.

**Задача 56. Создание интерфейса IWorkflowEngineProvider и обновление WorkflowEngine**

Создать `IWorkflowEngineProvider` в `domain/interfaces/` и обновить `WorkflowEngine` (если существует) в `application/services/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, участвующих в сложных бизнес-процессах (например, полный цикл викторины).

**Задача 57. Создание интерфейса ISearchQueryBuilder и обновление SearchQueryBuilder**

Создать `ISearchQueryBuilder` в `domain/interfaces/` и обновить `SearchQueryBuilder` (если существует) в `application/services/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, формирующих поисковые запросы (например, `QuizService`, `QdrantProblemRetriever`).

**Задача 58. Создание интерфейса IExternalAPIClientProvider и обновление ExternalAPIClient**

Создать `IExternalAPIClientProvider` в `domain/interfaces/` и обновить `ExternalAPIClient` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, взаимодействующих с внешними API (например, помимо ФИПИ, другие сервисы в будущем).

**Задача 59. Создание интерфейса IDataMigrationProvider и обновление DataMigrationService**

Создать `IDataMigrationProvider` в `domain/interfaces/` и обновить `DataMigrationService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости скриптов миграции данных.

**Задача 60. Создание интерфейса IBackupProvider и обновление BackupService**

Создать `IBackupProvider` в `domain/interfaces/` и обновить `BackupService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, управляющих резервным копированием.

**Задача 61. Создание интерфейса IFeatureFlagProvider и обновление FeatureFlagService**

Создать `IFeatureFlagProvider` в `domain/interfaces/` и обновить `FeatureFlagService` (если существует) в `application/services/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, использующих флаги функций.

**Задача 62. Создание интерфейса ILocalizationProvider и обновление LocalizationService**

Создать `ILocalizationProvider` в `domain/interfaces/` и обновить `LocalizationService` (если существует) в `application/services/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, отвечающих за локализацию (переводы интерфейса).

**Задача 63. Создание интерфейса IThemeManagerProvider и обновление ThemeManager**

Создать `IThemeManagerProvider` в `domain/interfaces/` и обновить `ThemeManager` (если существует) в `application/services/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, управляющих темами оформления.

**Задача 64. Создание интерфейса IFileFormatConverterProvider и обновление FileFormatConverter**

Создать `IFileFormatConverterProvider` в `domain/interfaces/` и обновить `FileFormatConverter` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, конвертирующих форматы файлов (например, HTML в PDF для оффлайн-режима).

**Задача 65. Создание интерфейса IEncryptionProvider и обновление EncryptionService**

Создать `IEncryptionProvider` в `domain/interfaces/` и обновить `EncryptionService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, работающих с чувствительными данными.

**Задача 66. Создание интерфейса ICompressionProvider и обновление CompressionService**

Создать `ICompressionProvider` в `domain/interfaces/` и обновить `CompressionService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, сжимающих данные (например, при сохранении оффлайн-контента).

**Задача 67. Создание интерфейса IBackupRestoreProvider и обновление BackupRestoreService**

Создать `IBackupRestoreProvider` в `domain/interfaces/` и обновить `BackupRestoreService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, восстанавливающих данные из резервных копий.

**Задача 68. Создание интерфейса IHealthCheckProvider и обновление HealthCheckService**

Создать `IHealthCheckProvider` в `domain/interfaces/` и обновить `HealthCheckService` (если существует) в `infrastructure/adapters/`, чтобы он реализовывал этот интерфейс. Обновить зависимости компонентов, проверяющих состояние системы (например, `/health` endpoint).
