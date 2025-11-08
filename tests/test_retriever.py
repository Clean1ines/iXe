import pytest
import logging
from io import StringIO
from unittest.mock import Mock, MagicMock, patch
from models.problem_schema import Problem
from infrastructure.adapters.qdrant_retriever_adapter import QdrantRetrieverAdapter
from infrastructure.adapters.database_adapter import DatabaseAdapter


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


class TestQdrantRetrieverAdapterRetrieve:
    """
    Tests for the retrieve method in QdrantRetrieverAdapter.
    Focuses on verifying the interaction with the updated DatabaseAdapter.get_problems_by_ids method.
    """

    def setup_method(self):
        """Set up a mock Qdrant client and database manager for each test."""
        self.mock_qdrant_client = Mock()
        # Создаем мок DatabaseAdapter, указываем, что у него есть атрибут db_path
        self.mock_db_manager = Mock(spec=DatabaseAdapter)
        self.mock_db_manager.db_path = "mocked_db_path_for_test" # Добавляем требуемый атрибут

        self.retriever = QdrantRetrieverAdapter(
            qdrant_client=self.mock_qdrant_client,
            collection_name="test_collection",
            db_manager=self.mock_db_manager
        )

    def test_retrieve_calls_get_problems_by_ids(self):
        """
        Test that retrieve method calls the new get_problems_by_ids method
        on the database manager with the IDs obtained from Qdrant.
        """
        query_text = "test query"
        embedding_model = Mock()
        embedding_model.encode.return_value = [0.1, 0.9]

        # Mock Qdrant search result
        mock_point_1 = Mock()
        mock_point_1.payload = {"problem_id": "id_1"}
        mock_point_2 = Mock()
        mock_point_2.payload = {"problem_id": "id_2"}
        mock_qdrant_result = [mock_point_1, mock_point_2]
        self.mock_qdrant_client.search.return_value = mock_qdrant_result

        # Mock the database manager's get_problems_by_ids to return a list of Problems
        expected_problems = [
            create_sample_problem("id_1", text="Retrieved 1"),
            create_sample_problem("id_2", text="Retrieved 2")
        ]
        self.mock_db_manager.get_problems_by_ids.return_value = expected_problems

        # Call retrieve
        result = self.retriever.retrieve(query_text, embedding_model, top_k=5)

        # Assertions
        # Check that Qdrant search was called
        self.mock_qdrant_client.search.assert_called_once()
        # Check that get_problems_by_ids was called with the correct IDs
        self.mock_db_manager.get_problems_by_ids.assert_called_once_with(["id_1", "id_2"])
        # Check that the result from the database manager is returned
        assert result == expected_problems

    def test_retrieve_with_empty_qdrant_result(self):
        """
        Test retrieve method when Qdrant returns no results.
        Should call get_problems_by_ids with an empty list.
        """
        query_text = "no match query"
        embedding_model = Mock()
        embedding_model.encode.return_value = [0.5, 0.5]

        # Mock Qdrant search result as empty
        self.mock_qdrant_client.search.return_value = []

        # Mock the database manager's get_problems_by_ids
        self.mock_db_manager.get_problems_by_ids.return_value = []

        result = self.retriever.retrieve(query_text, embedding_model, top_k=5)

        # Should call get_problems_by_ids with an empty list
        self.mock_db_manager.get_problems_by_ids.assert_called_once_with([])
        assert result == []

    def test_retrieve_with_malformed_qdrant_payload(self):
        """
        Test retrieve method when Qdrant returns points with missing or malformed problem_id in payload.
        Should filter out None IDs and call get_problems_by_ids with the valid ones.
        Also tests a scenario with a large number of results.
        """
        query_text = "malformed query"
        embedding_model = Mock()
        embedding_model.encode.return_value = [0.2, 0.8]

        # Mock Qdrant search result with various invalid payloads and one valid
        mock_points = []
        for i in range(100): # Simulate a larger list to check performance of filtering logic
            if i % 3 == 0:
                p = Mock()
                p.payload = {"problem_id": f"valid_id_{i}"}
                mock_points.append(p)
            elif i % 3 == 1:
                p = Mock()
                p.payload = {} # Missing problem_id
                mock_points.append(p)
            else: # i % 3 == 2
                p = Mock()
                p.payload = {"problem_id": None} # None ID
                mock_points.append(p)

        self.mock_qdrant_client.search.return_value = mock_points

        # Mock DB to return only the valid ones found
        expected_db_ids = [f"valid_id_{i}" for i in range(100) if i % 3 == 0]
        expected_problems_from_db = [create_sample_problem(pid) for pid in expected_db_ids]
        self.mock_db_manager.get_problems_by_ids.return_value = expected_problems_from_db

        result = self.retriever.retrieve(query_text, embedding_model, top_k=100)

        # Should call get_problems_by_ids only with the valid IDs
        self.mock_db_manager.get_problems_by_ids.assert_called_once_with(expected_db_ids)
        assert result == expected_problems_from_db

    def test_retrieve_logs_warning_for_missing_problems(self, caplog):
        """
        Test that retrieve logs a warning when problems found by Qdrant are missing from the database.
        """
        query_text = "warning test query"
        embedding_model = Mock()
        embedding_model.encode.return_value = [0.3, 0.7]

        # Mock Qdrant search result with IDs
        mock_point_1 = Mock()
        mock_point_1.payload = {"problem_id": "found_in_db"}
        mock_point_2 = Mock()
        mock_point_2.payload = {"problem_id": "missing_from_db"}
        mock_qdrant_result = [mock_point_1, mock_point_2]
        self.mock_qdrant_client.search.return_value = mock_qdrant_result

        # Mock the database manager's get_problems_by_ids to return only the found one
        # This simulates the scenario where 'missing_from_db' is not in the DB
        db_problem_found = create_sample_problem("found_in_db", text="Found in DB")
        self.mock_db_manager.get_problems_by_ids.return_value = [db_problem_found]

        # Run the retrieve method within the caplog context
        with caplog.at_level(logging.WARNING):
            result = self.retriever.retrieve(query_text, embedding_model, top_k=5)

        # Check that the warning was logged
        assert "missing_from_db" in caplog.text
        assert "not in database" in caplog.text
        assert "Problem IDs found in Qdrant but not in database" in caplog.messages[0] if caplog.messages else False

        # Result should only contain the found problem
        assert result == [db_problem_found]

