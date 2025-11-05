#!/usr/bin/env python3
"""
Script to audit Python requirements.txt against actual imports in code.
Supports multiple paths and ignores imports from 'common' directory and local modules.
"""

import ast
import sys
import os
import argparse
from pathlib import Path
from typing import Set, Dict, List
import importlib.util
import pkgutil


def get_stdlib_modules() -> Set[str]:
    """Get the set of standard library module names."""
    stdlib_modules = set(sys.stdlib_module_names) if hasattr(sys, 'stdlib_module_names') else set()
    if not stdlib_modules:
        # Fallback: use a common list of stdlib modules for Python 3.12
        stdlib_modules = {
            '__future__', '__main__', '_thread', 'abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio',
            'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'bisect', 'builtins', 'bz2', 'cProfile',
            'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections',
            'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy',
            'copyreg', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal',
            'difflib', 'dis', 'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler',
            'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt',
            'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html',
            'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress',
            'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox',
            'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing',
            'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser',
            'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib',
            'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue',
            'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched',
            'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib',
            'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'sre', 'sre_compile', 'sre_constants',
            'sre_parse', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct', 'subprocess', 'sunau',
            'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios',
            'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace',
            'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata',
            'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser',
            'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib'
        }
    return stdlib_modules


def is_local_module(module_name: str, project_root: Path) -> bool:
    """Check if a module is a local project module (not external dependency)."""
    # Check if it's a relative import or starts with common, api, utils, etc.
    if module_name.startswith('.'):
        return True
    # Check if it's a direct import from common or other project directories
    if module_name.startswith('common'):
        return True
    # Check if the module exists as a local file/directory relative to project root
    # This is a simplified check - in practice, you might need a more sophisticated approach
    local_paths = ['api', 'utils', 'models', 'processors', 'scraper', 'scripts', 'config', 'tests', 'services', 'templates']
    if any(module_name.startswith(path) for path in local_paths):
        return True
    return False


def normalize_package_name(name: str) -> str:
    """Normalize package name (e.g., convert 'python-jose' to 'jose')."""
    # Common normalization rules
    name = name.lower()
    # Remove common prefixes/suffixes that don't match package names
    if name.startswith('python-'):
        name = name[7:]
    if name.startswith('py-'):
        name = name[3:]
    # Replace underscores with hyphens as they are often used interchangeably
    name = name.replace('_', '-')
    return name


def extract_imports_from_file(filepath: str, project_root: Path) -> Set[str]:
    """Extract all import names from a Python file using AST parsing."""
    imports = set()
    stdlib_modules = get_stdlib_modules()
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split('.')[0]  # Get top-level module name
                if module_name not in stdlib_modules and not is_local_module(module_name, project_root):
                    imports.add(normalize_package_name(module_name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                module_name = node.module.split('.')[0]  # Get top-level module name
                if module_name not in stdlib_modules and not is_local_module(module_name, project_root):
                    imports.add(normalize_package_name(module_name))
    
    return imports


def extract_imports_from_paths(paths: List[str], project_root: Path) -> Set[str]:
    """Recursively extract imports from a list of files/directories."""
    all_imports = set()
    
    for path_str in paths:
        path = Path(path_str)
        
        if path.is_file() and path.suffix == '.py':
            all_imports.update(extract_imports_from_file(str(path), project_root))
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                all_imports.update(extract_imports_from_file(str(py_file), project_root))
        else:
            print(f"Warning: Path {path_str} is not a .py file or directory", file=sys.stderr)
    
    return all_imports


def read_req_file(req_path: str) -> Dict[str, str]:
    """Read requirements.txt and return a dict {package_name: version_spec}."""
    req_dict = {}
    
    with open(req_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Split on version specifiers
                if '==' in line:
                    name, version = line.split('==', 1)
                elif '>=' in line:
                    name, version = line.split('>=', 1)
                elif '<=' in line:
                    name, version = line.split('<=', 1)
                elif '>' in line:
                    name, version = line.split('>', 1)
                elif '<' in line:
                    name, version = line.split('<', 1)
                elif '!=' in line:
                    name, version = line.split('!=', 1)
                else:
                    name = line
                    version = ''
                
                name = name.strip().split('[')[0]  # Remove extras like package[extra]
                req_dict[normalize_package_name(name)] = version.strip()
    
    return req_dict


def compare_usage_and_reqs(imports: Set[str], req_dict: Dict[str, str]) -> Dict[str, Set[str]]:
    """Compare imports vs requirements and return discrepancies."""
    req_packages = set(req_dict.keys())
    
    used_not_in_reqs = imports - req_packages
    in_reqs_not_used = req_packages - imports
    in_reqs_used = req_packages.intersection(imports)
    
    return {
        'used_not_in_reqs': used_not_in_reqs,
        'in_reqs_not_used': in_reqs_not_used,
        'in_reqs_used': in_reqs_used
    }


def main():
    parser = argparse.ArgumentParser(description='Audit Python requirements.txt against actual imports')
    parser.add_argument('--path', action='append', help='Path to directory to scan for imports')
    parser.add_argument('--file', action='append', help='Specific Python file to scan for imports')
    parser.add_argument('--requirements', default='requirements.txt', help='Path to requirements.txt file')
    
    args = parser.parse_args()
    
    # Collect all paths to scan
    paths_to_scan = []
    if args.path:
        paths_to_scan.extend(args.path)
    if args.file:
        paths_to_scan.extend(args.file)
    
    if not paths_to_scan:
        print("Error: No paths or files specified", file=sys.stderr)
        sys.exit(1)
    
    # Use current directory as project root
    project_root = Path.cwd()
    
    # Extract imports from specified paths/files
    imports = extract_imports_from_paths(paths_to_scan, project_root)
    
    # Read requirements
    req_dict = read_req_file(args.requirements)
    
    # Compare
    results = compare_usage_and_reqs(imports, req_dict)
    
    # Print results
    print("=== AUDIT RESULTS ===")
    print(f"Scanned paths: {paths_to_scan}")
    print(f"Total unique imports found: {len(imports)}")
    print(f"Total requirements in {args.requirements}: {len(req_dict)}")
    print()
    
    print("Used in code but NOT in requirements.txt:")
    for pkg in sorted(results['used_not_in_reqs']):
        print(f"  - {pkg}")
    
    print("\nIn requirements.txt but NOT used in code:")
    for pkg in sorted(results['in_reqs_not_used']):
        print(f"  - {pkg} (version: {req_dict[pkg]})")
    
    print("\nUsed in code AND in requirements.txt:")
    for pkg in sorted(results['in_reqs_used']):
        print(f"  - {pkg} (version: {req_dict[pkg]})")


if __name__ == '__main__':
    main()
