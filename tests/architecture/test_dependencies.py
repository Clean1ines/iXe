import ast
import os
from pathlib import Path


def get_imports(file_path):
    """Extract all imports from a Python file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return []
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    
    return imports


def test_layer_dependencies():
    """Test that layers follow dependency rules: domain -> application -> infrastructure -> api."""
    
    # Define layer prefixes
    domain_modules = []
    application_modules = []
    infrastructure_modules = []
    api_modules = []
    
    # Find modules in each layer
    for root, dirs, files in os.walk('.'):
        if 'domain' in root:
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    domain_modules.append(os.path.join(root, file))
        elif 'application' in root:
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    application_modules.append(os.path.join(root, file))
        elif 'infrastructure' in root:
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    infrastructure_modules.append(os.path.join(root, file))
        elif 'api' in root:
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    api_modules.append(os.path.join(root, file))
    
    # Check domain layer - should not import from other layers
    for module in domain_modules:
        imports = get_imports(module)
        for imp in imports:
            assert not imp.startswith(('application.', 'infrastructure.', 'api.')), \
                f"Domain module {module} should not import from other layers: {imp}"
    
    # Check application layer - should only import from domain
    for module in application_modules:
        imports = get_imports(module)
        for imp in imports:
            assert imp.startswith('domain.') or imp in ['typing', 'dataclasses', 'abc'], \
                f"Application module {module} should only import from domain: {imp}"
    
    # Check infrastructure layer - can import from domain and application
    for module in infrastructure_modules:
        imports = get_imports(module)
        for imp in imports:
            assert imp.startswith(('domain.', 'application.')) or imp in ['typing', 'pathlib', 'json', 'bs4'], \
                f"Infrastructure module {module} should only import from domain/application: {imp}"
    
    print("All dependency tests passed!")


if __name__ == "__main__":
    test_layer_dependencies()
