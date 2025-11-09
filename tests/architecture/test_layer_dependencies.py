import pytest
from pathlib import Path
import re

PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_domain_layer_has_no_infrastructure_dependencies():
    """Domain layer should not depend on infrastructure implementations"""
    domain_path = PROJECT_ROOT / "domain"
    
    for py_file in domain_path.rglob("*.py"):
        if py_file.name == "__init__.py" or "interfaces" in str(py_file):
            continue
        
        content = py_file.read_text()
        # Check for direct imports of infrastructure
        assert "import infrastructure" not in content, f"Domain file {py_file} should not import infrastructure"
        assert "from infrastructure" not in content, f"Domain file {py_file} should not import from infrastructure"
        # Check for adapter imports
        assert "adapters" not in content.lower(), f"Domain file {py_file} should not import adapters"

def test_application_layer_has_no_infrastructure_dependencies():
    """Application layer should not depend on infrastructure implementations"""
    application_path = PROJECT_ROOT / "application"
    
    for py_file in application_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        
        content = py_file.read_text()
        assert "import infrastructure" not in content, f"Application file {py_file} should not import infrastructure"
        assert "from infrastructure" not in content, f"Application file {py_file} should not import from infrastructure"
        assert "adapters" not in content.lower(), f"Application file {py_file} should not import adapters"

def test_services_depend_on_interfaces_not_implementations():
    """Services should depend on domain interfaces, not infrastructure implementations"""
    services_path = PROJECT_ROOT / "services"
    
    for py_file in services_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        
        content = py_file.read_text()
        # Should not directly import infrastructure adapters
        assert "from infrastructure.adapters" not in content, \
            f"Service file {py_file} should not directly import infrastructure adapters"
        assert "import infrastructure.adapters" not in content, \
            f"Service file {py_file} should not directly import infrastructure adapters"
        
        # Should import domain interfaces instead
        has_domain_import = "from domain.interfaces" in content or "import domain.interfaces" in content
        assert has_domain_import, \
            f"Service file {py_file} should import domain interfaces for dependencies"
