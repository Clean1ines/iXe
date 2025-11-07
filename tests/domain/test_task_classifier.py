import pytest
from unittest.mock import Mock
from domain.services.task_classifier import TaskClassificationService, TaskClassificationResult
from utils.task_number_inferer import TaskNumberInferer


class TestTaskClassificationService:
    """Unit tests for TaskClassificationService."""

    @pytest.fixture
    def mock_task_inferer(self):
        """Create a mock TaskNumberInferer."""
        return Mock(spec=TaskNumberInferer)

    @pytest.fixture
    def task_classifier(self, mock_task_inferer):
        """Create a TaskClassificationService instance with mocked dependencies."""
        return TaskClassificationService(task_inferer=mock_task_inferer)

    def test_classify_task_calls_inferer(self, task_classifier, mock_task_inferer):
        """Test that classify_task calls the underlying inferer."""
        kes_codes = ["1.1", "2.3"]
        kos_codes = ["4.5"]
        answer_type = "short"
        
        mock_task_inferer.infer.return_value = 5
        
        result = task_classifier.classify_task(kes_codes, kos_codes, answer_type)
        
        mock_task_inferer.infer.assert_called_once_with(kes_codes, answer_type)
        assert result.task_number == 5

    def test_classify_task_basic_difficulty(self, task_classifier, mock_task_inferer):
        """Test that difficulty is set correctly for basic tasks."""
        mock_task_inferer.infer.return_value = 7  # Basic task
        
        result = task_classifier.classify_task(["1.1"], ["2.1"], "short")
        
        assert result.difficulty_level == "basic"
        assert result.max_score == 1

    def test_classify_task_advanced_difficulty(self, task_classifier, mock_task_inferer):
        """Test that difficulty is set correctly for advanced tasks."""
        mock_task_inferer.infer.return_value = 15  # Advanced task
        
        result = task_classifier.classify_task(["1.1"], ["2.1"], "extended")
        
        assert result.difficulty_level == "advanced"
        assert result.max_score == 2

    def test_classify_task_none_result(self, task_classifier, mock_task_inferer):
        """Test behavior when inferer returns None."""
        mock_task_inferer.infer.return_value = None
        
        result = task_classifier.classify_task(["1.1"], ["2.1"], "short")
        
        assert result.task_number == 0
        assert result.difficulty_level == "basic"  # 0 <= 12
        assert result.max_score == 1  # 0 <= 12
