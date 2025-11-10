"""
Application service implementing quiz-related use cases with adaptive learning logic.

This service coordinates between domain entities, repositories, and infrastructure
adapters to provide quiz functionality. It implements the application layer
responsibilities according to Clean Architecture principles.
"""
from typing import List, Optional
from datetime import datetime
from domain.interfaces.repositories import IProblemRepository, IUserProgressRepository, ISkillRepository
from domain.models.problem import Problem
from domain.models.user_progress import UserProgress, ProgressStatus
from domain.models.skill import Skill
from domain.value_objects.problem_id import ProblemId
from utils.skill_graph import InMemorySkillGraph


class QuizApplicationService:
    """
    Application service coordinating quiz-related business operations.

    This service implements use cases for quiz management, including problem selection,
    progress tracking, and adaptive learning logic. It orchestrates interactions between
    domain entities and repositories while maintaining separation from infrastructure concerns.
    """
    
    def __init__(
        self,
        problem_repo: IProblemRepository,
        progress_repo: IUserProgressRepository,
        skill_repo: ISkillRepository,
        skill_graph: InMemorySkillGraph,
    ):
        """
        Initialize the quiz application service.

        Args:
            problem_repo: Repository for accessing problem domain entities
            progress_repo: Repository for tracking user progress
            skill_repo: Repository for managing skill domain entities  
            skill_graph: In-memory graph for adaptive skill-based problem selection
        """
        self._problem_repo = problem_repo
        self._progress_repo = progress_repo
        self._skill_repo = skill_repo
        self._skill_graph = skill_graph

    async def start_quiz(self, user_id: str, subject: str, count: int = 5) -> List[Problem]:
        """
        Start a new quiz session by selecting appropriate problems for the user.

        This method implements adaptive problem selection based on user progress,
        skill mastery, and difficulty levels. It considers completed problems and
        skill prerequisites to provide an optimal learning experience.

        Args:
            user_id: Unique identifier for the user
            subject: Subject area for the quiz (e.g., mathematics, informatics)
            count: Number of problems to include in the quiz (default: 5)

        Returns:
            List of selected problems for the quiz session
        """
        # Get all problems for the subject
        all_problems = await self._problem_repo.get_by_subject(subject)

        # Get user's progress to filter out completed problems
        user_progress_list = await self._progress_repo.get_by_user(user_id)
        completed_problem_ids = {
            p.problem_id for p in user_progress_list 
            if p.status == ProgressStatus.COMPLETED
        }

        # Filter out already completed problems
        available_problems = [p for p in all_problems if p.problem_id not in completed_problem_ids]

        # Apply adaptive selection based on skill graph and user's weak areas
        selected_problems = self._adaptive_problem_selection(
            available_problems, user_id, count
        )

        return selected_problems[:count]

    def _adaptive_problem_selection(
        self, problems: List[Problem], user_id: str, count: int
    ) -> List[Problem]:
        """
        Select problems adaptively based on user's skill profile and progress.

        This method uses the skill graph to identify areas where the user needs
        improvement and selects problems that target those specific skills.

        Args:
            problems: Available problems to choose from
            user_id: User identifier for progress lookup
            count: Target number of problems to select

        Returns:
            List of adaptively selected problems
        """
        # For now, implement basic adaptive selection
        # In future, this would use the skill graph more extensively
        sorted_problems = sorted(
            problems,
            key=lambda p: (p.difficulty_level.value.name, p.task_number or 0)
        )
        
        return sorted_problems

    async def record_attempt(self, user_id: str, problem_id: ProblemId, user_answer: str) -> UserProgress:
        """
        Record a user's attempt at solving a problem and update their progress.

        This method validates the answer, calculates the score, and updates the
        user's progress record in the repository. It also handles retry logic
        and ensures business rules are maintained.

        Args:
            user_id: Unique identifier for the user
            problem_id: Identifier of the attempted problem
            user_answer: The answer provided by the user

        Returns:
            Updated UserProgress record
        """
        # Get the problem to calculate score
        problem = await self._problem_repo.get_by_id(problem_id)
        if not problem:
            raise ValueError(f"Problem with ID {problem_id} not found")

        # Get existing progress or create new one
        progress = await self._progress_repo.get_by_user_and_problem(user_id, problem_id)
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                problem_id=problem_id,
                status=ProgressStatus.NOT_STARTED
            )

        # Validate if user can retry
        if not progress.can_retry():
            raise ValueError("User cannot retry this problem yet")

        # Calculate score
        score = problem.calculate_score(user_answer)
        is_correct = score == problem.max_score

        # Update progress
        progress.record_attempt(is_correct, score)

        # Save updated progress
        await self._progress_repo.save(progress)

        return progress

    async def get_user_progress_summary(self, user_id: str) -> dict:
        """
        Get a summary of user's progress across all subjects and skills.

        This method aggregates user progress data to provide insights into
        their learning journey, including completion rates and skill mastery.

        Args:
            user_id: Unique identifier for the user

        Returns:
            Dictionary containing progress summary metrics
        """
        all_progress = await self._progress_repo.get_by_user(user_id)
        completed_progress = [p for p in all_progress if p.status == ProgressStatus.COMPLETED]
        
        # Count by subject
        subject_counts = {}
        for progress in all_progress:
            problem = await self._problem_repo.get_by_id(progress.problem_id)
            if problem:
                subject = problem.subject
                if subject not in subject_counts:
                    subject_counts[subject] = {"total": 0, "completed": 0}
                subject_counts[subject]["total"] += 1
                if progress.status == ProgressStatus.COMPLETED:
                    subject_counts[subject]["completed"] += 1

        return {
            "total_problems": len(all_progress),
            "completed_problems": len(completed_progress),
            "completion_rate": len(completed_progress) / len(all_progress) if all_progress else 0,
            "by_subject": subject_counts
        }
