"""
Pytest configuration file.

This file is automatically loaded by pytest and can be used to configure
the test environment, including modifying sys.path and setting up logging.
"""
import logging
import sys
from pathlib import Path

# Add the project root directory (parent of 'tests') to sys.path
# This allows importing modules like 'config', 'main', 'processors' directly
project_root = Path(__file__).parent.parent  # Go up two levels from tests/
sys.path.insert(0, str(project_root))

# Configure logging for tests
def pytest_configure(config):
    """Configure logging for pytest"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )
    
    # Set specific logging levels for noisy modules
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

# Optional: Print sys.path for debugging
print("Updated sys.path:", sys.path)
