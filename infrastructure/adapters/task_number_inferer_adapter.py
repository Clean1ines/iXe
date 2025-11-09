"""
Infrastructure adapter for inferring task numbers from problem IDs using official FIPI specifications.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from domain.interfaces.specification_provider import ISpecificationProvider
from domain.interfaces.task_inferer import ITaskNumberInferer


class TaskNumberInfererAdapter(ITaskNumberInferer):
    """
    Adapter for inferring task numbers based on rules and specifications.
    
    This class implements the logic for inferring task numbers from problem IDs
    by applying a set of predefined rules. It uses the specification service
    to validate inferred numbers against official FIPI specifications.
    """

    def __init__(self, spec_service: ISpecificationProvider, rules_path: Path = Path("config/task_number_rules.json")):
        """
        Initialize the inferer with specification service and rules.

        Args:
            spec_service: An instance of SpecificationService loaded with subject-specific specs
            rules_path: Path to the JSON file containing task number inference rules
        """
        self.spec_service = spec_service
        self.rules = self._load_rules(rules_path)

    def _load_rules(self, rules_path: Path) -> Dict[str, Any]:
        """Load inference rules from a JSON file."""
        if rules_path.exists():
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Default rules if file doesn't exist
            return {
                "default": 1,  # Default task number if no rule matches
                "patterns": {
                    # Example patterns - these would be customized based on actual problem ID formats
                    "task_(\\d+)": "\\1",
                    "problem_(\\d+)": "\\1"
                }
            }

    def infer_task_number(self, problem_id: str) -> Optional[int]:
        """
        Infer the task number from a problem ID using loaded rules.

        Args:
            problem_id: The ID of the problem to infer the task number for.

        Returns:
            The inferred task number, or None if it could not be inferred.
        """
        # Apply pattern matching rules
        import re
        for pattern, replacement in self.rules.get("patterns", {}).items():
            match = re.search(pattern, problem_id)
            if match:
                try:
                    # If replacement is a pattern with groups, apply it
                    if '\\' in replacement:
                        inferred = re.sub(pattern, replacement, problem_id)
                    else:
                        # Otherwise, use the matched group
                        inferred = match.group(1)
                    return int(inferred)
                except (ValueError, IndexError):
                    continue  # If conversion fails, try next pattern

        # Return default if no pattern matched
        default = self.rules.get("default")
        return int(default) if default is not None else None

    def infer(self, kes_codes: List[str], answer_type: str) -> Optional[int]:
        """
        Infer the official ЕГЭ task number from KES codes and answer type.
        
        Args:
            kes_codes: List of KES codes extracted from the problem header
            answer_type: Type of answer expected (e.g., 'number', 'text', 'formula')
            
        Returns:
            The inferred task number, or None if it could not be inferred.
        """
        if not kes_codes:
            return None

        # Load direct mappings from rules
        direct_mappings = self.rules.get("direct_mappings", [])
        
        # Check for single KES code mappings
        for mapping in direct_mappings:
            if "kes_code" in mapping and mapping["kes_code"] in kes_codes:
                # Check if answer_type is also specified and matches
                if "answer_type" in mapping:
                    if mapping["answer_type"] == answer_type:
                        return mapping["task_number"]
                else:
                    # If no answer_type specified in rule, just return the task number
                    return mapping["task_number"]
        
        # Check for multi-KES code mappings
        for mapping in direct_mappings:
            if "kes_codes" in mapping:
                required_codes = mapping["kes_codes"]
                # Check if all required codes are present in the input kes_codes
                if all(code in kes_codes for code in required_codes):
                    # Check if answer_type is also specified and matches
                    if "answer_type" in mapping:
                        if mapping["answer_type"] == answer_type:
                            return mapping["task_number"]
                    else:
                        # If no answer_type specified in rule, just return the task number
                        return mapping["task_number"]
        
        # If no direct mapping found, return None
        return None
