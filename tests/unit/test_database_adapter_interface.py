"""
Unit tests for DatabaseAdapter interface compliance.
Following industry best practices and minimal viable testing approach.
"""
import asyncio
import tempfile
import pytest
from pathlib import Path
from domain.interfaces.infrastructure_adapters import IDatabaseProvider
from domain.models.problem import Problem as DomainProblem
from domain.value_objects.problem_id import ProblemId
from domain.value_objects.problem_type import ProblemType, ProblemTypeEnum
from domain.value_objects.difficulty_level import DifficultyLevel, DifficultyLevelEnum
from domain.value_objects.problem_status import ProblemStatus, ProblemStatusEnum
from datetime import datetime
from infrastructure.adapters.database_adapter import DatabaseAdapter


class TestDatabaseAdapterInterfaceCompliance:
    """Test that DatabaseAdapter properly implements IDatabaseProvider interface."""

    def setup_method(self):
        """Setup method for each test."""
        self.temp_db_path = Path(tempfile.mktemp(suffix=".db"))
        self.db_adapter = DatabaseAdapter(str(self.temp_db_path))

    def teardown_method(self):
        """Teardown method for each test."""
        if self.temp_db_path.exists():
            self.temp_db_path.unlink()

    def test_implements_idatabase_provider(self):
        """Test that DatabaseAdapter implements IDatabaseProvider interface."""
        assert isinstance(self.db_adapter, IDatabaseProvider)

    def test_has_required_sync_methods(self):
        """Test that DatabaseAdapter has required synchronous methods."""
        assert hasattr(self.db_adapter, 'get_all_subjects')
        assert callable(getattr(self.db_adapter, 'get_all_subjects'))
        assert hasattr(self.db_adapter, 'get_random_problem_ids')
        assert callable(getattr(self.db_adapter, 'get_random_problem_ids'))

    def test_has_required_async_methods(self):
        """Test that DatabaseAdapter has required asynchronous methods."""
        import inspect
        assert hasattr(self.db_adapter, 'save_answer_status')
        assert inspect.iscoroutinefunction(self.db_adapter.save_answer_status)
        assert hasattr(self.db_adapter, 'get_answer_status')
        assert inspect.iscoroutinefunction(self.db_adapter.get_answer_status)
        assert hasattr(self.db_adapter, 'get_problem_by_id')
        assert inspect.iscoroutinefunction(self.db_adapter.get_problem_by_id)
        assert hasattr(self.db_adapter, 'save_problem')
        assert inspect.iscoroutinefunction(self.db_adapter.save_problem)

    def test_get_all_subjects_returns_list(self):
        """Test that get_all_subjects returns a list."""
        subjects = self.db_adapter.get_all_subjects()
        assert isinstance(subjects, list)

    def test_get_random_problem_ids_returns_list(self):
        """Test that get_random_problem_ids returns a list."""
        problem_ids = self.db_adapter.get_random_problem_ids("math", 5)
        assert isinstance(problem_ids, list)

    @pytest.mark.asyncio
    async def test_get_random_problem_ids_returns_requested_count(self):
        """Test that get_random_problem_ids returns requested number of IDs when possible."""
        # Add one problem for testing
        problem = DomainProblem(
            problem_id=ProblemId("math_1_2025_1"),
            subject="math",
            problem_type=ProblemType(ProblemTypeEnum.MULTIPLE_CHOICE),
            text="Test problem for count verification",
            difficulty_level=DifficultyLevel(DifficultyLevelEnum.BASIC),
            exam_part="Part 1",  # Correct value
            max_score=1,
            answer="A",
            options=["A", "B", "C", "D"],
            kes_codes=["KES1"],
            kos_codes=["KOS1"],
            task_number=1,
            form_id="form1",
            source_url="http://example.com",
            raw_html_path="/path/to/html",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )
    
        # Save the problem asynchronously
        await self.db_adapter.save_problem(problem)
    
        # Check that it returns the right number of IDs
        problem_ids = self.db_adapter.get_random_problem_ids("math", 1)
        assert len(problem_ids) == 1
        assert problem_ids[0] == "math_1_2025_1"
