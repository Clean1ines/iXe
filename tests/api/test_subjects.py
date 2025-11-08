# tests/api/test_subjects.py
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api.app import create_app
from infrastructure.adapters.database_adapter import DatabaseAdapter

# --- Импорт зависимостей ДО функций ---
from api.dependencies import get_db_manager
# ------------------------------------

def test_get_available_subjects_success():
    """
    1. Получение списка доступных предметов (/api/subjects/available)
    Описание: Проверить, что эндпоинт возвращает корректный список предметов.
    Шаги:
    1. Вызвать GET /api/subjects/available.
    2. Проверить статус-код 200.
    3. Проверить, что тело ответа содержит ожидаемый список предметов (например, ["mathematics", "informatics", "russian"]).
    Ожидаемый результат: Успешный ответ с корректным списком.
    """
    app = create_app()
    client = TestClient(app)

    mock_db = Mock(spec=DatabaseAdapter)
    # Используем реальные объекты Problem с атрибутом subject
    from models.problem_schema import Problem
    from datetime import datetime
    mock_db.get_all_problems.return_value = [
        Problem(
            problem_id="1", subject="mathematics", type="type1", text="text1",
            answer="ans1", topics=["t1"], difficulty_level="easy", task_number=1,
            kes_codes=["k1"], kos_codes=["ko1"], exam_part="part1", max_score=1,
            created_at=datetime.now()
        ),
        Problem(
            problem_id="2", subject="informatics", type="type2", text="text2",
            answer="ans2", topics=["t2"], difficulty_level="easy", task_number=2,
            kes_codes=["k2"], kos_codes=["ko2"], exam_part="part1", max_score=1,
            created_at=datetime.now()
        ),
        Problem(
            problem_id="3", subject="mathematics", type="type3", text="text3",
            answer="ans3", topics=["t3"], difficulty_level="easy", task_number=3,
            kes_codes=["k3"], kos_codes=["ko3"], exam_part="part1", max_score=1,
            created_at=datetime.now()
        ),  # дубликат для проверки set
        Problem(
            problem_id="4", subject="russian", type="type4", text="text4",
            answer="ans4", topics=["t4"], difficulty_level="easy", task_number=4,
            kes_codes=["k4"], kos_codes=["ko4"], exam_part="part1", max_score=1,
            created_at=datetime.now()
        ),
    ]
    expected_subjects = ["mathematics", "informatics", "russian"]

    app.dependency_overrides[get_db_manager] = lambda: mock_db
    response = client.get("/api/subjects/available")
    app.dependency_overrides.pop(get_db_manager, None)

    assert response.status_code == 200
    data = response.json()
    # Сортируем списки для надёжного сравнения
    assert sorted(data["subjects"]) == sorted(expected_subjects)

def test_get_available_subjects_error():
    """
    9. Обработка внутренней ошибки сервера
    Описание: Проверить, что непредвиденные ошибки в сервисах или эндпоинтах корректно обрабатываются
    и не возвращают трейсbacks клиенту.
    Шаги:
    1. Подготовить мок/заглушку, чтобы какая-либо внутренняя функция (например, db.get_all_problems() в QuizService)
       выбрасывала общее исключение Exception.
    2. Вызвать эндпоинт, который использует эту функцию (например, GET /api/subjects/available).
    3. Проверить статус-код 500 (Internal Server Error).
    4. Проверить, что тело ответа содержит общее сообщение об ошибке (например, {"detail": "Internal server error"}),
       а не трейсбэк.
    Ожидаемый результат: Сервер возвращает 500 с общим сообщением об ошибке.
    """
    app = create_app()
    client = TestClient(app)

    mock_db = Mock(spec=DatabaseAdapter)
    mock_db.get_all_problems.side_effect = Exception("Database error")

    app.dependency_overrides[get_db_manager] = lambda: mock_db
    response = client.get("/api/subjects/available")
    app.dependency_overrides.pop(get_db_manager, None)

    assert response.status_code == 500
    data = response.json()
    assert data == {"detail": "Internal error"}

# Импорт уже в начале файла
