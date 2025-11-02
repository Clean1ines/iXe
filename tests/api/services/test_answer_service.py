import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from api.services.answer_service import AnswerService
from api.schemas import CheckAnswerRequest, Feedback


class TestAnswerService:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_checker(self):
        return AsyncMock()

    @pytest.fixture
    def mock_storage(self):
        return MagicMock()

    @pytest.fixture
    def mock_skill_graph(self):
        return MagicMock()

    @pytest.fixture
    def mock_spec_service(self):
        return MagicMock()

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
    async def test_check_answer_cache_hit(self, answer_service, mock_db, mock_storage, mock_spec_service, mock_checker):
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1, subject="math")
        mock_storage.get_answer_and_status.return_value = ("42", "correct")
        expected_feedback = Feedback(kos_explanation="Correct explanation", kes_topics=["Topic 1"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback

        response = await answer_service.check_answer(request)

        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == "From cache"
        assert response.feedback == expected_feedback
        mock_checker.check_answer.assert_not_called()

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_check_answer_cache_miss_correct(
        self, mock_extract, answer_service, mock_db, mock_storage, mock_checker, mock_spec_service
    ):
        mock_extract.return_value = ("123", "form1")
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1, subject="math")
        mock_storage.get_answer_and_status.return_value = (None, None)
        mock_checker.check_answer.return_value = {"status": "correct", "message": "Correct!"}
        expected_feedback = Feedback(kos_explanation="Correct explanation", kes_topics=["Topic 1"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback

        response = await answer_service.check_answer(request)

        assert response.verdict == "correct"
        assert response.score_float == 1.0
        assert response.short_hint == "Correct!"
        assert response.feedback == expected_feedback
        mock_checker.check_answer.assert_awaited_once_with("123", "form1", "42", "math")
        mock_storage.save_answer_and_status.assert_called_once_with("123", "42", "correct")

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_check_answer_cache_miss_incorrect_with_recommendations(
        self, mock_extract, answer_service, mock_db, mock_storage, mock_checker, mock_skill_graph, mock_spec_service
    ):
        mock_extract.return_value = ("123", "form1")
        request = CheckAnswerRequest(problem_id="123", user_answer="41", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=5, subject="math")
        mock_storage.get_answer_and_status.return_value = (None, None)
        mock_checker.check_answer.return_value = {"status": "incorrect", "message": "Try again."}
        mock_skill_graph.get_codes_for_task.return_value = ["skill_A", "skill_B"]
        mock_skill_graph.skill_descriptions = {"skill_A": "Algebra Basics", "skill_B": "Linear Equations"}
        mock_spec_service.get_task_spec.return_value = {"description": "Solving Linear Equations in One Variable"}
        initial_feedback = Feedback(kos_explanation="Incorrect, review concepts.", kes_topics=["Topic 5"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback

        response = await answer_service.check_answer(request)

        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert "Algebra Basics" in response.feedback.next_steps[0]
        mock_checker.check_answer.assert_awaited_once_with("123", "form1", "41", "math")
        mock_storage.save_answer_and_status.assert_called_once_with("123", "41", "incorrect")

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_check_answer_cache_miss_incorrect_no_recommendations(
        self, mock_extract, answer_service, mock_db, mock_storage, mock_checker, mock_skill_graph, mock_spec_service
    ):
        mock_extract.return_value = ("123", "form1")
        request = CheckAnswerRequest(problem_id="123", user_answer="41", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=5, subject="math")
        mock_storage.get_answer_and_status.return_value = (None, None)
        mock_checker.check_answer.return_value = {"status": "incorrect", "message": "Try again."}
        mock_skill_graph.get_codes_for_task.return_value = []
        initial_feedback = Feedback(kos_explanation="Incorrect, review concepts.", kes_topics=["Topic 5"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = initial_feedback

        response = await answer_service.check_answer(request)

        assert response.verdict == "incorrect"
        assert response.score_float == 0.0
        assert response.feedback.next_steps == []
        mock_checker.check_answer.assert_awaited_once_with("123", "form1", "41", "math")
        mock_storage.save_answer_and_status.assert_called_once_with("123", "41", "incorrect")

    @pytest.mark.asyncio
    async def test_check_answer_problem_not_found(self, answer_service, mock_db):
        request = CheckAnswerRequest(problem_id="nonexistent", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = None

        with pytest.raises(HTTPException) as exc:
            await answer_service.check_answer(request)
        assert exc.value.status_code == 404
        assert exc.value.detail == "Problem not found in database"

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_check_answer_external_checker_error(
        self, mock_extract, answer_service, mock_db, mock_storage, mock_checker
    ):
        mock_extract.return_value = ("123", "form1")
        request = CheckAnswerRequest(problem_id="123", user_answer="42", form_id="form1")
        mock_db.get_problem_by_id.return_value = MagicMock(task_number=1, subject="math")
        mock_storage.get_answer_and_status.return_value = (None, None)
        mock_checker.check_answer.side_effect = Exception("Network error")

        with pytest.raises(HTTPException) as exc:
            await answer_service.check_answer(request)
        assert exc.value.status_code == 502
        assert exc.value.detail == "Error checking answer with external service"

    @pytest.mark.asyncio
    async def test_check_cache_hit_correct(self, answer_service, mock_storage, mock_spec_service):
        mock_storage.get_answer_and_status.return_value = ("42", "correct")
        expected_feedback = Feedback(kos_explanation="Correct explanation", kes_topics=["Topic 1"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = expected_feedback

        response = await answer_service._check_cache("123", 1)
        assert response is not None
        assert response.verdict == "correct"

    @pytest.mark.asyncio
    async def test_check_cache_miss(self, answer_service, mock_storage):
        mock_storage.get_answer_and_status.return_value = (None, None)
        response = await answer_service._check_cache("123", 1)
        assert response is None

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_call_external_checker_success(self, mock_extract, answer_service, mock_checker):
        mock_extract.return_value = ("123", "form1")
        mock_checker.check_answer.return_value = {"status": "correct", "message": "Correct!"}
        verdict, msg = await answer_service._call_external_checker("123", "42", "math")
        assert verdict == "correct"
        assert msg == "Correct!"
        mock_checker.check_answer.assert_awaited_once_with("123", "form1", "42", "math")

    @pytest.mark.asyncio
    @patch("api.services.answer_service.extract_task_id_and_form_id")
    async def test_call_external_checker_error(self, mock_extract, answer_service, mock_checker):
        mock_extract.return_value = ("123", "form1")
        mock_checker.check_answer.side_effect = Exception("Fail")
        with pytest.raises(HTTPException) as exc:
            await answer_service._call_external_checker("123", "42", "math")
        assert exc.value.status_code == 502

    @pytest.mark.asyncio
    async def test_save_result_with_storage(self, answer_service, mock_storage):
        await answer_service._save_result("123", "42", "correct")
        mock_storage.save_answer_and_status.assert_called_once_with("123", "42", "correct")

    @pytest.mark.asyncio
    async def test_save_result_no_storage(self, answer_service):
        answer_service.storage = None
        await answer_service._save_result("123", "42", "correct")

    @pytest.mark.asyncio
    async def test_generate_feedback_correct(self, answer_service, mock_spec_service):
        expected = Feedback(kos_explanation="Correct explanation", kes_topics=["Topic 1"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = expected
        resp = await answer_service._generate_feedback(1, "correct", "OK", "42")
        assert resp.feedback == expected
        assert resp.feedback.next_steps == []

    @pytest.mark.asyncio
    async def test_generate_feedback_incorrect_with_recommendations(self, answer_service, mock_skill_graph, mock_spec_service):
        mock_skill_graph.get_codes_for_task.return_value = ["s1"]
        mock_skill_graph.skill_descriptions = {"s1": "Algebra Basics"}
        mock_spec_service.get_task_spec.return_value = {"description": "Solving Linear Equations"}
        initial = Feedback(kos_explanation="Incorrect, review.", kes_topics=["T5"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = initial

        resp = await answer_service._generate_feedback(5, "incorrect", "No", "41")
        assert "Algebra Basics" in resp.feedback.next_steps[0]

    @pytest.mark.asyncio
    async def test_generate_feedback_incorrect_no_recommendations(self, answer_service, mock_skill_graph, mock_spec_service):
        mock_skill_graph.get_codes_for_task.return_value = []
        initial = Feedback(kos_explanation="Incorrect, review.", kes_topics=["T5"], next_steps=[])
        mock_spec_service.get_feedback_for_task.return_value = initial

        resp = await answer_service._generate_feedback(5, "incorrect", "No", "41")
        assert resp.feedback.next_steps == []
