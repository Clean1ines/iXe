import pytest
from pathlib import Path

def test_scraping_checking_reqs():
    """Test that requirements_scraping_checking.txt contains the correct dependencies."""
    req_file = Path("requirements_scraping_checking.txt")
    assert req_file.exists(), "requirements_scraping_checking.txt should exist"
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    # Check that required packages for scraping/checking are present
    required_deps = {'playwright', 'requests', 'beautifulsoup4'}
    missing_deps = required_deps - packages
    assert not missing_deps, f"Missing required scraping/checking dependencies in requirements_scraping_checking.txt: {missing_deps}"
    
    # Check that heavy deps not specific to this service are not included (optional, depends on scope)
    # For this service, playwright is expected, but things like fastapi, qdrant-client should not be here
    web_or_indexing_deps = {'fastapi', 'qdrant-client', 'uvicorn'}
    found_web_or_indexing_deps = packages.intersection(web_or_indexing_deps)
    assert not found_web_or_indexing_deps, f"Found web/indexing dependencies in requirements_scraping_checking.txt: {found_web_or_indexing_deps}"

