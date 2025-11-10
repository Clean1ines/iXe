# Глава 3: Рефакторинг "комка грязи" - Продолжение: Связь FIPIScraper и CLIScraper

## 3.9. Анализ `scripts/scrape_tasks.py` и его связи с `scraper/fipi_scraper.py`

После рефакторинга `FIPIScraper` мы не просто изолировали его внутреннюю сложность, мы также улучшили архитектуру точки входа, которая его использует. Рассмотрим `scripts/scrape_tasks.py`.

### 3.9.1. Текущая структура `CLIScraper`

Класс `CLIScraper` в `scripts/scrape_tasks.py` является точкой входа для скрапинга. Он отвечает за:
- **Конфигурацию CLI**: Взаимодействие с пользователем, выбор предметов.
- **Управление ресурсами**: Создание пула браузеров (`BrowserPoolManager`), баз данных (`DatabaseAdapter`).
- **Оркестрацию процесса**: Вызов `FIPIScraper` для конкретных страниц, обработка результатов, сохранение данных.

**Проблема**: `CLIScraper.scrape_subject_logic` тесно связан с `FIPIScraper`. Он создает все зависимости для `FIPIScraper` (спецификации, инферер задач и т.д.) и передает их внутрь. Это означает, что логика *создания* скрапера находится в `CLIScraper`, а не в самом `FIPIScraper` или в специализированной фабрике. Это нарушает инкапсуляцию и усложняет повторное использование `FIPIScraper`.

```python
# scripts/scrape_tasks.py (фрагмент)
# В scrape_subject_logic:
spec_service = SpecificationAdapter(spec_path, kes_kos_path)
task_inferer = TaskNumberInfererAdapter(spec_service)
scraper = FIPIScraper(
    base_url=config.FIPI_QUESTIONS_URL,
    browser_manager=browser_manager,
    subjects_url=config.FIPI_SUBJECTS_URL,
    spec_service=spec_service,
    task_inferer=task_inferer # Создание зависимостей в точке использования!
)
```

### 3.9.2. Применение DDD к `CLIScraper`

После рефакторинга `FIPIScraper` в `ScrapingOrchestrator` (из предыдущего раздела), `CLIScraper` становится *фасадом* для запуска скрапинга. Он управляет *контекстом* запуска (пользовательский ввод, пулы ресурсов), но не должен знать деталей *процесса скрапинга*.

```python
# scripts/scrape_tasks.py (обновленный фрагмент)
from application.services.scraping_orchestrator import ScrapingOrchestrator
from infrastructure.adapters.web_page_navigator import WebPageNavigatorAdapter
from infrastructure.adapters.web_content_extractor import WebContentExtractorAdapter
from domain.services.problem_factory import ProblemFactoryService
from infrastructure.adapters.arango_document_adapter import ArangoDocumentAdapter
from processors.page_processor import PageProcessingOrchestrator # Реализует IPageProcessor
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from infrastructure.adapters.task_number_inferer_adapter import TaskNumberInfererAdapter

async def scrape_subject_logic(self, ...):
    # Управление ресурсами (браузер, база данных) всё ещё здесь
    browser_manager = await browser_pool.get_available_browser()
    # ... инициализация db_manager ...

    try:
        # Создание зависимостей скрапинга (это можно вынести в фабрику!)
        spec_service = SpecificationAdapter(...) # Согласно логике из оригинала
        task_inferer = TaskNumberInfererAdapter(spec_service)
        # PageProcessingOrchestrator может быть настроенным фабричным методом
        page_processor = PageProcessingOrchestrator(
            html_processor=BlockProcessorAdapter(...) # с нужными адаптерами
        )
        navigator = WebPageNavigatorAdapter(browser_manager)
        extractor = WebContentExtractorAdapter()
        factory = ProblemFactoryService()
        repo = ArangoDocumentAdapter(...) # или любой другой IProblemRepository

        orchestrator = ScrapingOrchestrator(
            page_navigator=navigator,
            content_extractor=extractor,
            page_processor=page_processor,
            problem_factory=factory,
            problem_repo=repo
        )

        # Оркестрация процесса скрапинга страниц
        # Скрапим страницу "init"
        problems = await orchestrator.scrape_page(proj_id, "init", scraping_subject_key)
        for problem in problems:
            # Сохранение уже произошло внутри orchestrator через problem_repo
            total_saved += 1
            self.logger.info(f"Saved problem {problem.problem_id} to database")

        # Итеративный скрапинг страниц 1, 2, ...
        page_num = 1
        empty_count = 0
        max_empty = 2
        while True:
            # ... логика определения последней страницы ...
            if last_page_num is not None and page_num > last_page_num:
                break
            if last_page_num is None and empty_count >= max_empty:
                break

            problems = await orchestrator.scrape_page(proj_id, str(page_num), scraping_subject_key)
            if len(problems) == 0:
                empty_count += 1
            else:
                empty_count = 0
                for problem in problems:
                    # Сохранение уже произошло внутри orchestrator
                    total_saved += 1
                    self.logger.info(f"Saved problem {problem.problem_id} to database")
            page_num += 1

    finally:
        # Возврат ресурса в пул
        await browser_pool.return_browser(browser_manager)
```

### 3.9.3. Улучшения архитектуры

Теперь `CLIScraper`:
- **Сфокусирован на своей области ответственности**: CLI, управление ресурсами, оркестрация вызовов сервисов.
- **Изолирован от деталей процесса скрапинга**: Не знает, как именно происходит скрапинг, обработка HTML или создание `Problem`.
- **Более тестируем**: Легко мокать `ScrapingOrchestrator` и проверять, что `CLIScraper` правильно вызывает его методы.

`ScrapingOrchestrator`:
- **Сфокусирован на сценарии использования**: Скрапинг одной страницы.
- **Изолирован от контекста запуска**: Не зависит от CLI, пулов браузеров или пользовательского ввода.
- **Четко определенные зависимости**: Все зависимости инжектятся, легко заменить для тестирования.

## 3.10. Влияние на полиглотную персистентность

Рефакторинг `FIPIScraper` и `CLIScraper` напрямую поддерживает реализацию ADR о полиглотной персистентности.

- **Интерфейс `IProblemRepository`** позволяет легко заменить `ArangoDocumentAdapter` на `PostgreSQLAdapter` или любой другой адаптер для документов.
- **Интерфейс `IPageProcessor`** (`PageProcessingOrchestrator`) может быть расширен для индексации в Qdrant после создания `Problem`.
- **Сервис `ScrapingOrchestrator`** может быть легко расширен для вызова других сервисов (например, `IEventStore`) для логирования событий скрапинга.

## 3.11. Выводы

Рефакторинг `scraper/fipi_scraper.py` и его взаимодействия с `scripts/scrape_tasks.py` является ярким примером того, как принципы DDD и TDD могут улучшить архитектуру существующего кода:
- **Четкое разделение ответственностей** между компонентами.
- **Улучшенная тестируемость** за счет изоляции зависимостей.
- **Более гибкая архитектура**, готовая к изменениям (например, к полиглотной персистентности).
- **Соблюдение принципа инверсии зависимостей**: `CLIScraper` зависит от абстракции (`ScrapingOrchestrator`), а не от конкретной реализации `FIPIScraper`.

Этот процесс рефакторинга является итеративным и может быть продолжен для других "комков грязи" в проекте, постепенно приводя архитектуру к чистому, тестируемому и поддерживаемому состоянию.

