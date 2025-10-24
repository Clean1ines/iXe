"""
Pydantic модель для представления задачи из ЕГЭ, спарсенной с сайта ФИПИ.
Содержит все необходимые атрибуты задачи в унифицированном формате.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Problem(BaseModel):
    """
    Модель задачи из ЕГЭ.

    Attributes:
        problem_id (str): Уникальный идентификатор задачи, например, 'init_0_40B442'.
        subject (str): Предмет, например, "mathematics".
        type (str): Тип задания по формату ЕГЭ, например, "A", "B", "task_1".
        text (str): Полный текст задачи, включая LaTeX.
        options (Optional[List[str]]): Варианты ответа, если применимо.
        answer (str): Эталонный ответ, может быть выражением.
        solutions (Optional[List[Dict[str, Any]]]): Список решений, каждое с id, text, author.
        topics (List[str]): Список идентификаторов тем, например, ["algebra.equations"].
        skills (Optional[List[str]]): Список идентификаторов навыков.
        difficulty (str): Уровень сложности, например, "easy", "medium", "hard".
        source_url (Optional[str]): URL оригинальной задачи на сайте ФИПИ.
        raw_html_path (Optional[str]): Путь к файлу с оригинальным HTML, если сохраняется.
        created_at (datetime): Дата/время создания записи.
        updated_at (Optional[datetime]): Дата/время последнего обновления.
        metadata (Optional[Dict[str, Any]]): Дополнительные данные.
    """
    problem_id: str
    subject: str
    type: str
    text: str
    options: Optional[List[str]] = None
    answer: str
    solutions: Optional[List[Dict[str, Any]]] = None
    topics: List[str]
    skills: Optional[List[str]] = None
    difficulty: str
    source_url: Optional[str] = None
    raw_html_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
