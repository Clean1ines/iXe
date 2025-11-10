# Глава 5: MVP Сценарий Пользователя - Шаг 1: Вход в PWA и Приветствие

## 5.1. Введение: Цель Шага 1

Шаг 1 пользовательского сценария MVP является отправной точкой взаимодействия пользователя с платформой iXe. Его цель - обеспечить положительный первый опыт, проинформировать пользователя о возможностях приложения и направить его к следующему логическому действию: выбору предмета ЕГЭ. В контексте архитектуры, этот шаг включает в себя как фронтенд (PWA), так и бэкенд (API), и служит демонстрацией корректной интеграции этих слоев.

## 5.2. Техническая реализация: Frontend (PWA)

### 5.2.1. Архитектура PWA

PWA (Progressive Web App) для iXe реализована с использованием современных фронтенд-технологий. В проекте присутствует директория `frontend/`, содержащая:
- **`src/`**: Исходный код (предположительно на TypeScript с использованием React, Vue, Angular или другого фреймворка, хотя конкретный фреймворк не указан в дереве).
- **`public/`**: Статические ресурсы, включая `manifest.json` для функций PWA.
- **`package.json`**: Зависимости и скрипты сборки (Vite, как видно из `vite.config.ts`).

PWA обеспечивает:
- **Установку на устройство**: Пользователь может добавить приложение на главный экран, как нативное приложение.
- **Оффлайн-функциональность**: Ограниченная работа без подключения к интернету (в MVP может быть минимальной).
- **Надежность и производительность**: Быстрая загрузка и плавное взаимодействие.

### 5.2.2. Компонент Приветствия

Компонент, отвечающий за приветственный экран, будет находиться в `frontend/src/pages/` (или аналогичной структуре). Его задачи:
- **Отображение приветствия**: Текст, логотип, краткое описание цели приложения ("Подготовка к ЕГЭ с помощью адаптивного ИИ").
- **Получение списка предметов**: Вызов API для получения доступных для подготовки предметов.
- **Обработка ошибок**: В случае сбоя при получении списка предметов, отображение понятного сообщения пользователю.
- **Навигация**: Предоставление кнопки или элемента интерфейса для перехода к экрану выбора предметов.

```typescript
// frontend/src/pages/GreetingPage.tsx (примерная структура)
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom'; // или аналогичный роутер
import { fetchAvailableSubjects } from '../api/subjects'; // Функция для вызова API
import { AvailableSubjectsResponse } from '../types'; // Импорт схемы

const GreetingPage: React.FC = () => {
  const [subjects, setSubjects] = useState<AvailableSubjectsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const loadSubjects = async () => {
      try {
        const data = await fetchAvailableSubjects(); // Вызов API
        setSubjects(data);
      } catch (err) {
        console.error('Error fetching subjects:', err);
        setError('Не удалось загрузить список предметов. Проверьте подключение.');
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, []);

  if (loading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка: {error}</div>;

  const handleSubjectSelection = () => {
    // Переход к экрану выбора предметов, передав полученные subject
    navigate('/select-subject', { state: { subjects } });
  };

  return (
    <div className="greeting-container">
      <h1>Добро пожаловать в iXe!</h1>
      <p>Ваш персональный помощник в подготовке к ЕГЭ.</p>
      <p>Выберите предмет, по которому хотите начать подготовку:</p>
      <button onClick={handleSubjectSelection}>
        Выбрать предмет
      </button>
    </div>
  );
};

export default GreetingPage;
```

### 5.2.3. Взаимодействие с API

Компонент `GreetingPage` использует функцию `fetchAvailableSubjects`, которая инкапсулирует вызов API:
- **URL**: `GET /subjects/available`
- **Метод**: GET
- **Заголовки**: Обычно `Content-Type: application/json`.
- **Ответ**: Ожидается `AvailableSubjectsResponse` из `api/schemas.py`.

## 5.3. Техническая реализация: Backend (FastAPI API)

### 5.3.1. Эндпоинт API

Эндпоинт, отвечающий за предоставление списка доступных предметов, определен в `api/endpoints/subjects.py`.

