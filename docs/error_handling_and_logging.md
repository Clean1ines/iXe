# Обработка ошибок и логирование

## Обзор

Этот документ описывает стратегию и реализацию обработки ошибок и логирования в проекте `FIPI Core API`.

## Цель

- Обеспечить централизованную, структурированную и наблюдаемую систему обработки ошибок и логирования.
- Упростить диагностику и устранение неполадок в системе.
- Обеспечить единообразие в обработке исключений на всех уровнях приложения.

## Иерархия исключений (domain/exceptions/)

Все бизнес- и инфраструктурные ошибки представлены через иерархию исключений, расположенную в `domain/exceptions/`.

- `BaseDomainException`: Базовый класс для всех доменных исключений.
  - `ValidationException`: Ошибки валидации входных данных.
  - `ResourceNotFoundException`: Ошибка, когда запрашиваемый ресурс не найден.
  - `BusinessRuleException`: Нарушение бизнес-правила.
  - `InfrastructureException`: Базовый класс для инфраструктурных ошибок.
    - `ExternalServiceException`: Ошибка при взаимодействии с внешним сервисом.
    - `ResourceUnavailableException`: Ресурс временно недоступен.

## Обработка исключений в FastAPI

В `api/app.py` определены глобальные обработчики исключений:

- `@app.exception_handler(HTTPException)`: Обрабатывает стандартные HTTP-исключения.
- `@app.exception_handler(BaseDomainException)`: Обрабатывает доменные исключения, возвращает структурированный JSON-ответ.
- `@app.exception_handler(Exception)`: Обрабатывает все прочие необработанные исключения.

## Структурированное логирование

### Конфигурация

- Используется `structlog`.
- Для продакшена: `JSONRenderer` с `format_exc_info` для полной трассировки исключений.
- Для разработки/тестов: `ConsoleRenderer` для удобочитаемого вывода.

### ObservabilityService (domain/services/observability_service.py)

Централизованный сервис для логирования:

- `log_info(message, context, trace_id)`: Логирование информационных сообщений.
- `log_error(message, exception, context, trace_id, alert)`: Логирование ошибок. Если `alert=True`, вызывает `AlertService`.
- `log_warning(message, context, trace_id)`: Логирование предупреждений.
- `log_metric(name, value, tags, trace_id)`: Логирование метрик (заглушка).
- `generate_trace_id()`: Генерация уникального Trace ID.

### Middleware для трейсинга

`api/middleware/logging_middleware.py` добавляет `Trace ID` к каждому запросу и логирует начало и завершение запроса с контекстом и временем выполнения.

## Алертинг

`domain/services/alert_service.py` предоставляет централизованный способ отправки уведомлений о критических событиях:

- `send_alert(type, message, details, severity)`: Базовый метод отправки алерта.
- `alert_on_exception(exc, context)`: Отправка алерта при возникновении исключения.
- `alert_resource_unavailable(resource_name, reason)`: Алерт о недоступности ресурса.
- `alert_external_service_failure(service_name, operation, error_details)`: Алерт о сбое внешнего сервиса.

## Health Checks

- `GET /api/health`: Проверяет статус основных зависимостей (БД, Qdrant, Browser Pool).
- `GET /api/health/browser-resources`: Проверяет статус пула браузерных ресурсов.

