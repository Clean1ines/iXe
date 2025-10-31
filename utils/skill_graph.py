from typing import Dict, List
from utils.database_manager import DatabaseManager
from services.specification import SpecificationService
from models.problem_schema import Problem


class InMemorySkillGraph:
    """
    In-memory representation of the skill graph for adaptive learning.
    Maps tasks to skills, skills to tasks, and provides skill descriptions.
    """

    def __init__(self):
        self.task_to_skills: Dict[int, List[str]] = {}
        self.skill_to_tasks: Dict[str, List[str]] = {}
        self.skill_descriptions: Dict[str, str] = {}

    @classmethod
    def build_from_db_and_specs(
        cls, db: DatabaseManager, spec_service: SpecificationService
    ) -> 'InMemorySkillGraph':
        """
        Builds the skill graph from database problems and specification files.

        Args:
            db: DatabaseManager instance to fetch problems.
            spec_service: SpecificationService instance to fetch task and skill mappings.

        Returns:
            InMemorySkillGraph: Initialized skill graph.
        """
        graph = cls()

        # Load all problems from DB
        problems: List[Problem] = db.get_all_problems()

        # Initialize graph mappings
        task_to_skills = {}
        skill_to_tasks = {}
        skill_descriptions = {}

        # Populate task_to_skills from spec_service
        # Assuming spec_service has a method to get task-to-skills mapping
        # This requires spec_service to have loaded the ege_2026_math_spec.json
        for problem in problems:
            task_num = problem.task_number
            if task_num not in task_to_skills:
                task_to_skills[task_num] = []
            # Extend with kes_codes and kos_codes from the problem itself
            task_to_skills[task_num].extend(problem.kes_codes)
            task_to_skills[task_num].extend(problem.kos_codes)
            # Remove duplicates while preserving order
            task_to_skills[task_num] = list(dict.fromkeys(task_to_skills[task_num]))

        # Populate skill_to_tasks based on problems
        for problem in problems:
            all_codes = problem.kes_codes + problem.kos_codes
            for code in all_codes:
                if code not in skill_to_tasks:
                    skill_to_tasks[code] = []
                if problem.problem_id not in skill_to_tasks[code]:
                    skill_to_tasks[code].append(problem.problem_id)

        # Populate skill_descriptions from spec_service
        # Assuming spec_service has a method to get descriptions for KES/KOS codes
        # This requires spec_service to have loaded the ege_2026_math_kes_kos.json
        # Let's assume spec_service has an attribute kes_kos_map containing the mapping
        kes_kos_mapping = spec_service.kes_kos_map  # Исправлено: используем правильное имя атрибута
        for code, details in kes_kos_mapping.items():
            skill_descriptions[code] = details.get("description", f"Описание для {code}")

        # Assign to instance
        graph.task_to_skills = task_to_skills
        graph.skill_to_tasks = skill_to_tasks
        graph.skill_descriptions = skill_descriptions

        return graph

    def get_prerequisites_for_task(self, task_number: int) -> List[str]:
        """
        Returns the skill codes required for a given task number.
        In this implementation, it simply returns the skills associated with the task.

        Args:
            task_number: The task number (e.g., 1, 18).

        Returns:
            List[str]: A list of skill codes (KES/KOS) associated with the task.
        """
        return self.task_to_skills.get(task_number, [])

    def get_tasks_by_kes(self, kes_code: str) -> List[str]:
        """
        Returns a list of problem IDs associated with a given KES code.

        Args:
            kes_code: The KES code.

        Returns:
            List[str]: A list of problem IDs.
        """
        return self.skill_to_tasks.get(kes_code, [])
