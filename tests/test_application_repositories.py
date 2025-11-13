"""
Unit tests for application repository implementations.

These tests verify that the repository implementations correctly
adapt domain interfaces to infrastructure concerns following DDD principles.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from domain.models.problem import Problem
from domain.models.user_progress import UserProgress, ProgressStatus
from domain.models.skill import Skill
from domain.value_objects.problem_id import ProblemId
from domain.value_objects.difficulty_level import DifficultyLevel, DifficultyLevelEnum
from domain.value_objects.problem_type import ProblemType, ProblemTypeEnum
from domain.value_objects.problem_status import ProblemStatus, ProblemStatusEnum
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
            max_score=1,
            status=ProblemStatus(ProblemStatusEnum.DRAFT)
        )
        
        # Call save method
        await problem_repository.save(problem)
        
        # Verify that the database adapter's save method was called
        mock_db_adapter.save.assert_called_once_with(problem)
    
    @pytest.mark.asyncio
    async def test_get_by_id(self, problem_repository, mock_db_adapter):
        """Test retrieving a problem by ID."""
        problem_id = ProblemId(value="math_1_2024_1")
        # Create a mock database problem
        mock_db_problem = Problem(
            problem_id=problem_id,
            subject="mathematics",
            problem_type=ProblemType(ProblemTypeEnum.NUMBER),
            text="Solve the equation",
            difficulty_level=DifficultyLevel(DifficultyLevelEnum.BASIC),
            exam_part="Part 1",
            max_score=1,
            status=ProblemStatus(ProblemStatusEnum.DRAFT)
        )
        
        mock_db_adapter.get_by_id = AsyncMock(return_value=mock_db_problem)
        
        result = await problem_repository.get_by_id(problem_id)
        
        # Verify that get_by_id was called with string representation
        mock_db_adapter.get_by_id.assert_called_once_with("math_1_2024_1")
        assert result is not None
        assert result.problem_id.value == "math_1_2024_1"
    
    @pytest.mark.asyncio
    async def test_get_by_subject(self, problem_repository, mock_db_adapter):
        """Test retrieving problems by subject."""
        subject = "mathematics"
        # Create mock database problems
        problem_id1 = ProblemId(value="math_1_2024_1")
        problem_id2 = ProblemId(value="math_2_2024_2")
        
        mock_db_problem1 = Problem(
            problem_id=problem_id1,
            subject="mathematics",
            problem_type=ProblemType(ProblemTypeEnum.NUMBER),
            text="Solve the equation",
            difficulty_level=DifficultyLevel(DifficultyLevelEnum.BASIC),
            exam_part="Part 1",
            max_score=1,
            status=ProblemStatus(ProblemStatusEnum.DRAFT)
        )
        
        mock_db_problem2 = Problem(
            problem_id=problem_id2,
            subject="mathematics",
            problem_type=ProblemType(ProblemTypeEnum.TEXT),
            text="Explain the concept",
            difficulty_level=DifficultyLevel(DifficultyLevelEnum.INTERMEDIATE),
            exam_part="Part 2",
            max_score=2,
            status=ProblemStatus(ProblemStatusEnum.DRAFT)
        )
        
        expected_problems = [mock_db_problem1, mock_db_problem2]
        mock_db_adapter.get_by_subject = AsyncMock(return_value=expected_problems)
        
        result = await problem_repository.get_by_subject(subject)
        
        mock_db_adapter.get_by_subject.assert_called_once_with(subject)
        assert len(result) == 2
        assert result[0].subject == "mathematics"
        assert result[1].subject == "mathematics"


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
        
        # Create mock object with proper ProblemId conversion
        mock_db_progress = MagicMock()
        mock_db_progress.user_id = user_id
        mock_db_progress.problem_id = "math_1_2024_1"  # String, will be converted to ProblemId
        mock_db_progress.status = ProgressStatus.NOT_STARTED
        mock_db_progress.score = 0
        mock_db_progress.attempts = 0
        mock_db_progress.last_attempt_at = None
        mock_db_progress.started_at = datetime.now()
        
        mock_db_adapter.get_user_progress_by_user_and_problem = AsyncMock(return_value=mock_db_progress)
        
        result = await user_progress_repository.get_by_user_and_problem(user_id, problem_id)
        
        # Verify that call was made with correct arguments (string for problem_id)
        mock_db_adapter.get_user_progress_by_user_and_problem.assert_called_once_with(
            user_id, 
            "math_1_2024_1"  # String representation
        )
        
        assert result is not None
        assert result.user_id == "user123"
        assert result.problem_id.value == "math_1_2024_1"
        assert result.status == ProgressStatus.NOT_STARTED


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
        
        # Create mock object without created_at and updated_at fields
        mock_db_skill = MagicMock()
        mock_db_skill.skill_id = skill_id
        mock_db_skill.name = "Basic Algebra"
        mock_db_skill.description = "Fundamental algebra concepts"
        mock_db_skill.prerequisites = []
        mock_db_skill.related_problems = ["math_1_2024_1", "math_2_2024_2"]
        
        mock_db_adapter.get_skill_by_id = AsyncMock(return_value=mock_db_skill)
        
        result = await skill_repository.get_by_id(skill_id)
        
        mock_db_adapter.get_skill_by_id.assert_called_once_with(skill_id)
        assert result is not None
        assert result.skill_id == "algebra_basic"
        assert result.name == "Basic Algebra"
        assert result.description == "Fundamental algebra concepts"
        assert result.prerequisites == []
        # Ensure related_problems are converted to ProblemId objects
        assert len(result.related_problems) == 2
        assert result.related_problems[0].value == "math_1_2024_1"
        assert result.related_problems[1].value == "math_2_2024_2"
