"""
Module for inferring the official ЕГЭ task number (1–19) from extracted KES codes
and answer type, using the official specification.

This is necessary because the FIPI question bank does not explicitly state
the task number; it only provides KES/KOS codes.
"""

from typing import List, Optional, Dict, Any
from services.specification import SpecificationService


class TaskNumberInferer:
    """
    Infers the official ЕГЭ task number based on KES codes and answer type.

    Uses the official `ege_2026_math_spec.json` to map top-level KES sections
    to possible task numbers, and applies heuristic rules for disambiguation.
    """

    def __init__(self, spec_service: SpecificationService):
        """
        Initializes the inferer with the official specification.

        Args:
            spec_service: An instance of SpecificationService loaded with
                          the official ЕГЭ 2026 math spec.
        """
        self.spec_service = spec_service
        self.spec_tasks = self.spec_service.spec.get("tasks", [])

    def infer(self, kes_codes: List[str], answer_type: str) -> int:
        """
        Infers the most probable task number (1-19).

        Args:
            kes_codes: List of KES codes extracted from the FIPI block (e.g., ["7.5", "2.4"]).
            answer_type: "short" or "extended".

        Returns:
            The inferred task number (1-19), or 0 if no match is found.
        """
        if not kes_codes:
            return 0

        # Step 1: Map sub-KES codes to their top-level sections (e.g., "7.5" -> "7")
        top_level_kes = {code.split('.')[0] for code in kes_codes}

        # Step 2: Find candidate tasks from the official spec
        candidates = []
        for task in self.spec_tasks:
            spec_kes_set = set(task["kes_codes"])
            # Check if there's an intersection between extracted and spec KES
            if top_level_kes & spec_kes_set:
                expected_type = "extended" if task["task_number"] >= 13 else "short"
                if answer_type == expected_type or answer_type == "unknown":
                    candidates.append(task)

        if not candidates:
            return 0

        # Step 3: Apply heuristic rules for disambiguation
        # Rule 1: If a specific sub-KES code is known to map to a single task, use it.
        if "7.5" in kes_codes:
            return 2  # "Координаты и векторы" is almost exclusively Task 2.
        if "6.2" in kes_codes and answer_type == "short":
            return 4  # Basic probability is Task 4; advanced is Task 5.
        if "4.2" in kes_codes:
            return 12 # Derivative application is Task 12 in Part 1.
        if "1.5" in kes_codes and "1.8" in kes_codes:
            return 7  # Trig functions + expression transformation is Task 7.

        # Rule 2: If only one candidate, return it.
        if len(candidates) == 1:
            return candidates[0]["task_number"]

        # Rule 3: For multiple candidates, prefer the most basic (lowest number) for short answers,
        # and the most advanced (highest number) for extended answers.
        candidate_numbers = [t["task_number"] for t in candidates]
        if answer_type == "short":
            return min(candidate_numbers)
        else:
            return max(candidate_numbers)

    @classmethod
    def from_paths(cls, spec_path: str, kes_kos_path: str) -> 'TaskNumberInferer':
        """
        Convenience factory method to create an instance from file paths.

        Args:
            spec_path: Path to ege_2026_math_spec.json.
            kes_kos_path: Path to ege_2026_math_kes_kos.json.

        Returns:
            A configured TaskNumberInferer instance.
        """
        from pathlib import Path
        spec_svc = SpecificationService(
            spec_path=Path(spec_path),
            kes_kos_path=Path(kes_kos_path)
        )
        return cls(spec_svc)