```python
# api/endpoints/subjects.py
from fastapi import APIRouter, Depends
from api.dependencies import get_subject_list_service # Предполагаемый сервис
from api.schemas import AvailableSubjectsResponse

router = APIRouter()

@router.get("/available", response_model=AvailableSubjectsResponse)
async def get_available_subjects(
    service = Depends(get_subject_list_service) # Инъекция сервиса
):
    """
    API endpoint to get the list of available subjects for preparation.
    This endpoint returns a list of subjects that the system currently supports.
    In MVP, this list is likely static or loaded from configuration/mapping files.
    """
    # Вызов метода сервиса прикладного уровня
    subjects = await service.get_available_subjects() # Подразумевается асинхронный вызов
    return AvailableSubjectsResponse(subjects=subjects)
```

### 5.3.2. Зависимости и Сервисы

Как видно из `api/dependencies.py`, FastAPI использует Dependency Injection (DI) для предоставления зависимостей, таких как `get_subject_list_service`. В MVP, сервис получения списка предметов может быть простым, например, оберткой вокруг утилиты `utils/subject_mapping.py`.

```python
# api/dependencies.py (фрагмент, добавлен сервис для примера)
# ... существующие зависимости ...
from utils.subject_mapping import get_available_subjects # Импорт утилиты
from services.subject_list_service import SubjectListService # Новый сервис

# Вспомогательная функция для получения статического списка
def get_static_subject_list():
    # Использует утилиту для получения маппинга subject_key -> official_name
    # Возвращает список, подходящий для AvailableSubjectsResponse
    available_mapping = get_available_subjects() # Метод из CLIScraper или утилиты
    return [{"key": k, "name": n} for k, n in available_mapping.items()]

# Сервис прикладного уровня (в папке services/)
class SubjectListService:
    async def get_available_subjects(self):
        # В MVP: просто возвращает статический список
        # В будущем: может интегрироваться с базой данных, проверять наличие задач и т.д.
        return get_static_subject_list()

def get_subject_list_service() -> SubjectListService:
    return SubjectListService()
```

### 5.3.3. Схемы данных

Схема ответа определена в `api/schemas.py` как `AvailableSubjectsResponse`.

```python
# api/schemas.py (фрагмент)
from pydantic import BaseModel
from typing import List

class SubjectItem(BaseModel): # Вспомогательная схема
    key: str
    name: str

class AvailableSubjectsResponse(BaseModel):
    subjects: List[SubjectItem] # или List[Dict[str, str]] в зависимости от точной спецификации
```

## 5.4. Интеграция и Архитектурные Соображения

### 5.4.1. Слой Представления (Frontend)

Frontend изолирован от деталей реализации бэкенда. Он знает только о схеме `AvailableSubjectsResponse` и URL эндпоинта. Это позволяет изменять бэкенд (например, добавлять логику проверки наличия задач) без изменений в фронтенде.

### 5.4.2. Слой Приложений (Backend Service)

`SubjectListService` (или его аналог в MVP) находится в слое приложений. В текущем MVP он может просто возвращать статический список, но его абстракция позволяет в будущем легко добавить сложную логику (например, проверку `IProblemRepository` на наличие задач для каждого предмета перед возвратом).

### 5.4.3. Слой Инфраструктуры (Dependencies)

`get_subject_list_service` в `dependencies.py` инкапсулирует создание и предоставление экземпляра `SubjectListService`, соблюдая принципы DI и упрощая тестирование API эндпоинтов.

## 5.5. Выводы

Шаг 1 ("Вход в PWA и Приветствие") кажется простым, но он закладывает фундамент для дальнейшего взаимодействия. Его реализация требует:
- **Фронтенд**: Создания компонента, отвечающего за приветствие и вызов API.
- **Бэкенд**: Создания эндпоинта, который предоставляет статический или динамический список предметов через сервис прикладного уровня.

Этот шаг демонстрирует, как принципы чистой архитектуры (слои, DI, абстракции) применяются даже на самых простых этапах MVP, обеспечивая гибкость и тестируемость.
