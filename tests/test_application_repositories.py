"""
Unit tests for application repository implementations.

These tests verify that the repository implementations correctly
adapt domain interfaces to infrastructure concerns.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from domain.models.problem import Problem
from domain.models.user_progress import UserProgress, ProgressStatus
from domain.models.skill import Skill
from domain.value_objects.problem_id import ProblemId
from domain.value_objects.difficulty_level import DifficultyLevel, DifficultyLevelEnum
from domain.value_objects.problem_type import ProblemType, ProblemTypeEnum
from application.repositories.problem_repository_impl import ProblemRepositoryImpl
from application.repositories.user_progress_repository_impl import UserProgressRepositoryImpl
from application.repositories.skill_repository_impl import SkillRepositoryImpl
from infrastructure.adapters.database_adapter import DatabaseAdapter


class TestProblemRepositoryImpl:
    """Test cases for ProblemRepositoryImpl."""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """Create a mock database adapter."""
        return AsyncMock(spec=DatabaseAdapter)
    
    @pytest.fixture
    def problem_repository(self, mock_db_adapter):
        """Create a problem repository instance."""
        return ProblemRepositoryImpl(mock_db_adapter)
    
    @pytest.mark.asyncio
    async def test_save_problem(self, problem_repository, mock_db_adapter):
        """Test saving a problem domain entity."""
        # Create a domain problem
        problem_id = ProblemId(value="math_1_2024_1")
        problem = Problem(
            problem_id=problem_id,
            subject="mathematics",
            problem_type=ProblemType(ProblemTypeEnum.NUMBER),
            text="Solve the equation",
            difficulty_level=DifficultyLevel(DifficultyLevelEnum.BASIC),
            exam_part="Part 1",
            max_score=1
        )
        
        # Call save method
        await problem_repository.save(problem)
        
        # Verify that the database adapter's save method was called
        mock_db_adapter.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, problem_repository, mock_db_adapter):
        """Test retrieving a problem by ID."""
        problem_id = ProblemId(value="math_1_2024_1")
        # Create a mock database problem with proper attributes
        mock_db_problem = MagicMock()
        mock_db_problem.problem_id = "math_1_2024_1"
        mock_db_problem.subject = "mathematics"
        mock_db_problem.type = "number"
        mock_db_problem.text = "Solve the equation"
        mock_db_problem.difficulty_level = "basic"
        mock_db_problem.exam_part = "Part 1"
        mock_db_problem.max_score = 1
        mock_db_problem.options = None
        mock_db_problem.answer = None
        mock_db_problem.solutions = None
        mock_db_problem.kes_codes = []
        mock_db_problem.skills = None
        mock_db_problem.task_number = 1
        mock_db_problem.kos_codes = []
        mock_db_problem.form_id = None
        mock_db_problem.source_url = None
        mock_db_problem.raw_html_path = None
        mock_db_problem.created_at = None
        mock_db_problem.updated_at = None
        mock_db_problem.metadata = None
        
        mock_db_adapter.get_by_id = AsyncMock(return_value=mock_db_problem)
        
        result = await problem_repository.get_by_id(problem_id)
        
        mock_db_adapter.get_by_id.assert_called_once_with(problem_id)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_get_by_subject(self, problem_repository, mock_db_adapter):
        """Test retrieving problems by subject."""
        subject = "mathematics"
        # Create mock database problems with proper attributes
        mock_db_problem1 = MagicMock()
        mock_db_problem1.problem_id = "math_1_2024_1"
        mock_db_problem1.subject = "mathematics"
        mock_db_problem1.type = "number"
        mock_db_problem1.text = "Solve the equation"
        mock_db_problem1.difficulty_level = "basic"
        mock_db_problem1.exam_part = "Part 1"
        mock_db_problem1.max_score = 1
        mock_db_problem1.options = None
        mock_db_problem1.answer = None
        mock_db_problem1.solutions = None
        mock_db_problem1.kes_codes = []
        mock_db_problem1.skills = None
        mock_db_problem1.task_number = 1
        mock_db_problem1.kos_codes = []
        mock_db_problem1.form_id = None
        mock_db_problem1.source_url = None
        mock_db_problem1.raw_html_path = None
        mock_db_problem1.created_at = None
        mock_db_problem1.updated_at = None
        mock_db_problem1.metadata = None
        
        mock_db_problem2 = MagicMock()
        mock_db_problem2.problem_id = "math_2_2024_2"
        mock_db_problem2.subject = "mathematics"
        mock_db_problem2.type = "text"
        mock_db_problem2.text = "Explain the concept"
        mock_db_problem2.difficulty_level = "intermediate"
        mock_db_problem2.exam_part = "Part 2"
        mock_db_problem2.max_score = 2
        mock_db_problem2.options = None
        mock_db_problem2.answer = None
        mock_db_problem2.solutions = None
        mock_db_problem2.kes_codes = []
        mock_db_problem2.skills = None
        mock_db_problem2.task_number = 2
        mock_db_problem2.kos_codes = []
        mock_db_problem2.form_id = None
        mock_db_problem2.source_url = None
        mock_db_problem2.raw_html_path = None
        mock_db_problem2.created_at = None
        mock_db_problem2.updated_at = None
        mock_db_problem2.metadata = None
        
        expected_problems = [mock_db_problem1, mock_db_problem2]
        mock_db_adapter.get_by_subject = AsyncMock(return_value=expected_problems)
        
        result = await problem_repository.get_by_subject(subject)
        
        mock_db_adapter.get_by_subject.assert_called_once_with(subject)
        assert len(result) == 2


class TestUserProgressRepositoryImpl:
    """Test cases for UserProgressRepositoryImpl."""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """Create a mock database adapter."""
        return AsyncMock(spec=DatabaseAdapter)
    
    @pytest.fixture
    def user_progress_repository(self, mock_db_adapter):
        """Create a user progress repository instance."""
        return UserProgressRepositoryImpl(mock_db_adapter)
    
    @pytest.mark.asyncio
    async def test_save_user_progress(self, user_progress_repository, mock_db_adapter):
        """Test saving user progress."""
        problem_id = ProblemId(value="math_1_2024_1")
        progress = UserProgress(
            user_id="user123",
            problem_id=problem_id,
            status=ProgressStatus.NOT_STARTED
        )
        
        await user_progress_repository.save(progress)
        
        mock_db_adapter.save_user_progress.assert_called_once_with(progress)
    
    @pytest.mark.asyncio
    async def test_get_by_user_and_problem(self, user_progress_repository, mock_db_adapter):
        """Test retrieving user progress by user and problem."""
        user_id = "user123"
        problem_id = ProblemId(value="math_1_2024_1")
        expected_progress = MagicMock()
        mock_db_adapter.get_user_progress_by_user_and_problem = AsyncMock(return_value=expected_progress)
        
        result = await user_progress_repository.get_by_user_and_problem(user_id, problem_id)
        
        mock_db_adapter.get_user_progress_by_user_and_problem.assert_called_once_with(
            user_id, str(problem_id)
        )
        assert result == expected_progress


class TestSkillRepositoryImpl:
    """Test cases for SkillRepositoryImpl."""
    
    @pytest.fixture
    def mock_db_adapter(self):
        """Create a mock database adapter."""
        return AsyncMock(spec=DatabaseAdapter)
    
    @pytest.fixture
    def skill_repository(self, mock_db_adapter):
        """Create a skill repository instance."""
        return SkillRepositoryImpl(mock_db_adapter)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, skill_repository, mock_db_adapter):
        """Test retrieving a skill by ID."""
        skill_id = "algebra_basic"
        expected_skill = MagicMock()
        mock_db_adapter.get_skill_by_id = AsyncMock(return_value=expected_skill)
        
        result = await skill_repository.get_by_id(skill_id)
        
        mock_db_adapter.get_skill_by_id.assert_called_once_with(skill_id)
        assert result == expected_skill
