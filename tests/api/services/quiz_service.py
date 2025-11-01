# tests/api/services/test_quiz_service.py
import pytest
from unittest.mock import Mock, patch
from api.services.quiz_service import QuizService
from api.schemas import StartQuizRequest, StartQuizResponse, QuizItem

class TestQuizService:

    @pytest.fixture
    def mock_dependencies(self):
        """Fixture to create mock dependencies."""
        db_mock = Mock()
        retriever_mock = Mock()
        skill_graph_mock = Mock()
        spec_service_mock = Mock()
        return db_mock, retriever_mock, skill_graph_mock, spec_service_mock

    @pytest.fixture
    def quiz_service(self, mock_dependencies):
        """Fixture to create an instance of QuizService."""
        db_mock, retriever_mock, skill_graph_mock, spec_service_mock = mock_dependencies
        return QuizService(db_mock, retriever_mock, skill_graph_mock, spec_service_mock)

    def test_initialization(self, mock_dependencies):
        """Test that the service is initialized correctly."""
        db_mock, retriever_mock, skill_graph_mock, spec_service_mock = mock_dependencies

        service = QuizService(db_mock, retriever_mock, skill_graph_mock, spec_service_mock)

        assert service.db is db_mock
        assert service.retriever is retriever_mock
        assert service.skill_graph is skill_graph_mock
        assert service.spec_service is spec_service_mock

    def test_start_quiz_calls_get_all_problems(self, quiz_service):
        """Test that db.get_all_problems is called in start_quiz."""
        quiz_service.db.get_all_problems.return_value = []

        request = StartQuizRequest(page_name="math", user_id="user123", strategy="adaptive")
        quiz_service.start_quiz(request)

        quiz_service.db.get_all_problems.assert_called_once()

    @patch('api.services.quiz_service.uuid')
    def test_start_quiz_generates_correct_quiz_id(self, mock_uuid, quiz_service):
        """Test that quiz_id is generated with the correct format."""
        # uuid.uuid4().hex[:8] takes the first 8 characters
        mock_uuid.uuid4.return_value.hex = 'abcdef1234567890abcdef1234567890'
        quiz_service.db.get_all_problems.return_value = [] # Does not call _select_problems_by_strategy if no problems
        quiz_service._select_problems_by_strategy = Mock(return_value=[]) # Mock problem selection

        request = StartQuizRequest(page_name="math", user_id="user123", strategy="calibration")
        response = quiz_service.start_quiz(request)

        # CORRECTED: Expect quiz_id to be "quiz_calibration_abcdef12" (first 8 chars of UUID)
        assert response.quiz_id == "quiz_calibration_abcdef12"

    def test_start_quiz_calls_select_problems_by_strategy(self, quiz_service):
        """Test that _select_problems_by_strategy is called in start_quiz."""
        mock_problems = [Mock(), Mock()]
        quiz_service.db.get_all_problems.return_value = mock_problems
        quiz_service._select_problems_by_strategy = Mock(return_value=[])

        request = StartQuizRequest(page_name="math", user_id="user123", strategy="adaptive")
        quiz_service.start_quiz(request)

        quiz_service._select_problems_by_strategy.assert_called_once_with(request, mock_problems)

    def test_start_quiz_returns_response_with_items(self, quiz_service):
        """Test that StartQuizResponse with items is returned."""
        mock_problems = [Mock(problem_id="math_1", subject="math", topics=["topic1"], text="Question 1", offline_html=None, type="type1")]
        quiz_service.db.get_all_problems.return_value = []
        quiz_service._select_problems_by_strategy = Mock(return_value=mock_problems)

        request = StartQuizRequest(page_name="math", user_id="user123", strategy="adaptive")
        response = quiz_service.start_quiz(request)

        assert isinstance(response, StartQuizResponse)
        assert hasattr(response, 'items')
        # Check that items is not empty if problems were selected
        assert len(response.items) == 1
        assert isinstance(response.items[0], QuizItem)

    def test_select_problems_by_strategy_calls_correct_method(self, quiz_service):
        """Test that the appropriate internal strategy method is called."""
        # Mock internal strategy methods
        calibration_mock = Mock(return_value=[])
        adaptive_mock = Mock(return_value=[])
        final_mock = Mock(return_value=[])

        quiz_service._get_calibration_problems = calibration_mock
        quiz_service._get_adaptive_problems = adaptive_mock
        quiz_service._get_final_problems = final_mock

        all_problems = [Mock()]

        # Test for calibration
        request_calibration = StartQuizRequest(page_name="math", user_id="user123", strategy="calibration")
        quiz_service._select_problems_by_strategy(request_calibration, all_problems)
        calibration_mock.assert_called_once_with("math", all_problems)
        adaptive_mock.assert_not_called()
        final_mock.assert_not_called()

        # Reset mocks for next test
        calibration_mock.reset_mock()
        adaptive_mock.reset_mock()
        final_mock.reset_mock()

        # Test for adaptive
        request_adaptive = StartQuizRequest(page_name="math", user_id="user123", strategy="adaptive")
        quiz_service._select_problems_by_strategy(request_adaptive, all_problems)
        adaptive_mock.assert_called_once_with("user123", "math", all_problems)
        calibration_mock.assert_not_called()
        final_mock.assert_not_called()

        # Reset mocks for next test
        calibration_mock.reset_mock()
        adaptive_mock.reset_mock()
        final_mock.reset_mock()

        # Test for final
        request_final = StartQuizRequest(page_name="math", user_id="user123", strategy="final")
        quiz_service._select_problems_by_strategy(request_final, all_problems)
        final_mock.assert_called_once_with("user123", "math", all_problems)
        calibration_mock.assert_not_called()
        adaptive_mock.assert_not_called()

    def test_select_problems_by_strategy_returns_strategy_result(self, quiz_service):
        """Test that the value from the internal strategy method is returned."""
        expected_problems = [Mock(), Mock()]
        quiz_service._get_calibration_problems = Mock(return_value=expected_problems)
        all_problems = [Mock()]

        request = StartQuizRequest(page_name="math", user_id="user123", strategy="calibration")
        result = quiz_service._select_problems_by_strategy(request, all_problems)

        assert result == expected_problems
