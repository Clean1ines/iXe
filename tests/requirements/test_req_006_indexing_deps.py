import pytest
from pathlib import Path

def test_indexing_reqs():
    """Test that requirements_indexing.txt contains the correct dependencies."""
    req_file = Path("requirements_indexing.txt")
    assert req_file.exists(), "requirements_indexing.txt should exist"
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    # Check that required packages for indexing are present
    required_deps = {'qdrant-client', 'sentence-transformers'}
    missing_deps = required_deps - packages
    assert not missing_deps, f"Missing required indexing dependencies in requirements_indexing.txt: {missing_deps}"
    
    # Check that web/scraping specific deps are not included (optional, depends on scope)
    # For this service, qdrant-client is expected, but things like fastapi, playwright should not be here
    web_or_scraping_deps = {'fastapi', 'playwright', 'uvicorn', 'beautifulsoup4'}
    found_web_or_scraping_deps = packages.intersection(web_or_scraping_deps)
    assert not found_web_or_scraping_deps, f"Found web/scraping dependencies in requirements_indexing.txt: {found_web_or_scraping_deps}"

