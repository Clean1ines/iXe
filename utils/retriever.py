"""
Module for retrieving Problem instances from the database based on semantic similarity.

This module provides the `QdrantProblemRetriever` class which performs semantic search
using a Qdrant vector store. It finds similar problems based on a query text and
returns the full Problem objects fetched from the database.
"""

import logging
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from models.problem_schema import Problem
from utils.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class QdrantProblemRetriever:
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
        db_manager: DatabaseManager
    ):
        """
        Initializes the retriever with Qdrant client, collection name, and database manager.

        Args:
            qdrant_client (QdrantClient): Instance of the Qdrant client.
            collection_name (str): The name of the Qdrant collection to search in.
            db_manager (DatabaseManager): Instance to fetch full Problem objects from the database.
        """
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.db_manager = db_manager
        logger.debug(
            f"QdrantProblemRetriever initialized for collection '{collection_name}' "
            f"with database at '{db_manager.db_path}'"
        )

    def retrieve(self, query_text: str, embedding_model, top_k: int = 5) -> List[Problem]:
        """
        Retrieves a list of Problem objects similar to the query text.

        Performs a vector search in Qdrant and fetches the corresponding full Problem
        instances from the database.

        Args:
            query_text (str): The text to search for similar problems.
            embedding_model: An object with an `encode(text)` method to generate embeddings.
            top_k (int): The maximum number of similar problems to retrieve. Defaults to 5.

        Returns:
            List[Problem]: A list of Problem objects retrieved from the database,
                           sorted by similarity score (most similar first).
        """
        logger.info(f"Starting retrieval for query: '{query_text[:50]}...' (truncated if long), top_k={top_k}")
        try:
            # --- Generate embedding for the query ---
            query_embedding = embedding_model.encode(query_text)

            # --- Perform search in Qdrant ---
            logger.debug(f"Performing search in Qdrant collection '{self.collection_name}' with vector length {len(query_embedding)} and top_k {top_k}.")
            scored_points = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k
            )
            logger.debug(f"Qdrant search returned {len(scored_points)} results.")

            # --- Extract problem IDs from the results ---
            retrieved_problem_ids = [point.payload.get("problem_id") for point in scored_points]
            # Filter out potential None values if payload is malformed
            retrieved_problem_ids = [pid for pid in retrieved_problem_ids if pid is not None]
            logger.debug(f"Extracted {len(retrieved_problem_ids)} unique problem IDs from search results: {retrieved_problem_ids[:3]}...") # Log first 3

            # --- Fetch full Problem objects from the database ---
            # We need to fetch each problem individually using get_problem_by_id
            # A batch method like get_problems_by_ids would be more efficient if available.
            retrieved_problems = []
            for pid in retrieved_problem_ids:
                problem = self.db_manager.get_problem_by_id(pid)
                if problem:
                    retrieved_problems.append(problem)
                else:
                    logger.warning(f"Problem with ID '{pid}' found in Qdrant but not in database.")

            logger.info(f"Successfully retrieved {len(retrieved_problems)} Problem objects from the database.")
            return retrieved_problems

        except Exception as e:
            logger.error(f"Error occurred during retrieval: {e}", exc_info=True)
            raise # Re-raise the exception to signal failure to the caller
