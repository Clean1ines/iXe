"""
SQLAlchemy ORM-модели для хранения задач, пользовательских ответов и прогресса.

Соответствуют обновлённой доменной модели Problem и текущему воркфлоу.
"""

import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DBProblem(Base):
    """
    ORM-модель задачи из ЕГЭ.

    Соответствует обновлённой доменной модели `Problem`.
    """
    __tablename__ = "problems"

    problem_id: str = sa.Column(sa.String, primary_key=True, nullable=False)
    subject: str = sa.Column(sa.String, nullable=False)
    type: str = sa.Column(sa.String, nullable=False)
    text: str = sa.Column(sa.Text, nullable=False)
    options = sa.Column(sa.JSON, nullable=True)
    answer: Optional[str] = sa.Column(sa.Text, nullable=True)  # Может быть NULL
    topics = sa.Column(sa.JSON, nullable=False)  # Синоним kes_codes
    difficulty_level: str = sa.Column(sa.String, nullable=False)
    task_number: int = sa.Column(sa.Integer, nullable=False)
    kes_codes = sa.Column(sa.JSON, nullable=False)
    kos_codes = sa.Column(sa.JSON, nullable=False)
    exam_part: str = sa.Column(sa.String, nullable=False)
    max_score: int = sa.Column(sa.Integer, nullable=False)
    form_id: Optional[str] = sa.Column(sa.String, nullable=True)
    source_url: Optional[str] = sa.Column(sa.String, nullable=True)
    raw_html_path: Optional[str] = sa.Column(sa.String, nullable=True)
    created_at: datetime.datetime = sa.Column(sa.DateTime, nullable=False)
    updated_at: Optional[datetime.datetime] = sa.Column(sa.DateTime, nullable=True)
    metadata_: Optional[dict] = sa.Column("metadata", sa.JSON, nullable=True)
    solutions = sa.Column(sa.JSON, nullable=True)  # Добавляем поле solutions
    skills = sa.Column(sa.JSON, nullable=True)  # Добавляем поле skills

    answers = relationship("DBAnswer", back_populates="problem", cascade="all, delete-orphan")


class DBAnswer(Base):
    """
    ORM-модель пользовательского ответа на задачу.
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
    )
    is_correct = sa.Column(sa.Boolean)  # Новое поле
    score = sa.Column(sa.Float)         # Новое поле
    timestamp: datetime.datetime = sa.Column(
        sa.DateTime,
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    problem = relationship("DBProblem", back_populates="answers")


class DBUserProgress(Base):
    """
    ORM-модель прогресса пользователя по задаче.
    """
    __tablename__ = "user_progress"

    user_id: str = sa.Column(sa.String, primary_key=True)
    problem_id: str = sa.Column(
        sa.String,
        sa.ForeignKey("problems.problem_id", ondelete="CASCADE"),
        primary_key=True,
    )
    status: str = sa.Column(sa.String, nullable=False)  # NOT_STARTED, IN_PROGRESS, COMPLETED
    score: float = sa.Column(sa.Float, nullable=False, default=0.0)
    attempts: int = sa.Column(sa.Integer, nullable=False, default=0)
    last_attempt_at: Optional[datetime.datetime] = sa.Column(sa.DateTime, nullable=True)
    started_at: datetime.datetime = sa.Column(
        sa.DateTime, 
        nullable=False, 
        default=lambda: datetime.datetime.now(datetime.UTC)
    )

    problem = relationship("DBProblem")


class DBSkill(Base):
    """
    ORM-модель навыка для адаптивного обучения.
    """
    __tablename__ = "skills"

    skill_id: str = sa.Column(sa.String, primary_key=True)
    name: str = sa.Column(sa.String, nullable=False)
    description: str = sa.Column(sa.Text, nullable=True)
    prerequisites = sa.Column(sa.JSON, nullable=False, default=list)  # Список skill_id
    related_problems = sa.Column(sa.JSON, nullable=False, default=list)  # Список problem_id
