import ast
import os
from collections import defaultdict
import sys

def find_python_files(root_dir):
    py_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environment and test directories to focus on main code
        if 'venv' in root or '__pycache__' in root or '/tests/' in root:
            continue
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                py_files.append(os.path.join(root, file))
    return py_files

def get_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
        except SyntaxError:
            return []
    
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    
    return imports

def build_module_path(file_path, root_dir):
    # Convert file path to module path
    rel_path = os.path.relpath(file_path, root_dir)
    module_path = rel_path.replace(os.sep, '.').replace('.py', '')
    if module_path.endswith('.__init__'):
        module_path = module_path[:-9]  # Remove .__init__
    return module_path

def build_dependency_graph(root_dir):
    py_files = find_python_files(root_dir)
    modules = {}
    
    # Build module map
    for file_path in py_files:
        module_name = build_module_path(file_path, root_dir)
        if module_name:
            modules[module_name] = file_path
    
    graph = defaultdict(set)
    
    # Build dependencies
    for module_name, file_path in modules.items():
        imports = get_imports(file_path)
        for imp in imports:
            # Check if the import is one of our modules
            for proj_module in modules.keys():
                if imp == proj_module or imp.startswith(proj_module + '.'):
                    graph[module_name].add(proj_module)
                    break
    
    return graph

def has_cycle(graph):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {node: WHITE for node in graph}
    
    def dfs(node, path):
        if color[node] == GRAY:
            return True, path + [node]
        if color[node] == BLACK:
            return False, []
        
        color[node] = GRAY
        path.append(node)
        
        for neighbor in graph.get(node, []):
            if neighbor in graph:  # Only check if neighbor is in our project
                has_cycle_result, cycle_path = dfs(neighbor, path.copy())
                if has_cycle_result:
                    return True, cycle_path
        
        color[node] = BLACK
        path.pop()
        return False, []
    
    for node in graph:
        if color[node] == WHITE:
            has_cycle_result, cycle_path = dfs(node, [])
            if has_cycle_result:
                return True, cycle_path
    return False, []

# Check for cycles in the project
graph = build_dependency_graph('.')
has_cycle_result, cycle_path = has_cycle(graph)

if has_cycle_result:
    print(f'ЦИКЛИЧЕСКАЯ ЗАВИСИМОСТЬ НАЙДЕНА: {" -> ".join(cycle_path)}')
else:
    print('ЦИКЛИЧЕСКИЕ ЗАВИСИМОСТИ НЕ ОБНАРУЖЕНЫ')
