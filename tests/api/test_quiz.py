# tests/api/test_quiz.py
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from api.app import create_app
from api.services.quiz_service import QuizService
from models.problem_schema import Problem

def test_start_quiz_success():
    app = create_app()
    client = TestClient(app)

    # Подготовка mock-данных
    mock_problem = Problem(
        problem_id="test_123",
        subject="mathematics",
        text="What is 2+2?",
        topics=["algebra"],
        type="text",
        answer="4",
        difficulty_level="easy",
        task_number=1,
        kes_codes=[],
        kos_codes=[],
        exam_part="part1",
        max_score=1,
        form_id="form123",
        source_url="http://example.com",
        raw_html_path="path/to/html",
        created_at=None,
        metadata={}
    )
    mock_service = Mock(spec=QuizService)
    mock_service.start_quiz.return_value = {
        "quiz_id": "daily_quiz_abc123",
        "items": [
            {
                "problem_id": "test_123",
                "subject": "mathematics",
                "topic": "algebra",
                "prompt": "What is 2+2?",
                "choices_or_input_type": "text_input"
            }
        ]
    }

    # Используем patch, чтобы внедрить mock в зависимость
    with patch('api.endpoints.quiz.get_quiz_service', return_value=mock_service):
        response = client.post("/api/quiz/daily/start", json={"page_name": "mathematics"})

    assert response.status_code == 200
    data = response.json()
    assert data["quiz_id"] == "daily_quiz_abc123"
    assert len(data["items"]) == 1
    assert data["items"][0]["problem_id"] == "test_123"
