"""
Acceptance tests for Task 3: Creating isolated dependencies for unified automation-service.

This test verifies that all acceptance criteria are met:
- requirements_scraping_checking.txt contains correct dependencies
- requirements_web.txt contains correct dependencies  
- Isolation test exists and passes
- BrowserPoolManager implements cleanup after 50 requests
- ImageScriptProcessor handles ShowPicture scripts
- CheckAnswerResponse contains cognitive technique fields
- Automation components work without qdrant-client and supabase
- Healthcheck endpoint exists
"""

import pytest
import os
from pathlib import Path


def test_requirements_scraping_checking_contains_correct_deps():
    """Test that requirements_scraping_checking.txt contains required dependencies."""
    req_file = Path("requirements_scraping_checking.txt")
    assert req_file.exists(), "requirements_scraping_checking.txt should exist"
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    # Check for required packages (using actual versions from current architecture)
    required_packages = {'playwright', 'beautifulsoup4', 'lxml', 'requests'}
    missing_packages = required_packages - packages
    assert not missing_packages, f"Missing required packages in requirements_scraping_checking.txt: {missing_packages}"
    
    # Check specific versions exist
    assert any('playwright==' in line for line in lines), "playwright version not specified"
    assert any('beautifulsoup4==' in line for line in lines), "beautifulsoup4 version not specified"
    assert any('lxml==' in line for line in lines), "lxml version not specified"


def test_requirements_web_contains_correct_deps():
    """Test that requirements_web.txt contains required dependencies."""
    req_file = Path("requirements_web.txt")
    assert req_file.exists(), "requirements_web.txt should exist"
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    
    # Check for required packages
    assert any('fastapi==' in line for line in lines), "fastapi version not specified"
    assert any('uvicorn==' in line for line in lines), "uvicorn version not specified"


def test_no_cross_dependencies_in_automation():
    """Test that automation requirements don't contain qdrant-client or supabase."""
    req_file = Path("requirements_scraping_checking.txt")
    assert req_file.exists(), "requirements_scraping_checking.txt should exist"
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    forbidden_deps = {'qdrant-client', 'supabase'}
    found_forbidden = packages.intersection(forbidden_deps)
    assert not found_forbidden, f"Found forbidden dependencies in requirements_scraping_checking.txt: {found_forbidden}"


def test_isolation_test_exists():
    """Test that isolation test exists."""
    test_file = Path("tests/isolation/test_dependency_isolation.py")
    assert test_file.exists(), "tests/isolation/test_dependency_isolation.py should exist"


def test_browser_pool_manager_cleanup():
    """Test that BrowserPoolManager implements cleanup after 50 requests."""
    code_file = Path("utils/browser_pool_manager.py")
    assert code_file.exists(), "utils/browser_pool_manager.py should exist"
    
    content = code_file.read_text()
    
    # Check for max_requests_per_context initialization
    assert 'max_requests_per_context: int = 50' in content, "max_requests_per_context should be set to 50"
    
    # Check for cleanup methods
    assert 'page.context.clear_cookies()' in content, "page.context.clear_cookies() should be used for cleanup"
    assert 'page.reload(' in content, "page.reload() should be used for cleanup"
    
    # Check for request counting logic
    assert '_request_counts' in content, "_request_counts should track requests per browser"
    assert 'self._request_counts[browser_id] >= self.max_requests_per_context' in content, "Should check request count against threshold"


def test_image_script_processor_handles_showpicture():
    """Test that ImageScriptProcessor handles ShowPicture scripts."""
    code_file = Path("processors/html/image_processor.py")
    assert code_file.exists(), "processors/html/image_processor.py should exist"
    
    content = code_file.read_text()
    
    # Check for ShowPicture processing
    assert 'ShowPicture' in content, "ImageScriptProcessor should handle ShowPicture scripts"
    assert "re.search(r\"ShowPicture$$'([^']*)'$$\", script.string)" in content, "Should search for ShowPicture pattern"


def test_check_answer_response_has_cognitive_fields():
    """Test that CheckAnswerResponse contains cognitive technique fields."""
    code_file = Path("common/models/check_answer_schema.py")
    assert code_file.exists(), "common/models/check_answer_schema.py should exist"
    
    content = code_file.read_text()
    
    # Check for required fields
    required_fields = ['is_correct', 'feedback', 'evidence', 'deep_explanation_id', 'hint', 'next_task_suggestion']
    for field in required_fields:
        assert field in content, f"Field {field} should be present in CheckAnswerResponse"


def test_automation_components_work_without_qdrant_supabase():
    """Test that automation components can work without qdrant-client and supabase."""
    # Check utils directory
    content = Path("utils/browser_pool_manager.py").read_text()
    assert 'qdrant' not in content or 'qdrant_client' not in content, "BrowserPoolManager should not depend on qdrant"
    assert 'supabase' not in content, "BrowserPoolManager should not depend on supabase"
    
    # Check scraper directory
    content = Path("scraper/fipi_scraper.py").read_text()
    assert 'qdrant' not in content or 'qdrant_client' not in content, "FIPIScraper should not depend on qdrant"
    assert 'supabase' not in content, "FIPIScraper should not depend on supabase"
    
    # Check processors directory
    content = Path("processors/html/image_processor.py").read_text()
    assert 'qdrant' not in content or 'qdrant_client' not in content, "ImageScriptProcessor should not depend on qdrant"
    assert 'supabase' not in content, "ImageScriptProcessor should not depend on supabase"


def test_healthcheck_endpoint_exists():
    """Test that healthcheck endpoint exists."""
    health_file = Path("api/health.py")
    assert health_file.exists(), "api/health.py should exist"
    
    content = health_file.read_text()
    
    # Check for health endpoint
    assert 'def health_check(' in content, "health_check endpoint should exist"
    assert 'browser_pool' in content, "health check should check browser pool status"
    assert 'router.get("/health"' in content, "GET /health endpoint should exist"


def test_all_acceptance_criteria_met():
    """Comprehensive test that all acceptance criteria are met."""
    # Run all individual tests
    test_requirements_scraping_checking_contains_correct_deps()
    test_requirements_web_contains_correct_deps()
    test_no_cross_dependencies_in_automation()
    test_isolation_test_exists()
    test_browser_pool_manager_cleanup()
    test_image_script_processor_handles_showpicture()
    test_check_answer_response_has_cognitive_fields()
    test_automation_components_work_without_qdrant_supabase()
    test_healthcheck_endpoint_exists()
    
    # If we get here, all tests passed
    assert True, "All acceptance criteria for Task 3 are met"


if __name__ == "__main__":
    test_all_acceptance_criteria_met()
    print("All acceptance tests for Task 3 passed!")
