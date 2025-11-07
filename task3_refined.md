### **Задача 3. Архитектурная реорганизация обработки HTML для соблюдения принципов чистой архитектуры**

**Контекст:**
Анализ текущего состояния показывает, что HTML-процессоры в `processors/` содержат бизнес-логику (KES/KOS коды, определение номера задания), нарушая границы слоев. Также используется `BeautifulSoup` напрямую в обработчиках, что затрудняет тестирование и поддержку.

**Цель:** 
Разделить слои ответственности, вынеся предметную логику в отдельный доменный слой, а HTML-обработку оставить на уровне инфраструктуры. Обеспечить соблюдение принципов чистой архитектуры и улучшить тестируемость.

**Текущее состояние (анализ):**
- `processors/block_processor.py` и `processors/page_processor.py` содержат бизнес-логику (task_number inferer, работа с KES/KOS)
- `utils/task_number_inferer.py` содержит логику сопоставления KES кодов с номерами заданий
- `utils/metadata_extractor.py` извлекает KES/KOS из HTML
- HTML-процессоры в `processors/html/` работают непосредственно с `BeautifulSoup`
- Существует `services/specification.py` - начало доменного слоя

**Требуемые действия:**

1.  **Создать доменную директорию и сервисы:**
    ```bash
    mkdir -p domain/services
    ```

2.  **Реализовать `domain/services/task_classifier.py`:**
    - `TaskClassificationService`: Интерфейс и реализация для классификации задач по KES/KOS кодам.
    - Метод `classify_task(kes_codes: List[str], kos_codes: List[str], answer_type: str) -> TaskClassificationResult`
    - Использовать существующую логику из `utils/task_number_inferer.py`, но вынести в доменный слой.

3.  **Реализовать `domain/services/answer_type_detector.py`:**
    - `AnswerTypeService`: Интерфейс и реализация для определения типа ответа.
    - Метод `detect_answer_type(html_content: str) -> str` (short, extended, multiple_choice, etc.)

4.  **Реализовать `domain/services/metadata_enhancer.py`:**
    - `MetadataExtractionService`: Интерфейс и реализация для извлечения и обогащения метаданных.
    - Метод `enhance_metadata(extracted_metadata: dict, spec_service: SpecificationService) -> dict`

5.  **Создать интерфейс для HTML-процессоров:**
    - В `processors/` создать `html_processor_interface.py`
    - Определить `IHTMLProcessor` с методом `process(content: str, context: ProcessingContext) -> ProcessingResult`

6.  **Рефакторить существующие HTML-процессоры:**
    - Все процессоры в `processors/html/` должны реализовывать `IHTMLProcessor`
    - Удалить из них любую логику, связанную с KES/KOS/номерами заданий
    - Оставить только трансформации HTML (изображения, ссылки, удаление элементов)

7.  **Создать pipeline обработки:**
    - В `processors/` создать `html_processing_pipeline.py`
    - Реализовать `HTMLProcessingPipeline` с этапами:
        - `AssetProcessingStage` (файлы, изображения)
        - `ContentExtractionStage` (извлечение текста, очистка)
        - `MetadataExtractionStage` (только извлечение, не бизнес-логика)
    - Этапы должны быть слабо связаны, использовать интерфейсы.

8.  **Обновить `BlockProcessor` и `PageProcessingOrchestrator`:**
    - Заменить прямые вызовы `task_inferer` на использование `TaskClassificationService`
    - Инъектировать доменные сервисы через конструктор
    - Использовать `HTMLProcessingPipeline` вместо прямого вызова HTML-процессоров

9.  **Обновить `ProblemBuilder`:**
    - Убедиться, что он использует данные от доменных сервисов, а не вычисляет их сам

10. **Добавить юнит-тесты:**
    - Для каждого доменного сервиса
    - Для каждого этапа pipeline
    - Для обновленных `BlockProcessor` и `PageProcessingOrchestrator`

**Acceptance Criteria:**
- [ ] Все бизнес-логика (KES/KOS -> task_number) вынесена в `domain/services`
- [ ] `BlockProcessor` и `PageProcessingOrchestrator` используют доменные сервисы
- [ ] Все HTML-процессоры реализуют `IHTMLProcessor`
- [ ] Создан `HTMLProcessingPipeline` с четкими этапами
- [ ] `task_number_inferer.py` реорганизован или заменен доменным сервисом
- [ ] Добавлены юнит-тесты для доменных сервисов (покрытие > 85%)
- [ ] Обновлены интеграционные тесты, учитывающие новую архитектуру
- [ ] Производительность обработки не ухудшена (или улучшена до 10%)
- [ ] Отсутствуют циклические зависимости между слоями (проверить mypy или анализатором)
- [ ] Код соответствует принципам Dependency Inversion Principle (DIP)

**Примечания:**
- Использовать DI-контейнер или ручную инъекцию зависимостей
- Убедиться, что `SpecificationService` доступен доменным сервисам через интерфейс
- Подумать о валидации данных на границах слоев (pydantic-модели)
