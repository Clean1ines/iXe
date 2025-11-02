import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from sqlalchemy import event
from sqlalchemy.engine import Engine
from models.problem_schema import Problem
from utils.database_manager import DatabaseManager
from utils.model_adapter import db_problem_to_problem


def create_sample_problem(problem_id: str, subject: str = "math", text: str = "Sample text"):
    """Helper to create a sample Problem instance for testing."""
    return Problem(
        problem_id=problem_id,
        subject=subject,
        type="test_type",
        text=text,
        options=[],
        answer="A",
        kes_codes=["K.1"],
        difficulty_level="1", # Было 1, стало строка
        task_number=1,
        kos_codes=["KOS.1"],
        exam_part="Part 1",
        max_score=1,
        form_id="1", # Было 1, стало строка
        source_url="http://example.com",
        raw_html_path="/path/to/raw.html",
        created_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
        metadata={}
    )


class TestDatabaseManagerGetProblemsByIds:
    """
    Tests for the get_problems_by_ids method in DatabaseManager.
    """

    def setup_method(self):
        """Set up a temporary database for each test."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db_manager = DatabaseManager(self.temp_db_path)
        self.db_manager.initialize_db()

    def teardown_method(self):
        """Clean up the temporary database file."""
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)

    def test_get_problems_by_ids_empty_list(self):
        """Test get_problems_by_ids with an empty list returns an empty list."""
        result = self.db_manager.get_problems_by_ids([])
        assert result == []

    def test_get_problems_by_ids_single_existing(self):
        """Test get_problems_by_ids with a single existing ID."""
        problem = create_sample_problem("test_id_1", text="Single problem")
        self.db_manager.save_problems([problem])

        result = self.db_manager.get_problems_by_ids(["test_id_1"])

        assert len(result) == 1
        assert result[0].problem_id == "test_id_1"
        assert result[0].text == "Single problem"

    def test_get_problems_by_ids_multiple_existing(self):
        """Test get_problems_by_ids with multiple existing IDs."""
        problems = [
            create_sample_problem("id_1", text="Problem 1"),
            create_sample_problem("id_2", text="Problem 2"),
            create_sample_problem("id_3", text="Problem 3"),
        ]
        self.db_manager.save_problems(problems)

        requested_ids = ["id_1", "id_3"]
        result = self.db_manager.get_problems_by_ids(requested_ids)

        assert len(result) == 2
        result_ids = {p.problem_id for p in result}
        assert result_ids == {"id_1", "id_3"}

    def test_get_problems_by_ids_with_nonexistent(self):
        """Test get_problems_by_ids when some IDs do not exist in the DB."""
        problem = create_sample_problem("id_1", text="Existing problem")
        self.db_manager.save_problems([problem])

        requested_ids = ["id_1", "nonexistent_id", "another_nonexistent"]
        result = self.db_manager.get_problems_by_ids(requested_ids)

        # Should only return the existing problem
        assert len(result) == 1
        assert result[0].problem_id == "id_1"

    def test_get_problems_by_ids_all_nonexistent(self):
        """Test get_problems_by_ids when all IDs are non-existent."""
        requested_ids = ["nonexistent_1", "nonexistent_2"]
        result = self.db_manager.get_problems_by_ids(requested_ids)

        assert result == []

    def test_get_problems_by_ids_duplicate_ids_in_request(self):
        """Test get_problems_by_ids with duplicate IDs in the request list."""
        problem = create_sample_problem("id_1", text="Duplicate test problem")
        self.db_manager.save_problems([problem])

        # Request the same ID twice
        requested_ids = ["id_1", "id_1"]
        result = self.db_manager.get_problems_by_ids(requested_ids)

        # Should return the problem only once
        assert len(result) == 1
        assert result[0].problem_id == "id_1"
        assert result[0].text == "Duplicate test problem"

    def test_get_problems_by_ids_ordering(self):
        """
        Test that the order of results from get_problems_by_ids might not match
        the input order, which is typical for IN clauses without explicit ordering.
        """
        problems = [
            create_sample_problem("id_a", text="A"),
            create_sample_problem("id_b", text="B"),
            create_sample_problem("id_c", text="C"),
        ]
        self.db_manager.save_problems(problems)

        # Request in a specific order (e.g., reverse)
        requested_ids = ["id_c", "id_a", "id_b"]
        result = self.db_manager.get_problems_by_ids(requested_ids)

        # Check that all expected IDs are present
        result_ids = {p.problem_id for p in result}
        assert result_ids == {"id_a", "id_b", "id_c"}

        # The order might not be preserved, so we only check content, not order.
        # If order preservation is critical, an 'ORDER BY' clause would be needed in the SQL.
        # For this test, we just confirm all are present and unique.
        assert len(result) == 3

    def test_get_problems_by_ids_performance_single_query(self):
        """
        Test that get_problems_by_ids executes only a single SQL query,
        confirming the performance optimization.
        Uses SQLAlchemy's event system to count queries.
        """
        # Create and save multiple problems
        problems = [create_sample_problem(f"id_{i}") for i in range(5)]
        self.db_manager.save_problems(problems)

        # Count queries using the event system
        query_count = 0
        def track_queries(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count
            query_count += 1

        event.listen(Engine, "before_cursor_execute", track_queries)

        # Call get_problems_by_ids
        result = self.db_manager.get_problems_by_ids(["id_0", "id_1", "id_2"])

        # Remove the listener
        event.remove(Engine, "before_cursor_execute", track_queries)

        # Assert that the number of queries is minimal (e.g., 1-2 for setup + main query)
        # The key is that it's significantly less than N calls for N IDs (which would be 5 in this case if done individually).
        assert query_count <= 2, f"Expected <= 2 queries, got {query_count}. Method did not optimize to a single query."

        # Verify the result is correct
        assert len(result) == 3
        assert {p.problem_id for p in result} == {"id_0", "id_1", "id_2"}

    def test_get_problems_by_ids_performance_vs_individual_calls(self):
        """
        Integration-like test comparing the performance benefit of get_problems_by_ids
        versus calling get_problem_by_id N times.
        """
        # Create and save a larger set of problems
        num_problems = 10
        problems = [create_sample_problem(f"perf_test_id_{i}", text=f"Perf problem {i}") for i in range(num_problems)]
        self.db_manager.save_problems(problems)

        requested_ids = [f"perf_test_id_{i}" for i in range(num_problems)]

        # Count queries for the optimized method
        query_count_optimized = 0
        def track_queries_optimized(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count_optimized
            query_count_optimized += 1

        event.listen(Engine, "before_cursor_execute", track_queries_optimized)

        # Execute the optimized call
        result_optimized = self.db_manager.get_problems_by_ids(requested_ids)

        event.remove(Engine, "before_cursor_execute", track_queries_optimized)

        # Count queries for the old method (N individual calls)
        query_count_individual = 0
        def track_queries_individual(conn, cursor, statement, parameters, context, executemany):
            nonlocal query_count_individual
            query_count_individual += 1

        event.listen(Engine, "before_cursor_execute", track_queries_individual)

        # Execute the old way: N calls to get_problem_by_id
        result_individual = []
        for pid in requested_ids:
            prob = self.db_manager.get_problem_by_id(pid)
            if prob:
                result_individual.append(prob)

        event.remove(Engine, "before_cursor_execute", track_queries_individual)

        # The optimized method should use significantly fewer queries
        assert query_count_optimized < query_count_individual, (
            f"Optimized method ({query_count_optimized} queries) did not perform better "
            f"than individual calls ({query_count_individual} queries)."
        )
        # Specifically, for 10 IDs, get_problems_by_ids should be around 1 query, while N calls are N queries.
        assert query_count_optimized <= 2  # Expecting 1-2 for the IN query and setup
        assert query_count_individual == num_problems # Expecting N queries for N individual calls

        # Results should be equivalent
        assert len(result_optimized) == len(result_individual)
        assert {p.problem_id for p in result_optimized} == {p.problem_id for p in result_individual}


