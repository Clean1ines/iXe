"""
SQLAlchemy ORM-модели для хранения задач и пользовательских ответов.

Эти модели заменяют текущее хранение в JSON-файлах и обеспечивают
типизированное, надёжное и масштабируемое взаимодействие с SQLite.
"""

import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DBProblem(Base):
    """
    ORM-модель задачи из ЕГЭ.

    Соответствует Pydantic-модели `Problem`, но адаптирована под реляционную БД.
    Используется для хранения метаданных и содержимого задачи.
    """
    __tablename__ = "problems"

    problem_id: str = sa.Column(sa.String, primary_key=True, nullable=False)
    subject: str = sa.Column(sa.String, nullable=False)
    type: str = sa.Column(sa.String, nullable=False)
    text: str = sa.Column(sa.Text, nullable=False)
    options = sa.Column(sa.JSON, nullable=True)  # List[str] or None
    answer: str = sa.Column(sa.Text, nullable=False)
    solutions = sa.Column(sa.JSON, nullable=True)  # List[Dict[str, Any]] or None
    topics = sa.Column(sa.JSON, nullable=False)  # List[str]
    skills = sa.Column(sa.JSON, nullable=True)  # List[str] or None
    # --- Изменено: Заменено 'difficulty' на 'difficulty_level' ---
    difficulty_level: str = sa.Column(sa.String, nullable=False)
    # --- Добавлены новые поля ---
    task_number: int = sa.Column(sa.Integer, nullable=False)
    kes_codes = sa.Column(sa.JSON, nullable=False)  # List[str], default_factory=list -> nullable=False, default=[]
    kos_codes = sa.Column(sa.JSON, nullable=False)  # List[str], default_factory=list -> nullable=False, default=[]
    exam_part: str = sa.Column(sa.String, nullable=False)
    max_score: int = sa.Column(sa.Integer, nullable=False)
    form_id: Optional[str] = sa.Column(sa.String, nullable=True) # Сделано опциональным
    # --- /Новые поля ---
    source_url: Optional[str] = sa.Column(sa.String, nullable=True)
    raw_html_path: Optional[str] = sa.Column(sa.String, nullable=True)
    created_at: datetime.datetime = sa.Column(sa.DateTime, nullable=False)
    updated_at: Optional[datetime.datetime] = sa.Column(sa.DateTime, nullable=True)
    metadata_ = sa.Column("metadata", sa.JSON, nullable=True)  # renamed to avoid conflict with SQLAlchemy's metadata

    # Связь один-ко-многим с ответами (если потребуется)
    answers = relationship("DBAnswer", back_populates="problem", cascade="all, delete-orphan")


class DBAnswer(Base):
    """
    ORM-модель пользовательского ответа на задачу.

    Хранит ответ, статус проверки и временную метку.
    Предполагается один пользователь (user_id опционален и может быть константой).
    """
    __tablename__ = "answers"

    problem_id: str = sa.Column(
        sa.String,
        sa.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: str = sa.Column(sa.String, primary_key=True, default="default_user")
    user_answer: str = sa.Column(sa.Text, nullable=False)
    status: str = sa.Column(
        sa.String,
        nullable=False,
        default="not_checked"
    )  # "not_checked", "correct", "incorrect"
    timestamp: datetime.datetime = sa.Column(
        sa.DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    # Связь с задачей
    problem = relationship("DBProblem", back_populates="answers")
