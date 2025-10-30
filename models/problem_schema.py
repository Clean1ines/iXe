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
        subject (str): Предмет, например, "mathematics", "informatics", "russian".
        type (str): Тип задания по формату ЕГЭ, например, "A", "B", "task_1".
        text (str): Полный текст задачи, включая LaTeX.
        offline_html (Optional[str]): HTML-фрагмент задачи с встроенными base64 изображениями для оффлайн-режима. Может быть null.
        options (Optional[List[str]]): Варианты ответа, если применимо. Может быть null.
        answer (str): Эталонный ответ, может быть выражением.
        solutions (Optional[List[Dict[str, Any]]]): Список решений. Каждое решение - это словарь с полями,
        такими как 'solution_id', 'text', 'author'. Может быть null.
        topics (List[str]): Список идентификаторов тем, например, ["algebra.equations"].
        skills (Optional[List[str]]): Список идентификаторов навыков. Может быть null.
        difficulty_level (str): Уровень сложности по официальной шкале ЕГЭ: "basic", "advanced", "high".
        task_number (int): Номер задачи в экзаменационной работе (1–19).
        kes_codes (List[str]): Список кодов КЭС (кодификатора элементов содержания).
        kos_codes (List[str]): Список кодов КОС (кодификатора требований к уровню подготовки).
        exam_part (str): Часть экзамена: "Part 1" или "Part 2".
        max_score (int): Максимальный балл за выполнение задачи (1–4).
        form_id (Optional[str]): Идентификатор формы отправки ответа, извлекается из кнопки на странице FIPI. Может быть null для задач без формы.
        source_url (Optional[str]): URL оригинальной задачи на сайте ФИПИ. Может быть null.
        raw_html_path (Optional[str]): Путь к файлу с оригинальным HTML, если сохраняется. Может быть null.
        created_at (datetime): Дата/время создания записи в формате ISO8601.
        updated_at (Optional[datetime]): Дата/время последнего обновления в формате ISO8601. Может быть null.
        metadata (Optional[Dict[str, Any]]): Дополнительные данные. Может быть null.
    """
problem_id: str
subject: str
type: str
text: str
offline_html: Optional[str] = None
options: Optional[List[str]] = None
answer: str
solutions: Optional[List[Dict[str, Any]]] = None
topics: List[str]
skills: Optional[List[str]] = None
difficulty_level: str
task_number: int
kes_codes: List[str] = Field(default_factory=list)
kos_codes: List[str] = Field(default_factory=list)
exam_part: str
max_score: int
form_id: Optional[str] = None # Сделано опциональным
source_url: Optional[str] = None
raw_html_path: Optional[str] = None
created_at: datetime
updated_at: Optional[datetime] = None
metadata: Optional[Dict[str, Any]] = None
