"""
Module for indexing Problem instances from the database into a Qdrant vector store.

This module provides the `QdrantProblemIndexer` class which handles the process
of fetching problems from a database and uploading their embeddings and metadata
to a Qdrant collection for semantic search.
"""

import logging
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from domain.models.problem_schema import Problem
from domain.interfaces.infrastructure_adapters import IDatabaseProvider

logger = logging.getLogger(__name__)


class QdrantProblemIndexer:
    """
    A class to index Problems from a IDatabaseProvider into a Qdrant collection.

    This indexer fetches Problem instances, generates embeddings for their text,
    and uploads them along with metadata to a specified Qdrant collection.
    """

    def __init__(
        self,
        db_manager: IDatabaseProvider,
        qdrant_client: QdrantClient,
        collection_name: str
    ):
        """
        Initializes the indexer with database manager, Qdrant client, and collection name.

        Args:
            db_manager (IDatabaseProvider): Instance to fetch problems from the database.
            qdrant_client (QdrantClient): Instance of the Qdrant client.
            collection_name (str): The name of the Qdrant collection to index into.
        """
        self.db_manager = db_manager
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        logger.debug(
            f"QdrantProblemIndexer initialized for collection '{collection_name}' "
            # Note: db_manager might not have db_path attribute, so we might need to handle this carefully
            # For now, we'll keep it if the concrete implementation has this attribute
            # Otherwise, we might need to remove or adapt this log
            f"with database adapter"
        )

    def index_problems(self, embedding_model: Any) -> None:
        """
        Indexes all problems from the database into the Qdrant collection.

        Fetches problems, generates embeddings for their text, and uploads them
        with relevant metadata to Qdrant.

        Args:
            embedding_model (Any): An object with an `encode(text)` method to generate embeddings.
        """
        logger.info("Starting indexing process for all problems.")
        try:
            # Fetch all problems from the database
            problems: List[Problem] = self.db_manager.get_all_problems()
            logger.info(f"Fetched {len(problems)} problems from the database.")

            points_to_upsert = []
            for problem in problems:
                # --- Prepare text for embedding ---
                # Start with the main problem text
                text_for_embedding = problem.text
                # Future: Append solutions if they are relevant for search
                # if problem.solutions:
                #     solution_texts = [sol.get('text', '') for sol in problem.solutions if isinstance(sol, dict)]
                #     text_for_embedding += " " + " ".join(solution_texts)

                # --- Generate embedding ---
                embedding_vector = embedding_model.encode(text_for_embedding)

                # --- Prepare payload ---
                payload = {
                    "problem_id": problem.problem_id,
                    "subject": problem.subject,
                    "topics": getattr(problem, 'kes_codes', []),  # Using getattr to handle potentially missing attributes
                    "type": problem.type,
                    "difficulty": getattr(problem, 'difficulty', 'unknown'),
                    "source_url": getattr(problem, 'source_url', None), # Optional: useful for linking back
                    "text": problem.text, # Optional: store the text itself, might be redundant if searchable via vectors
                    # Add other fields as needed for filtering/searching
                }
                # Handle potentially non-serializable fields like datetime if necessary
                # For Pydantic models with datetime, they are usually serialized correctly by Qdrant client
                # but be mindful of complex nested structures in metadata if not handled by Pydantic serialization.

                # --- Create PointStruct ---
                point = qdrant_models.PointStruct(
                    id=problem.problem_id, # Use problem_id as the unique ID in Qdrant
                    vector=embedding_vector,
                    payload=payload
                )
                points_to_upsert.append(point)

            # --- Upsert points to Qdrant ---
            logger.debug(f"Upserting {len(points_to_upsert)} points to collection '{self.collection_name}'.")
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points_to_upsert
            )
            logger.info(f"Successfully indexed {len(problems)} problems into Qdrant collection '{self.collection_name}'.")

        except Exception as e:
            logger.error(f"Error occurred during indexing: {e}", exc_info=True)
            raise # Re-raise the exception to signal failure to the caller
