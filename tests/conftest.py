# tests/conftest.py
"""
Pytest configuration file.

This file is automatically loaded by pytest and can be used to configure
the test environment, including modifying sys.path.
"""
import sys
from pathlib import Path

# Add the project root directory (parent of 'tests') to sys.path
# This allows importing modules like 'config', 'main', 'processors' directly
project_root = Path(__file__).parent.parent  # Go up two levels from tests/
sys.path.insert(0, str(project_root))

# Optional: Print sys.path for debugging
# print("Updated sys.path:", sys.path)