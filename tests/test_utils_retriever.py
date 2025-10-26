"""
Unit tests for the QdrantProblemRetriever class.
"""
import unittest
from unittest.mock import MagicMock, patch
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from models.problem_schema import Problem
from utils.database_manager import DatabaseManager
from utils.retriever import QdrantProblemRetriever


class TestQdrantProblemRetriever(unittest.TestCase):
    """
    Test cases for the QdrantProblemRetriever class.
    """

    def setUp(self):
        """
        Set up mock instances for QdrantClient, DatabaseManager, and a fake embedding model.
        """
        self.mock_qdrant_client = MagicMock(spec=QdrantClient)
        self.mock_db_manager = MagicMock(spec=DatabaseManager)
        # Настроим мок, чтобы он возвращал атрибут db_path
        self.mock_db_manager.db_path = "/mock/path/to/db.sqlite"

        self.collection_name = "test_problems_collection"

        # Create a fake embedding model mock
        self.mock_embedding_model = MagicMock()
        self.query_embedding = [0.5, 0.5, 0.5]  # Example embedding vector for the query
        self.mock_embedding_model.encode.return_value = self.query_embedding

        self.retriever = QdrantProblemRetriever(
            qdrant_client=self.mock_qdrant_client,
            collection_name=self.collection_name,
            db_manager=self.mock_db_manager
        )

    def test_retrieve_success(self):
        """
        Test the retrieve method successfully performs a search and fetches problems.
        """
        # Arrange: Define query text and expected results
        query_text = "Find problems about trigonometric equations."
        top_k = 3

        # Mock Qdrant search results (ScoredPoints)
        mock_scored_point_1 = MagicMock()
        mock_scored_point_1.payload = {"problem_id": "test_001"}
        mock_scored_point_2 = MagicMock()
        mock_scored_point_2.payload = {"problem_id": "test_002"}
        mock_scored_point_3 = MagicMock()
        mock_scored_point_3.payload = {"problem_id": "test_003"}
        mock_scored_points = [mock_scored_point_1, mock_scored_point_2, mock_scored_point_3]

        self.mock_qdrant_client.search.return_value = mock_scored_points

        # Mock DB manager to return specific Problem objects for the IDs
        test_problem_1 = Problem(
            problem_id="test_001",
            subject="mathematics",
            type="B",
            text="Solve sin(x) = 0.5.",
            answer="x = pi/6 + 2*pi*k or x = 5*pi/6 + 2*pi*k",
            topics=["math.trigonometry"],
            difficulty="medium",
            created_at=self.mock_db_manager.get_all_problems.return_value[0].created_at if self.mock_db_manager.get_all_problems.return_value else None # Placeholder for datetime
        )
        test_problem_2 = Problem(
            problem_id="test_002",
            subject="mathematics",
            type="C",
            text="Simplify cos(x)^2 + sin(x)^2.",
            answer="1",
            topics=["math.trigonometry"],
            difficulty="easy",
            created_at=self.mock_db_manager.get_all_problems.return_value[0].created_at if self.mock_db_manager.get_all_problems.return_value else None # Placeholder for datetime
        )
        test_problem_3 = Problem(
            problem_id="test_003",
            subject="mathematics",
            type="A",
            text="What is tan(pi/4)?",
            answer="1",
            topics=["math.trigonometry"],
            difficulty="easy",
            created_at=self.mock_db_manager.get_all_problems.return_value[0].created_at if self.mock_db_manager.get_all_problems.return_value else None # Placeholder for datetime
        )

        # Configure get_problem_by_id to return the corresponding problem based on ID
        def mock_get_problem_by_id(problem_id):
            if problem_id == "test_001":
                return test_problem_1
            elif problem_id == "test_002":
                return test_problem_2
            elif problem_id == "test_003":
                return test_problem_3
            return None # Or raise if ID not found

        self.mock_db_manager.get_problem_by_id.side_effect = mock_get_problem_by_id

        # Act: Call the retrieve method
        retrieved_problems = self.retriever.retrieve(query_text, self.mock_embedding_model, top_k=top_k)

        # Assert: Check that embedding model was called correctly
        self.mock_embedding_model.encode.assert_called_once_with(query_text)

        # Assert: Check that Qdrant client search was called correctly
        self.mock_qdrant_client.search.assert_called_once_with(
            collection_name=self.collection_name,
            query_vector=self.query_embedding,
            limit=top_k
        )

        # Assert: Check that DB manager was called to get each problem by ID
        expected_calls = [unittest.mock.call("test_001"), unittest.mock.call("test_002"), unittest.mock.call("test_003")]
        self.mock_db_manager.get_problem_by_id.assert_has_calls(expected_calls, any_order=True)

        # Assert: Check the returned list of problems
        self.assertEqual(len(retrieved_problems), 3)
        self.assertIn(test_problem_1, retrieved_problems)
        self.assertIn(test_problem_2, retrieved_problems)
        self.assertIn(test_problem_3, retrieved_problems)
        # Note: Order might differ due to any_order=True in assert_has_calls for DB calls.
        # The Qdrant search order is preserved in the return list by the actual implementation,
        # but for this test, we just check presence if order isn't critical for the assertion logic.


if __name__ == '__main__':
    unittest.main()
