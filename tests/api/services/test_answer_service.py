import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from api.services.answer_service import AnswerService
from api.schemas import CheckAnswerRequest, CheckAnswerResponse, Feedback # Импортируем Feedback


class TestAnswerService:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_checker(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage(self):
        return AsyncMock()

    @pytest.fixture
    def mock_skill_graph(self):
        return AsyncMock()

    @pytest.fixture
    def mock_spec_service(self):
        return AsyncMock()

    @pytest.fixture
    def answer_service(self, mock_db, mock_checker, mock_storage, mock_skill_graph, mock_spec_service):
        return AnswerService(
            db=mock_db,
            checker=mock_checker,
            storage=mock_storage,
            skill_graph=mock_skill_graph,
            spec_service=mock_spec_service
        )

    @pytest.mark.asyncio
    async def test_check_answer_cache_hit(self, answer_service, mock_db, mock_storage, mock_spec_service):
        # Arrange
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1)
        
        # Мокаем кэш
        mock_storage.get_answer_and_status.return_value = ("42", "correct")
        
        # Мокаем feedback как объект Pydantic модели Feedback с корректной структурой
        expected_feedback_obj = Feedback(
            kos_explanation="Correct explanation",
            kes_topics=["Topic 1"],
            next_steps=[] # Пустой список, если из кэша
        )
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback_obj

        # Act
        response = await answer_service.check_answer(request)

        # Assert
        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == "From cache"
        assert response.feedback == expected_feedback_obj
        mock_checker.check_answer.assert_not_called()  # Не должно вызываться при попадании в кэш

    @pytest.mark.asyncio
    async def test_check_answer_cache_miss_correct(self, answer_service, mock_db, mock_storage, mock_checker, mock_spec_service):
        # Arrange
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1)
        mock_storage.get_answer_and_status.return_value = (None, None)  # Кэш пуст
        mock_checker.check_answer.return_value = {"status": "correct", "message": "Correct!"}
        
        expected_feedback_obj = Feedback(
            kos_explanation="Correct explanation",
            kes_topics=["Topic 1"],
            next_steps=[]
        )
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback_obj

        # Act
        response = await answer_service.check_answer(request)

        # Assert
        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == "Correct!"
        assert response.feedback == expected_feedback_obj
        mock_storage.save_answer_and_status.assert_called_once_with("123", "42", "correct")

    @pytest.mark.asyncio
    async def test_check_answer_cache_miss_incorrect_with_recommendations(self, answer_service, mock_db, mock_storage, mock_checker, mock_skill_graph, mock_spec_service):
        # Arrange
        request = CheckAnswerRequest(problem_id="123", user_answer="41", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=5)
        mock_storage.get_answer_and_status.return_value = (None, None)  # Кэш пуст
        mock_checker.check_answer.return_value = {"status": "incorrect", "message": "Try again."}
        mock_skill_graph.get_prerequisites_for_task.return_value = ["skill_A", "skill_B"]
        mock_skill_graph.skill_descriptions = {"skill_A": "Algebra Basics", "skill_B": "Linear Equations"}
        task_spec = {"description": "Solving Linear Equations in One Variable"}
        mock_spec_service.get_task_spec.return_value = task_spec
        
        initial_feedback_obj = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[] # Пока пустой, будет обновлен
        )
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback_obj
        # Ожидаемый фидбек с next_steps
        expected_feedback_with_steps = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[
                "Повторите: Algebra Basics, Linear Equations",
                "Решите 2 задачи по теме 'Solving Linear Eq...'"
            ]
        )

        # Act
        response = await answer_service.check_answer(request)

        # Assert
        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert response.short_hint == "Try again."
        assert response.feedback == expected_feedback_with_steps
        mock_storage.save_answer_and_status.assert_called_once_with("123", "41", "incorrect")

    @pytest.mark.asyncio
    async def test_check_answer_cache_miss_incorrect_no_recommendations(self, answer_service, mock_db, mock_storage, mock_checker, mock_skill_graph, mock_spec_service):
        # Arrange
        request = CheckAnswerRequest(problem_id="123", user_answer="41", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=5)
        mock_storage.get_answer_and_status.return_value = (None, None)  # Кэш пуст
        mock_checker.check_answer.return_value = {"status": "incorrect", "message": "Try again."}
        mock_skill_graph.get_prerequisites_for_task.return_value = []  # Нет пререквизитов
        
        initial_feedback_obj = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[]
        )
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback_obj

        # Act
        response = await answer_service.check_answer(request)

        # Assert
        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert response.short_hint == "Try again."
        assert response.feedback == initial_feedback_obj # next_steps должно быть пустым списком
        assert response.feedback.next_steps == []
        mock_storage.save_answer_and_status.assert_called_once_with("123", "41", "incorrect")

    @pytest.mark.asyncio
    async def test_check_answer_problem_not_found(self, answer_service, mock_db):
        # Arrange
        request = CheckAnswerRequest(problem_id="nonexistent", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await answer_service.check_answer(request)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Problem not found in database"

    @pytest.mark.asyncio
    async def test_check_answer_external_checker_error(self, answer_service, mock_db, mock_storage, mock_checker):
        # Arrange
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1)
        mock_storage.get_answer_and_status.return_value = (None, None)  # Кэш пуст
        mock_checker.check_answer.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await answer_service.check_answer(request)
        assert exc_info.value.status_code == 502
        assert exc_info.value.detail == "Error checking answer with external service"

    @pytest.mark.asyncio
    async def test_check_cache_hit_correct(self, answer_service, mock_storage, mock_spec_service):
        # Arrange
        problem_id = "123"
        task_number = 1
        mock_storage.get_answer_and_status.return_value = ("42", "correct")
        expected_feedback_obj = Feedback(
            kos_explanation="Correct explanation",
            kes_topics=["Topic 1"],
            next_steps=[] # Пустой список, если из кэша
        )
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback_obj

        # Act
        response = await answer_service._check_cache(problem_id, task_number)

        # Assert
        assert response is not None
        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == "From cache"
        assert response.feedback == expected_feedback_obj

    @pytest.mark.asyncio
    async def test_check_cache_miss(self, answer_service, mock_storage):
        # Arrange
        problem_id = "123"
        task_number = 1
        mock_storage.get_answer_and_status.return_value = (None, None)

        # Act
        response = await answer_service._check_cache(problem_id, task_number)

        # Assert
        assert response is None

    @pytest.mark.asyncio
    async def test_call_external_checker_success(self, answer_service, mock_checker):
        # Arrange
        problem_id = "123"
        form_id = "form1"
        user_answer = "42"
        mock_checker.check_answer.return_value = {"status": "correct", "message": "Correct!"}

        # Act
        verdict, message = await answer_service._call_external_checker(problem_id, form_id, user_answer)

        # Assert
        assert verdict == "correct"
        assert message == "Correct!"

    @pytest.mark.asyncio
    async def test_call_external_checker_error(self, answer_service, mock_checker):
        # Arrange
        problem_id = "123"
        form_id = "form1"
        user_answer = "42"
        mock_checker.check_answer.side_effect = Exception("Network error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await answer_service._call_external_checker(problem_id, form_id, user_answer)
        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_save_result_with_storage(self, answer_service, mock_storage):
        # Arrange
        problem_id = "123"
        user_answer = "42"
        verdict = "correct"

        # Act
        await answer_service._save_result(problem_id, user_answer, verdict)

        # Assert
        mock_storage.save_answer_and_status.assert_called_once_with(problem_id, user_answer, verdict)

    @pytest.mark.asyncio
    async def test_save_result_no_storage(self, answer_service):
        # Arrange
        answer_service.storage = None  # Отключаем хранилище
        problem_id = "123"
        user_answer = "42"
        verdict = "correct"

        # Act
        await answer_service._save_result(problem_id, user_answer, verdict) # Не должно вызывать исключение

        # Assert
        # Никаких вызовов не должно быть, так как storage = None
        # Проверка на отсутствие вызова сложнее, можно просто проверить, что не упало с ошибкой

    @pytest.mark.asyncio
    async def test_generate_feedback_correct(self, answer_service, mock_spec_service):
        # Arrange
        task_number = 1
        verdict = "correct"
        message = "Correct!"
        user_answer = "42"
        expected_feedback_obj = Feedback(
            kos_explanation="Correct explanation",
            kes_topics=["Topic 1"],
            next_steps=[] # next_steps не должно быть для корректного ответа
        )
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback_obj

        # Act
        response = await answer_service._generate_feedback(task_number, verdict, message, user_answer)

        # Assert
        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == message
        assert response.feedback == expected_feedback_obj
        assert response.feedback.next_steps == [] # next_steps не должно быть для корректного ответа

    @pytest.mark.asyncio
    async def test_generate_feedback_incorrect_with_recommendations(self, answer_service, mock_skill_graph, mock_spec_service):
        # Arrange
        task_number = 5
        verdict = "incorrect"
        message = "Try again."
        user_answer = "41"
        mock_skill_graph.get_prerequisites_for_task.return_value = ["skill_A"]
        mock_skill_graph.skill_descriptions = {"skill_A": "Algebra Basics"}
        task_spec = {"description": "Solving Linear Equations"}
        mock_spec_service.get_task_spec.return_value = task_spec
        initial_feedback_obj = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[] # Пока пустой, будет обновлен
        )
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback_obj
        expected_feedback_with_steps = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[
                "Повторите: Algebra Basics",
                "Решите 2 задачи по теме 'Solving Linear Eq...'"
            ]
        )

        # Act
        response = await answer_service._generate_feedback(task_number, verdict, message, user_answer)

        # Assert
        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert response.short_hint == message
        assert response.feedback == expected_feedback_with_steps

    @pytest.mark.asyncio
    async def test_generate_feedback_incorrect_no_recommendations(self, answer_service, mock_skill_graph, mock_spec_service):
        # Arrange
        task_number = 5
        verdict = "incorrect"
        message = "Try again."
        user_answer = "41"
        mock_skill_graph.get_prerequisites_for_task.return_value = [] # Нет пререквизитов
        initial_feedback_obj = Feedback(
            kos_explanation="Incorrect, review concepts.",
            kes_topics=["Topic 5"],
            next_steps=[] # next_steps пустой
        )
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback_obj

        # Act
        response = await answer_service._generate_feedback(task_number, verdict, message, user_answer)

        # Assert
        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert response.short_hint == message
        assert response.feedback == initial_feedback_obj
        assert response.feedback.next_steps == [] # next_steps не должно быть, так как список пуст

