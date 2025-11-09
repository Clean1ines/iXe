import logging
from typing import Dict, List
from infrastructure.adapters.database_adapter import DatabaseAdapter
from infrastructure.adapters.specification_adapter import SpecificationAdapter
from domain.models.problem_schema import Problem

logger = logging.getLogger(__name__)


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
        cls, db: DatabaseAdapter, spec_service: SpecificationAdapter
    ) -> 'InMemorySkillGraph':
        """
        Builds the skill graph from database problems and specification files.
        """
        logger.info("🔍 Starting to build InMemorySkillGraph...")
        graph = cls()

        problems: List[Problem] = db.get_all_problems()
        logger.info(f"✅ Loaded {len(problems)} problems from database")

        task_to_skills = {}
        skill_to_tasks = {}
        skill_descriptions = {}

        for problem in problems:
            task_num = problem.task_number
            if task_num not in task_to_skills:
                task_to_skills[task_num] = []
            combined_codes = problem.kes_codes + problem.kos_codes
            seen = set()
            unique_codes = []
            for code in combined_codes:
                if code not in seen:
                    unique_codes.append(code)
                    seen.add(code)
            task_to_skills[task_num] = unique_codes

        for problem in problems:
            all_codes = problem.kes_codes + problem.kos_codes
            for code in all_codes:
                if code not in skill_to_tasks:
                    skill_to_tasks[code] = []
                if problem.problem_id not in skill_to_tasks[code]:
                    skill_to_tasks[code].append(problem.problem_id)

        kes_kos_mapping = spec_service.kes_kos_map
        for code, details in kes_kos_mapping.items():
            skill_descriptions[code] = details.get("description", f"Description for {code}")

        graph.task_to_skills = task_to_skills
        graph.skill_to_tasks = skill_to_tasks
        graph.skill_descriptions = skill_descriptions

        logger.info("✅ InMemorySkillGraph built successfully")
        return graph

    def get_codes_for_task(self, task_number: int) -> List[str]:
        return self.task_to_skills.get(task_number, [])

    def get_tasks_by_kes(self, kes_code: str) -> List[str]:
        return self.skill_to_tasks.get(kes_code, [])


# Global cache variable
_skill_graph_cache: InMemorySkillGraph | None = None


def get_skill_graph_cached(db: DatabaseAdapter, spec_service: SpecificationAdapter) -> InMemorySkillGraph:
    """
    Returns a cached instance of InMemorySkillGraph.
    Builds it on the first call using the provided dependencies.
    """
    global _skill_graph_cache
    if _skill_graph_cache is None:
        _skill_graph_cache = InMemorySkillGraph.build_from_db_and_specs(db, spec_service)
    return _skill_graph_cache
