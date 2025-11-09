"""
Infrastructure adapter for retrieving Problem instances from the database based on semantic similarity.
"""

import logging
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from domain.models.problem_schema import Problem
from domain.interfaces.infrastructure_adapters import IProblemRetriever
from infrastructure.adapters.database_adapter import DatabaseAdapter


logger = logging.getLogger(__name__)


class QdrantRetrieverAdapter(IProblemRetriever):
    """
    A class to retrieve Problems from the database based on semantic similarity
    using a Qdrant vector store.

    This retriever performs a vector search in Qdrant using an embedding of the
    query text and then fetches the full Problem objects from the database
    using the IDs returned by Qdrant.
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        db_manager: DatabaseAdapter
    ):
        """
        Initializes the retriever with Qdrant client and database manager.

        Args:
            qdrant_client: The Qdrant client instance.
            collection_name: The name of the Qdrant collection to search in.
            db_manager: The database manager for fetching Problem objects.
        """
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.db_manager = db_manager

    def retrieve_similar_problems(self, query: str, limit: int = 5) -> List[Problem]:
        """
        Retrieve problems similar to the query.

        Args:
            query: The query text to find similar problems to.
            limit: The maximum number of problems to return.

        Returns:
            A list of Problem objects similar to the query.
        """
        # In a real implementation, we would generate an embedding for the query
        # and perform a search in Qdrant. For now, this is a simplified version.
        
        # This is a placeholder implementation
        # In reality, you'd convert the query to a vector and search Qdrant
        try:
            # Perform search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_text=query,  # This would be a vector in real implementation
                limit=limit
            )
            
            # Extract problem IDs from search results
            problem_ids = [result.id for result in search_results]
            
            # Fetch full Problem objects from the database
            problems = []
            for pid in problem_ids:
                problem = self.db_manager.get_problem_by_id(str(pid))
                if problem:
                    problems.append(problem)
            
            return problems
        except Exception as e:
            logger.error(f"Error retrieving similar problems: {e}")
            # Return empty list or handle error as appropriate
            return []
