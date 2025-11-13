#!/usr/bin/env python3
import os
import ast
import sys
from collections import defaultdict

def find_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=file_path)
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                imports.append(full_name)
    return imports

def analyze_project(root_dir):
    dependencies = defaultdict(list)
    files = []
    
    # Собираем все Python файлы
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'venv' in dirpath or '__pycache__' in dirpath or 'build' in dirpath:
            continue
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(dirpath, filename))
    
    # Анализируем импорты
    for file_path in files:
        module_path = os.path.relpath(file_path, root_dir).replace(os.sep, '.')[:-3]
        imports = find_imports(file_path)
        
        for imp in imports:
            # Проверяем на циклические зависимости между слоями
            if any(x in imp for x in ['infrastructure', 'domain', 'application']):
                dependencies[module_path].append(imp)
    
    # Ищем нарушения архитектуры
    violations = []
    for module, imports in dependencies.items():
        module_layer = 'other'
        if 'domain' in module:
            module_layer = 'domain'
        elif 'application' in module:
            module_layer = 'application'
        elif 'infrastructure' in module:
            module_layer = 'infrastructure'
        
        for imp in imports:
            imp_layer = 'other'
            if 'domain' in imp:
                imp_layer = 'domain'
            elif 'application' in imp:
                imp_layer = 'application'
            elif 'infrastructure' in imp:
                imp_layer = 'infrastructure'
            
            # Правила Clean Architecture:
            # 1. domain не должен зависеть от application или infrastructure
            # 2. application может зависеть от domain, но не от infrastructure (только через интерфейсы)
            # 3. infrastructure может зависеть от domain и application
            if module_layer == 'domain' and imp_layer in ['application', 'infrastructure']:
                violations.append(f"DOMAIN VIOLATION: {module} imports {imp}")
            elif module_layer == 'application' and imp_layer == 'infrastructure' and 'adapters' in imp:
                # Разрешаем импорт интерфейсов, но не конкретных адаптеров
                if 'DatabaseAdapter' in imp or 'adapter' in imp.lower():
                    violations.append(f"APPLICATION VIOLATION: {module} imports concrete adapter {imp}")
    
    return violations

if __name__ == "__main__":
    violations = analyze_project('.')
    if violations:
        print("ARCHITECTURAL VIOLATIONS FOUND:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("No architectural violations found")
