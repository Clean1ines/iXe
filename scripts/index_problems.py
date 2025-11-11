#!/usr/bin/env python3
"""
Script to index problems from the SQLite database into a Qdrant collection.

This script loads problems from the database specified in the config,
generates embeddings using a sentence-transformer model,
and indexes them using the QdrantProblemIndexer.
"""

import logging
import sys
from pathlib import Path

# Add project root to sys.path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Assuming config.py is in the root or a standard location
try:
    import config
except ImportError:
    print("Error: Cannot import 'config.py'. Please ensure it's in the Python path.")
    sys.exit(1)

# Assuming utility modules are in a 'utils' subdirectory
try:
    from infrastructure.adapters.database_adapter import DatabaseAdapter
    from utils.vector_indexer import QdrantProblemIndexer
    from utils.logging_config import setup_logging
except ImportError as e:
    print(f"Error importing utility modules: {e}")
    sys.exit(1)

# Assuming Qdrant client is installed
try:
    from qdrant_client import QdrantClient
except ImportError:
    print("Error: 'qdrant-client' library is not installed. Please install it using 'pip install qdrant-client'.")
    sys.exit(1)

# Assuming sentence-transformers is installed
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: 'sentence-transformers' library is not installed. Please install it using 'pip install sentence-transformers'.")
    sys.exit(1)

from domain.interfaces.infrastructure_adapters import IDatabaseProvider


def main():
    """
    Main function to orchestrate the indexing process.
    
    This function:
    1. Sets up logging
    2. Validates database path from config
    3. Initializes database manager with IDatabaseProvider interface
    4. Initializes Qdrant client
    5. Defines collection name
    6. Initializes indexer
    7. Loads embedding model
    8. Runs indexing process
    """
    setup_logging(level="INFO")
    logger = logging.getLogger(__name__)

    logger.info("Starting the problem indexing script.")

    # --- 1. Determine DB Path ---
    # Assuming DATABASE_PATH is defined in config.py, or construct it from DATA_ROOT
    # Let's assume config.DATA_ROOT is the base directory and the DB file is named fipi_data.db
    db_path = config.DATA_ROOT / "fipi_data.db"
    logger.info(f"Using database path from config: {db_path}")

    # --- 2. Validate DB Path ---
    if not db_path.exists():
        logger.error(f"Database file does not exist at: {db_path}")
        sys.exit(1)
    logger.info("Database file found.")

    # --- 3. Initialize Database Manager ---
    try:
        db_manager: IDatabaseProvider = DatabaseAdapter(db_path=str(db_path))
        logger.info("Database manager initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize DatabaseAdapter: {e}")
        sys.exit(1)

    # --- 4. Initialize Qdrant Client ---
    # For local testing, you might want to use an in-memory instance or a local server.
    # If running a local Qdrant server, use host="localhost", port=6333 (or your configured port)
    # For this example, we'll use in-memory storage. Change this as needed for persistence.
    try:
        # Example: Local server
        # qdrant_client = QdrantClient(host="localhost", port=6333)
        # Example: In-memory (for testing)
        qdrant_client = QdrantClient(location=":memory:")
        logger.info("Qdrant client initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize QdrantClient: {e}")
        sys.exit(1)

    # --- 5. Define Collection Name ---
    collection_name = "fipi_problems"
    logger.info(f"Target Qdrant collection: '{collection_name}'")

    # --- 6. Initialize Indexer ---
    try:
        indexer = QdrantProblemIndexer(
            db_manager=db_manager,
            qdrant_client=qdrant_client,
            collection_name=collection_name
        )
        logger.info("QdrantProblemIndexer initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize QdrantProblemIndexer: {e}")
        sys.exit(1)

    # --- 7. Load Embedding Model ---
    # Choose a suitable multilingual model from sentence-transformers
    embedding_model_name = "distiluse-base-multilingual-cased-v2" # Or another model
    logger.info(f"Loading embedding model: '{embedding_model_name}'")
    try:
        embedding_model = SentenceTransformer(embedding_model_name)
        logger.info("Embedding model loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load embedding model '{embedding_model_name}': {e}")
        sys.exit(1)

    # --- 8. Run Indexing ---
    try:
        logger.info("Starting the indexing process...")
        indexer.index_problems(embedding_model=embedding_model)
        logger.info("Indexing process completed successfully.")
    except Exception as e:
        logger.error(f"An error occurred during the indexing process: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
