import pytest
from pathlib import Path

def test_minimize_dependencies():
    """Test that heavy dependencies are not in requirements_web.txt."""
    req_file = Path("requirements_web.txt")
    assert req_file.exists(), "requirements_web.txt should exist"
    
    heavy_deps = {
        'playwright',
        'qdrant-client',
        'selenium',
        'lxml',
        'aiofiles',
        'requests-html',
        'click',
        'colorama',
        'beautifulsoup4',
    }
    
    content = req_file.read_text()
    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith('#')]
    packages = {line.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('!=')[0].split('[')[0] for line in lines}
    
    found_heavy_deps = packages.intersection(heavy_deps)
    assert not found_heavy_deps, f"Found heavy dependencies in requirements_web.txt: {found_heavy_deps}"

