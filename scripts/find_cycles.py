#!/usr/bin/env python3
import os
import sys
import importlib
import pkgutil
import inspect
from collections import defaultdict

def find_modules(root_dir):
    modules = []
    for root, dirs, files in os.walk(root_dir):
        if 'venv' in root or '__pycache__' in root or 'build' in root:
            continue
        package = root.replace('/', '.')
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                module_name = f"{package}.{file[:-3]}" if package != '.' else file[:-3]
                modules.append(module_name)
    return modules

def analyze_imports(modules):
    dependencies = defaultdict(set)
    cycles = []
    
    for module in modules:
        try:
            mod = importlib.import_module(module.replace('./', ''))
            for name, obj in inspect.getmembers(mod):
                if inspect.ismodule(obj):
                    imported_module = obj.__name__
                    if imported_module in modules:
                        dependencies[module].add(imported_module)
        except (ImportError, AttributeError, SyntaxError) as e:
            continue
    
    # Simple cycle detection
    for module in dependencies:
        for dep in dependencies[module]:
            if dep in dependencies and module in dependencies[dep]:
                cycles.append((module, dep))
    
    return cycles

if __name__ == "__main__":
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    modules = find_modules(root_dir)
    cycles = analyze_imports(modules)
    
    if cycles:
        print("CYCLIC DEPENDENCIES FOUND:")
        for cycle in cycles:
            print(f"  {cycle[0]} <-> {cycle[1]}")
    else:
        print("No cyclic dependencies found")
