"""
Модуль для сохранения и загрузки задач Problem в формате JSONL.
"""
import json
from pathlib import Path
from typing import List, Optional

from models.problem_schema import Problem


class ProblemStorage:
    """
    Класс для хранения задач Problem в файле формата JSONL.

    Attributes:
        storage_path (Path): Путь к файлу для хранения задач в формате JSONL.
    """

    def __init__(self, storage_path: Path):
        """
        Инициализирует ProblemStorage с указанным путем к файлу.

        Args:
            storage_path (Path): Путь к файлу .jsonl для хранения задач.
        """
        self.storage_path = storage_path

    def save_problem(self, problem: Problem) -> None:
        """
        Сохраняет одну задачу в конец файла JSONL.

        Args:
            problem (Problem): Объект задачи для сохранения.
        """
        with self.storage_path.open('a', encoding='utf-8') as f:
            f.write(problem.model_dump_json() + '\n')

    def save_problems(self, problems: List[Problem]) -> None:
        """
        Сохраняет список задач в конец файла JSONL.

        Args:
            problems (List[Problem]): Список объектов задач для сохранения.
        """
        with self.storage_path.open('a', encoding='utf-8') as f:
            for problem in problems:
                f.write(problem.model_dump_json() + '\n')

    def load_all_problems(self) -> List[Problem]:
        """
        Загружает все задачи из файла JSONL.

        Returns:
            List[Problem]: Список задач, загруженных из файла.
                           Возвращает пустой список, если файл не существует или пуст.
        """
        if not self.storage_path.exists():
            return []
        problems = []
        with self.storage_path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Пропускаем пустые строки
                    problem_data = json.loads(line)
                    problem = Problem.model_validate(problem_data)
                    problems.append(problem)
        return problems

    def get_problem_by_id(self, problem_id: str) -> Optional[Problem]:
        """
        Находит задачу по её идентификатору.

        Args:
            problem_id (str): Уникальный идентификатор задачи.

        Returns:
            Optional[Problem]: Объект задачи, если найден, иначе None.
        """
        # Для простоты читаем все задачи. В будущем можно оптимизировать.
        all_problems = self.load_all_problems()
        for problem in all_problems:
            if problem.problem_id == problem_id:
                return problem
        return None
