#!/usr/bin/env python3
"""
Generates a text representation of the directory structure, focusing on specific file types.

This script walks through the specified directory and its subdirectories,
listing folders and files matching common source code extensions (.py, .json, .ts, .js).
It respects .gitignore files, excluding matching files and directories from the output.
"""

import os
import argparse
from pathlib import Path
import fnmatch
import sys

# Define the set of file extensions to include
INCLUDED_EXTENSIONS = {'.py', '.json', '.ts', '.js'}

def read_gitignore(path):
    """
    Reads a .gitignore file and returns a list of patterns.

    Args:
        path (Path): The path object representing the directory containing .gitignore.

    Returns:
        list: A list of pattern strings from the .gitignore file.
              Returns an empty list if .gitignore does not exist.
    """
    gitignore_file = path / '.gitignore'
    if gitignore_file.is_file():
        try:
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # Filter out empty lines and comments (starting with #)
            patterns = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            return patterns
        except (IOError, OSError):
            # Silently ignore errors reading .gitignore, behave as if it's empty
            pass
    return []

def is_ignored(name, patterns):
    """
    Checks if a given name (file or directory) matches any of the provided .gitignore patterns.

    This is a simplified matcher supporting basic wildcards (*).
    It does not handle complex .gitignore features like ** or negations (!).

    Args:
        name (str): The name of the file or directory to check.
        patterns (list): A list of .gitignore pattern strings.

    Returns:
        bool: True if the name matches a pattern and should be ignored, False otherwise.
    """
    for pattern in patterns:
        # Use fnmatch for basic pattern matching
        # This handles '*' (any sequence) and '?' (any single character)
        # Note: This is a simplification. Real .gitignore is more complex.
        if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(os.path.basename(name), pattern):
            return True
        # Check for directory patterns ending with '/'
        if pattern.endswith('/'):
            if fnmatch.fnmatch(name, pattern.rstrip('/')) or fnmatch.fnmatch(os.path.basename(name), pattern.rstrip('/')):
                return True
    return False

def generate_structure(start_path, prefix="", gitignore_patterns=None, current_depth=0, max_depth=None):
    """
    Recursively generates the directory structure string, respecting .gitignore.

    Args:
        start_path (Path): The path object representing the current directory to process.
        prefix (str): The indentation prefix used for the current recursion level.
        gitignore_patterns (list): A list of patterns inherited from parent directories.
        current_depth (int): The current depth in the directory tree (for potential depth limiting).
        max_depth (int, optional): The maximum allowed depth. If specified, recursion stops beyond this level.

    Returns:
        list: A list of strings representing the formatted structure for this path and its children.
    """
    output_lines = []
    start_path = Path(start_path)

    if max_depth is not None and current_depth > max_depth:
        return output_lines

    # Use patterns from parent directory or initialize for root
    if gitignore_patterns is None:
        gitignore_patterns = []
        # Read .gitignore from the starting path (root) if it exists
        gitignore_patterns.extend(read_gitignore(start_path))

    # Get all items (files and directories) in the current directory
    try:
        items = sorted(start_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except (PermissionError, OSError):
        # If directory cannot be read, return empty list or a message
        # print(f"{prefix}[Permission Denied or Error reading {start_path}]")
        return output_lines

    # Separate directories and files, applying ignore rules
    dirs = []
    files = []
    for item in items:
        # Check if item itself is ignored based on current patterns
        if is_ignored(item.name, gitignore_patterns):
            continue # Skip this item entirely

        if item.is_dir():
            # Read .gitignore specific to this subdirectory
            subdir_gitignore_patterns = read_gitignore(item)
            # Combine parent patterns with current directory's patterns for children
            combined_patterns = gitignore_patterns + subdir_gitignore_patterns
            dirs.append((item, combined_patterns))
        elif item.is_file() and item.suffix.lower() in INCLUDED_EXTENSIONS:
            files.append(item)

    # Process directories first
    all_items_count = len(dirs) + len(files)
    for i, (d, child_gitignore_patterns) in enumerate(dirs):
        is_last_item = (i == len(dirs) - 1) and (len(files) == 0)  # Check if this dir is the last item overall
        current_prefix = "└── " if is_last_item else "├── "
        next_prefix = prefix + ("    " if is_last_item else "│   ")

        output_lines.append(f"{prefix}{current_prefix}{d.name}/")
        # Recurse, passing the combined patterns down to children
        output_lines.extend(generate_structure(
            d, next_prefix, child_gitignore_patterns, current_depth + 1, max_depth
        ))

    # Process files
    for i, f in enumerate(files):
        is_last_item = (i == len(files) - 1)  # Check if this file is the last item in *this* directory
        current_prefix = "└── " if is_last_item else "├── "
        output_lines.append(f"{prefix}{current_prefix}{f.name}")

    return output_lines

def main():
    """
    Main function to handle command-line arguments and initiate structure generation.
    """
    parser = argparse.ArgumentParser(
        description="Generate a text representation of directory structure for specific file types, respecting .gitignore.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="The path to the directory to analyze. Defaults to current directory."
    )
    parser.add_argument(
        "--max-depth", "-d",
        type=int,
        help="Maximum depth to recurse into subdirectories."
    )

    args = parser.parse_args()
    root_path = Path(args.path)

    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist.", file=sys.stderr)
        return

    if not root_path.is_dir():
        print(f"Error: Path '{root_path}' is not a directory.", file=sys.stderr)
        return

    print(f"{root_path.name}/")
    structure_lines = generate_structure(root_path, max_depth=args.max_depth)
    for line in structure_lines:
        print(line)

if __name__ == "__main__":
    main()
