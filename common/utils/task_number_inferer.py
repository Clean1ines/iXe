"""
Module for inferring the official ЕГЭ task number (1–19) from extracted KES codes
and answer type, using the official specification.

This is necessary because the FIPI question bank does not explicitly state
the task number; it only provides KES/KOS codes.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import json
from common.services.specification import SpecificationService


class TaskNumberInferer:
    """
    Infers the official ЕГЭ task number based on KES codes and answer type.

    Uses the official `ege_2026_math_spec.json` to map top-level KES sections
    to possible task numbers, and applies heuristic rules for disambiguation.
    """

    def __init__(self, spec_service: SpecificationService, rules_path: Path = Path("common/config/task_number_rules.json")):
        """
        Initializes the inferer with the official specification and rules.

        Args:
            spec_service: An instance of SpecificationService loaded with
                          the official ЕГЭ 2026 math spec.
            rules_path: Path to JSON file with inference rules.
        """
        self.spec_service = spec_service
        self.spec_tasks = self.spec_service.spec.get("tasks", [])
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def infer(self, kes_codes: List[str], answer_type: str) -> Optional[int]:
        """
        Infers the most probable task number (1-19).

        Args:
            kes_codes: List of KES codes extracted from the FIPI block (e.g., ["7.5", "2.4"]).
            answer_type: "short", "extended", or "unknown".

        Returns:
            The inferred task number (1-19), or None if no match is found.
        """
        if not kes_codes:
            return None

        # Step 1: Map sub-KES codes to their top-level sections (e.g., "7.5" -> "7")
        top_level_kes = {code.split('.')[0] for code in kes_codes}

        # Step 2: Apply direct mapping rules from config
        for rule in self.rules.get("direct_mappings", []):
            if "kes_codes" in rule:
                if set(rule["kes_codes"]).issubset(set(kes_codes)):
                    return rule["task_number"]
            elif "kes_code" in rule:
                if rule["kes_code"] in kes_codes:
                    if "answer_type" not in rule or rule["answer_type"] == answer_type:
                        return rule["task_number"]

        # Step 3: Find candidate tasks from the official spec
        candidates = []
        for task in self.spec_tasks:
            spec_kes_set = set(task["kes_codes"])
            # Check if there's an intersection between extracted and spec KES
            if top_level_kes & spec_kes_set:
                expected_type = "extended" if task["task_number"] >= 13 else "short"
                if answer_type == expected_type or answer_type == "unknown":
                    candidates.append(task)

        if not candidates:
            return None

        # Step 4: If only one candidate, return it.
        if len(candidates) == 1:
            return candidates[0]["task_number"]

        # Step 5: For multiple candidates, prefer the most basic (lowest number) for short answers,
        # and the most advanced (highest number) for extended answers.
        candidate_numbers = [t["task_number"] for t in candidates]
        if answer_type == "short":
            return min(candidate_numbers)
        else:
            return max(candidate_numbers)

    # test utility
    @classmethod
    def from_paths(cls, spec_path: str, kes_kos_path: str, rules_path: str = "common/config/task_number_rules.json") -> 'TaskNumberInferer':
        """
        Convenience factory method to create an instance from file paths.

        Args:
            spec_path: Path to ege_2026_math_spec.json.
            kes_kos_path: Path to ege_2026_math_kes_kos.json.
            rules_path: Path to task number inference rules.

        Returns:
            A configured TaskNumberInferer instance.
        """
        spec_svc = SpecificationService(
            spec_path=Path(spec_path),
            kes_kos_path=Path(kes_kos_path)
        )
        return cls(spec_svc, Path(rules_path))
