# tests/api/test_quiz.py
from fastapi.testclient import TestClient
from unittest.mock import Mock
from api.app import create_app
from api.services.quiz_service import QuizService
from api.dependencies import get_quiz_service
from models.problem_schema import Problem
from datetime import datetime

def test_start_quiz_success():
    app = create_app()

    # Подготовка mock-данных (не используется напрямую в этом тесте, так как мокается сервис)
    # mock_problem = Problem(
    #     problem_id="test_123",
    #     subject="mathematics",
    #     text="What is 2+2?",
    #     topics=["algebra"],
    #     type="text",
    #     answer="4",
    #     difficulty_level="easy",
    #     task_number=1,
    #     kes_codes=[],
    #     kos_codes=[],
    #     exam_part="part1",
    #     max_score=1,
    #     form_id="form123",
    #     source_url="http://example.com",
    #     raw_html_path="path/to/html",
    #     created_at=datetime.now(), # <-- Передаём корректный datetime
    #     metadata={}
    # )
    mock_service = Mock(spec=QuizService)
    # Возвращаем объект Pydantic, а не словарь, чтобы соответствовать ожиданиям сервиса
    from api.schemas import StartQuizResponse, QuizItem
    mock_response = StartQuizResponse(
        quiz_id="daily_quiz_abc123", # Фиксированный ID для теста
        items=[
            QuizItem(
                problem_id="test_123",
                subject="mathematics",
                topic="algebra",
                prompt="What is 2+2?",
                choices_or_input_type="text_input"
            )
        ]
    )
    mock_service.start_quiz.return_value = mock_response

    # --- Ключевое изменение: используем dependency_overrides ---
    app.dependency_overrides[get_quiz_service] = lambda: mock_service
    # ----------------------------------------------------------

    client = TestClient(app)

    with client as c: # Используем контекстный менеджер для TestClient, если нужно
        response = c.post("/api/quiz/daily/start", json={"page_name": "mathematics"})

    # Убираем override после теста (хорошая практика)
    app.dependency_overrides.pop(get_quiz_service, None)

    assert response.status_code == 200
    data = response.json()
    # Проверяем, что quiz_id соответствует возвращаемому сервисом значению
    assert data["quiz_id"] == "daily_quiz_abc123"
    assert len(data["items"]) == 1
    assert data["items"][0]["problem_id"] == "test_123"
    # Можно добавить другие проверки на структуру, если нужно
    assert "subject" in data["items"][0]
    assert "prompt" in data["items"][0]
