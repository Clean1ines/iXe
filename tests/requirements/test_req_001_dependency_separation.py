import pytest
from pathlib import Path

def test_web_api_reqs_no_heavy_deps():
    """Test that requirements_web.txt does not contain heavy dependencies."""
    req_file = Path("requirements_web.txt")
    assert req_file.exists(), "requirements_web.txt should exist"
    
    # Heavy dependencies that should NOT be in requirements_web.txt
    # These are typically used by scraper/checker/indexer/quiz-service but not by web API directly
    heavy_deps = {
        'playwright',      # Used by scraper and checker via utils.browser_manager  
        'selenium',        # Not currently used but potential heavy dep
        'lxml',            # Used by html processors
        'aiofiles',        # Not in current requirements but potential heavy dep
        'requests-html',   # Not in current requirements but potential heavy dep
        'click',           # CLI related, not web API
        'colorama',        # CLI related, not web API
        'beautifulsoup4',  # Used by scraper and processors, not directly by web API
        'qdrant-client',   # Used by QuizService, which should be external to web API layer
    }
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    found_heavy_deps = packages.intersection(heavy_deps)
    assert not found_heavy_deps, f"Found heavy dependencies in requirements_web.txt: {found_heavy_deps}"
    
    # Verify required web dependencies are present
    required_web_deps = {'fastapi', 'uvicorn', 'python-multipart', 'jinja2'}
    missing_web_deps = required_web_deps - packages
    assert not missing_web_deps, f"Missing required web dependencies in requirements_web.txt: {missing_web_deps}"

