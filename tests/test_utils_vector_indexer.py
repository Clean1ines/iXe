"""
Unit tests for the QdrantProblemIndexer class.
"""
import unittest
from unittest.mock import MagicMock, patch
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from domain.models.problem_schema import Problem
from infrastructure.adapters.database_adapter import DatabaseAdapter
from utils.vector_indexer import QdrantProblemIndexer


class TestQdrantProblemIndexer(unittest.TestCase):
    """
    Test cases for the QdrantProblemIndexer class.
    """

    def setUp(self):
        """
        Set up mock instances for DatabaseAdapter, QdrantClient, and a fake embedding model.
        """
        self.mock_db_manager = MagicMock(spec=DatabaseAdapter)
        # Настроим мок, чтобы он возвращал атрибут db_path, чтобы избежать ошибки в __init__
        self.mock_db_manager.db_path = "/mock/path/to/db.sqlite"

        self.mock_qdrant_client = MagicMock(spec=QdrantClient)
        self.collection_name = "test_problems_collection"

        # Create a fake embedding model mock
        self.mock_embedding_model = MagicMock()
        self.fake_embedding = [0.1, 0.2, 0.3]  # Example embedding vector
        self.mock_embedding_model.encode.return_value = self.fake_embedding

        self.indexer = QdrantProblemIndexer(
            db_manager=self.mock_db_manager,
            qdrant_client=self.mock_qdrant_client,
            collection_name=self.collection_name
        )

    def test_index_problems_success(self):
        """
        Test the index_problems method successfully fetches problems,
        generates embeddings, and calls Qdrant upsert with correct data.
        """
        # Arrange: Define test problems
        test_problem_1 = Problem(
            problem_id="test_001",
            subject="mathematics",
            type="A",
            text="Solve for x: x + 2 = 5.",
            answer="3",
            topics=["algebra.equations"],
            difficulty_level="easy",
            created_at=self.mock_db_manager.get_all_problems.return_value[0].created_at if self.mock_db_manager.get_all_problems.return_value else None # Placeholder for datetime
        )
        test_problem_2 = Problem(
            problem_id="test_002",
            subject="physics",
            type="B",
            text="What is the speed of light?",
            answer="300000000 m/s",
            topics=["physics.constants"],
            difficulty_level="medium",
            created_at=self.mock_db_manager.get_all_problems.return_value[0].created_at if self.mock_db_manager.get_all_problems.return_value else None # Placeholder for datetime
        )
        test_problems = [test_problem_1, test_problem_2]

        # Configure the mock to return the test problems
        self.mock_db_manager.get_all_problems.return_value = test_problems

        # Act: Call the index_problems method
        self.indexer.index_problems(self.mock_embedding_model)

        # Assert: Check that the DB manager was called to get problems
        self.mock_db_manager.get_all_problems.assert_called_once()

        # Assert: Check that the embedding model was called for each problem's text
        expected_encode_calls = [unittest.mock.call(test_problem_1.text), unittest.mock.call(test_problem_2.text)]
        self.mock_embedding_model.encode.assert_has_calls(expected_encode_calls, any_order=True)

        # Assert: Check that Qdrant client upsert was called
        self.mock_qdrant_client.upsert.assert_called_once()
        call_kwargs = self.mock_qdrant_client.upsert.call_args[1] # Get keyword arguments

        self.assertEqual(call_kwargs['collection_name'], self.collection_name)

        upserted_points = call_kwargs['points']
        self.assertEqual(len(upserted_points), 2) # Two problems should result in two points

        # Assert details for each point
        upserted_point_ids = {point.id for point in upserted_points}
        expected_ids = {test_problem_1.problem_id, test_problem_2.problem_id}
        self.assertEqual(upserted_point_ids, expected_ids)

        # Find the point for test_001 to check its details
        point_001 = next((p for p in upserted_points if p.id == "test_001"), None)
        self.assertIsNotNone(point_001)
        self.assertEqual(point_001.vector, self.fake_embedding)
        expected_payload_001 = {
            "problem_id": "test_001",
            "subject": "mathematics",
            "topics": ["algebra.equations"],
            "type": "A",
            "difficulty_level": "easy",
            "source_url": None, # Default value from the Problem instance
            "text": "Solve for x: x + 2 = 5.",
        }
        # Use assertDictEqual to check payload contents, ignoring potentially non-serializable fields like datetime if they exist in the payload
        for key, value in expected_payload_001.items():
             self.assertEqual(point_001.payload.get(key), value)

        # Find the point for test_002 to check its details
        point_002 = next((p for p in upserted_points if p.id == "test_002"), None)
        self.assertIsNotNone(point_002)
        self.assertEqual(point_002.vector, self.fake_embedding)
        expected_payload_002 = {
            "problem_id": "test_002",
            "subject": "physics",
            "topics": ["physics.constants"],
            "type": "B",
            "difficulty_level": "medium",
            "source_url": None, # Default value from the Problem instance
            "text": "What is the speed of light?",
        }
        for key, value in expected_payload_002.items():
             self.assertEqual(point_002.payload.get(key), value)


if __name__ == '__main__':
    unittest.main()

