import tempfile
import os
from pathlib import Path
from audit_requirements import extract_imports_from_file, compare_usage_and_reqs, read_req_file, is_local_module


def test_extract_imports_from_file():
    """Test that extract_imports_from_file correctly identifies imports."""
    # Create a temporary Python file with known imports
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import os
import sys
from pathlib import Path
import fastapi
from pydantic import BaseModel
import non_existent_package
from common.models.database_models import DBProblem
from api.schemas import StartQuizRequest
""")
        temp_file_path = f.name

    try:
        # Call the function
        project_root = Path.cwd()  # Use current directory as project root for this test
        imports = extract_imports_from_file(temp_file_path, project_root)

        # Define expected imports (excluding stdlib and local/common modules)
        # Note: normalize_package_name converts underscores to hyphens
        expected_imports = {
            'fastapi',
            'pydantic',
            'non-existent-package'  # This should be included as it's not stdlib or local/common, and is normalized
        }

        # Assert the results
        assert imports == expected_imports, f"Expected {expected_imports}, but got {imports}"
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)


def test_compare_usage_and_reqs():
    """Test that compare_usage_and_reqs correctly compares imports and requirements."""
    # Define test data
    imports = {'fastapi', 'pydantic', 'requests', 'non-existent-package'}
    req_dict = {
        'fastapi': '==0.100.0',
        'pydantic': '==2.12.3',
        'qdrant-client': '==1.15.1',
        'uvicorn': '==0.23.0'
    }

    # Call the function
    results = compare_usage_and_reqs(imports, req_dict)

    # Define expected results
    expected_used_not_in_reqs = {'requests', 'non-existent-package'}
    expected_in_reqs_not_used = {'qdrant-client', 'uvicorn'}
    expected_in_reqs_used = {'fastapi', 'pydantic'}

    # Assert the results
    assert results['used_not_in_reqs'] == expected_used_not_in_reqs
    assert results['in_reqs_not_used'] == expected_in_reqs_not_used
    assert results['in_reqs_used'] == expected_in_reqs_used


def test_is_local_module():
    """Test that is_local_module correctly identifies local modules."""
    project_root = Path.cwd()

    # Test cases for local modules
    assert is_local_module('common.models', project_root)
    assert is_local_module('api.endpoints', project_root)
    assert is_local_module('utils.browser_manager', project_root)
    assert is_local_module('models.problem_builder', project_root)
    assert is_local_module('processors.html', project_root)
    assert is_local_module('scraper.fipi_scraper', project_root)
    assert is_local_module('scripts.scrape_tasks', project_root)
    assert is_local_module('config', project_root)
    assert is_local_module('tests.unit', project_root)
    assert is_local_module('services.quiz_service', project_root)
    assert is_local_module('templates.ui_components', project_root)

    # Test cases for non-local modules (external packages)
    assert not is_local_module('fastapi', project_root)
    assert not is_local_module('pydantic', project_root)
    assert not is_local_module('sqlalchemy', project_root)
    assert not is_local_module('playwright', project_root)
    assert not is_local_module('qdrant-client', project_root)

    # Test relative import
    assert is_local_module('.some_relative_import', project_root)
    assert is_local_module('..some_parent_import', project_root)

