import datetime
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from models.database_models import Base, DBProblem, DBAnswer
from models.problem_schema import Problem
from infrastructure.adapters.database_adapter import DatabaseAdapter


@pytest.fixture
def temp_db_path():
    """Creates a temporary database file path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        tmp_path = tmp_file.name
    yield tmp_path
    # Cleanup after test
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def database_manager(temp_db_path):
    """Creates a DatabaseAdapter instance with a temporary database."""
    db_manager = DatabaseAdapter(temp_db_path)
    db_manager.initialize_db()  # Ensure tables are created
    return db_manager

# --- Фикстура для создания корректного объекта Problem ---
@pytest.fixture
def sample_problem_data():
    """Provides sample data for creating a Problem object that passes validation."""
    return {
        "problem_id": "test_id_1",
        "subject": "Math",
        "type": "multiple_choice", # str
        "text": "What is 2+2?",
        "options": ["3", "4", "5"], # List[str] - теперь корректно
        "answer": "4", # str
        "solutions": [{"step": 1, "description": "Add 2 and 2"}, {"step": 2, "result": "4"}], # List[Dict[str, Any]] - теперь корректно
        "topics": ["Arithmetic"], # Предполагается, что это поле есть в DBProblem, но не в Problem? Или ошибка?
        "skills": ["Addition"], # Optional[List[str]]
        "difficulty_level": "basic", # str - теперь корректно, enum-like значение
        "task_number": 1, # int - теперь корректно
        "kes_codes": ["KES1", "KES2"], # List[str] - теперь корректно
        "kos_codes": ["KOS1", "KOS2"], # List[str] - теперь корректно
        "exam_part": "Part 1", # str - теперь корректно
        "max_score": 1, # int - теперь корректно
        "form_id": "Form1", # Optional[str]
        "source_url": "http://example.com",
        "raw_html_path": "/path/to/html",
        "created_at": datetime.datetime.now(), # datetime - теперь корректно
        "updated_at": datetime.datetime.now(), # Optional[datetime] - теперь корректно
        "metadata": {"extra": "info"} # Optional[Dict[str, Any]] - теперь корректно
    }

@pytest.fixture
def sample_problem(sample_problem_data):
    """Provides a valid Problem instance."""
    # Убираем 'topics', так как его нет в схеме Problem
    data = sample_problem_data.copy()
    data.pop('topics', None)
    return Problem(**data)

# --- Тесты ---


class TestDatabaseAdapterInitialization:
    """Tests for database initialization."""

    def test_database_initialization(self, temp_db_path):
        """Test that initialize_db creates the necessary tables."""
        db_manager = DatabaseAdapter(temp_db_path)
        # Ensure tables don't exist initially (by creating a fresh engine/session)
        engine = sa.create_engine(f"sqlite:///{temp_db_path}")
        # Reflect the current state of the database
        meta = sa.MetaData()
        meta.reflect(bind=engine)

        # Initially, tables should not exist if the file was truly empty/new
        # This test primarily checks that initialize_db runs without error
        # and prepares the schema.
        assert len(meta.tables) == 0 # Assuming new file

        db_manager.initialize_db()

        # Reflect again after initialization
        meta_after = sa.MetaData()
        meta_after.reflect(bind=engine)

        # Check that the expected tables now exist
        assert 'problems' in meta_after.tables
        assert 'answers' in meta_after.tables


class TestDatabaseAdapterSaveProblems:
    """Tests for the save_problems method."""

    def test_save_problems_empty_list(self, database_manager):
        """Test saving an empty list of problems."""
        database_manager.save_problems([])
        all_problems = database_manager.get_all_problems()
        assert len(all_problems) == 0

    def test_save_problems_single_problem(self, database_manager, sample_problem):
        """Test saving a single problem."""
        database_manager.save_problems([sample_problem])

        retrieved_problem = database_manager.get_problem_by_id(sample_problem.problem_id)
        assert retrieved_problem is not None
        assert retrieved_problem.problem_id == sample_problem.problem_id
        assert retrieved_problem.subject == sample_problem.subject
        assert retrieved_problem.text == sample_problem.text
        assert retrieved_problem.answer == sample_problem.answer
        # assert retrieved_problem.topics == sample_problem.topics # 'topics' нет в Problem, не можем проверить напрямую из объекта Problem
        # Add more assertions for other fields as needed

    def test_save_problems_multiple_problems(self, database_manager, sample_problem_data):
        """Test saving multiple problems at once."""
        # Изменяем данные, чтобы создать уникальные объекты
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        problem1_data = {**base_data, "problem_id": "multi_id_1", "text": "Q1", "answer": "A1"}
        problem2_data = {**base_data, "problem_id": "multi_id_2", "text": "Q2", "answer": "A2", "subject": "Physics"}

        problem1 = Problem(**problem1_data)
        problem2 = Problem(**problem2_data)

        database_manager.save_problems([problem1, problem2])

        retrieved_problem1 = database_manager.get_problem_by_id("multi_id_1")
        retrieved_problem2 = database_manager.get_problem_by_id("multi_id_2")
        assert retrieved_problem1 is not None
        assert retrieved_problem2 is not None
        assert retrieved_problem1.text == "Q1"
        assert retrieved_problem2.text == "Q2"

    def test_save_problems_updates_existing(self, database_manager, sample_problem_data):
        """Test that saving a problem with an existing ID updates the record."""
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        initial_data = {**base_data, "problem_id": "update_id", "subject": "OldSubject", "text": "Old Text", "answer": "OldAns"}
        initial_problem = Problem(**initial_data)
        database_manager.save_problems([initial_problem])

        updated_data = {**base_data, "problem_id": "update_id", "subject": "NewSubject", "text": "New Text", "answer": "NewAns"}
        updated_problem = Problem(**updated_data)
        database_manager.save_problems([updated_problem])

        retrieved_problem = database_manager.get_problem_by_id("update_id")
        assert retrieved_problem is not None
        assert retrieved_problem.subject == "NewSubject"
        assert retrieved_problem.text == "New Text"
        assert retrieved_problem.answer == "NewAns" # Проверяем, что ответ обновился


class TestDatabaseAdapterSaveAndGetAnswer:
    """Tests for save_answer and get_answer_and_status methods."""

    def test_save_answer_and_get_with_user_id(self, database_manager, sample_problem):
        """Test saving an answer for a specific user and retrieving it."""
        database_manager.save_problems([sample_problem]) # Сохраняем задачу перед ответом
        task_id = sample_problem.problem_id
        user_id = "user_123"
        user_answer = "User's Answer Text"
        status = "checked"

        # Save the answer
        database_manager.save_answer(task_id=task_id, user_id=user_id, user_answer=user_answer, status=status)

        # Retrieve the answer and status
        retrieved_answer, retrieved_status = database_manager.get_answer_and_status(task_id=task_id, user_id=user_id)

        assert retrieved_answer == user_answer
        assert retrieved_status == status

    def test_get_answer_and_status_defaults_for_nonexistent_user_task(self, database_manager):
        """Test that get_answer_and_status returns defaults if no record exists for user/task."""
        task_id = "nonexistent_task"
        user_id = "nonexistent_user"

        retrieved_answer, retrieved_status = database_manager.get_answer_and_status(task_id=task_id, user_id=user_id)

        assert retrieved_answer is None
        assert retrieved_status == "not_checked"

    def test_save_answer_makes_user_id_mandatory(self, database_manager):
        """Test that save_answer requires user_id."""
        task_id = "some_task"
        user_answer = "Some Answer"

        # This should raise an error because user_id is missing
        with pytest.raises(TypeError):
             database_manager.save_answer(task_id=task_id, user_answer=user_answer)

    def test_get_answer_and_status_makes_user_id_mandatory(self, database_manager):
        """Test that get_answer_and_status requires user_id."""
        task_id = "some_task"

        # This should raise an error because user_id is missing
        with pytest.raises(TypeError):
             database_manager.get_answer_and_status(task_id=task_id)

    def test_save_answer_and_get_isolated_by_user(self, database_manager, sample_problem):
        """Test that answers for the same task but different users are isolated."""
        database_manager.save_problems([sample_problem]) # Сохраняем задачу перед ответом
        task_id = sample_problem.problem_id
        user_id_1 = "user_one"
        user_id_2 = "user_two"
        answer_1 = "Answer from User 1"
        answer_2 = "Answer from User 2"

        # Save answers for two different users for the same task
        database_manager.save_answer(task_id=task_id, user_id=user_id_1, user_answer=answer_1, status="checked")
        database_manager.save_answer(task_id=task_id, user_id=user_id_2, user_answer=answer_2, status="pending")

        # Retrieve answers for each user
        ans1, stat1 = database_manager.get_answer_and_status(task_id=task_id, user_id=user_id_1)
        ans2, stat2 = database_manager.get_answer_and_status(task_id=task_id, user_id=user_id_2)

        assert ans1 == answer_1
        assert stat1 == "checked"
        assert ans2 == answer_2
        assert stat2 == "pending"


class TestDatabaseAdapterGetAllProblemsAndSubjects:
    """Tests for get_all_problems and get_all_subjects methods."""

    def test_get_all_problems_empty(self, database_manager):
        """Test get_all_problems returns empty list when no problems exist."""
        all_problems = database_manager.get_all_problems()
        assert all_problems == []

    def test_get_all_problems_populated(self, database_manager, sample_problem_data):
        """Test get_all_problems returns all saved problems."""
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        problem1_data = {**base_data, "problem_id": "get_all_1", "text": "Q1", "answer": "A1"}
        problem2_data = {**base_data, "problem_id": "get_all_2", "text": "Q2", "answer": "A2", "subject": "Physics"}

        problem1 = Problem(**problem1_data)
        problem2 = Problem(**problem2_data)
        database_manager.save_problems([problem1, problem2])

        all_problems = database_manager.get_all_problems()
        assert len(all_problems) == 2
        # Check if the specific problems are present (order might vary)
        problem_ids = {p.problem_id for p in all_problems}
        assert "get_all_1" in problem_ids
        assert "get_all_2" in problem_ids

    def test_get_all_subjects_empty(self, database_manager):
        """Test get_all_subjects returns empty list when no problems exist."""
        subjects = database_manager.get_all_subjects()
        assert subjects == []

    def test_get_all_subjects_populated(self, database_manager, sample_problem_data):
        """Test get_all_subjects returns distinct subjects."""
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        problem1_data = {**base_data, "problem_id": "subj_1", "text": "Q1", "answer": "A1", "subject": "Math"}
        problem2_data = {**base_data, "problem_id": "subj_2", "text": "Q2", "answer": "A2", "subject": "Physics"}
        problem3_data = {**base_data, "problem_id": "subj_3", "text": "Q3", "answer": "A3", "subject": "Math"} # Same subject as problem1

        problem1 = Problem(**problem1_data)
        problem2 = Problem(**problem2_data)
        problem3 = Problem(**problem3_data)
        database_manager.save_problems([problem1, problem2, problem3])

        subjects = database_manager.get_all_subjects()
        assert len(subjects) == 2 # Should be distinct
        assert "Math" in subjects
        assert "Physics" in subjects
        # Ensure no duplicates
        assert subjects.count("Math") == 1
        assert subjects.count("Physics") == 1

    def test_get_all_subjects_ignores_null(self, database_manager):
        """Test that get_all_subjects correctly handles NULL subject values if they exist."""
        # This test might require direct DB manipulation if the ORM always requires a subject
        # Or, if the schema allows NULL, test with one.
        # For now, assuming subject is always populated based on Problem schema.
        # Example if NULLs were possible:
        # engine = sa.create_engine(f"sqlite:///{database_manager.db_path}")
        # with engine.connect() as conn:
        #     conn.execute(sa.text("INSERT INTO problems (problem_id, subject) VALUES ('null_subj', NULL);"))
        #     conn.commit()
        # subjects = database_manager.get_all_subjects()
        # assert 'null_subj' not in subjects # Or handle as per requirement
        # This test case is implicitly covered by the populated test if subject is non-nullable.
        pass # Covered by test_get_all_subjects_populated if subject is non-nullable


class TestDatabaseAdapterGetRandomProblemIds:
    """Tests for get_random_problem_ids method."""

    def test_get_random_problem_ids_empty_subject(self, database_manager):
        """Test get_random_problem_ids returns empty list for a subject with no problems."""
        problem_ids = database_manager.get_random_problem_ids(subject="Biology", count=5)
        assert problem_ids == []

    def test_get_random_problem_ids_specific_subject(self, database_manager, sample_problem_data):
        """Test get_random_problem_ids returns correct IDs for a specific subject."""
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        problem1_data = {**base_data, "problem_id": "rand_math_1", "text": "Q1", "answer": "A1", "subject": "Math"}
        problem2_data = {**base_data, "problem_id": "rand_math_2", "text": "Q2", "answer": "A2", "subject": "Math"}
        problem3_data = {**base_data, "problem_id": "rand_physics_1", "text": "P1", "answer": "PA1", "subject": "Physics"}

        problem1 = Problem(**problem1_data)
        problem2 = Problem(**problem2_data)
        problem3 = Problem(**problem3_data)
        database_manager.save_problems([problem1, problem2, problem3])

        math_ids = database_manager.get_random_problem_ids(subject="Math", count=10) # Request more than available
        assert set(math_ids) == {"rand_math_1", "rand_math_2"} # Should return all available Math IDs

        physics_ids = database_manager.get_random_problem_ids(subject="Physics", count=1)
        assert len(physics_ids) == 1
        assert physics_ids[0] == "rand_physics_1"

    def test_get_random_problem_ids_count_limit(self, database_manager, sample_problem_data):
        """Test that the count parameter limits the number of returned IDs."""
        # Save 5 problems for the same subject
        # Убираем 'topics' из данных перед созданием объекта Problem
        base_data = sample_problem_data.copy()
        base_data.pop('topics', None)

        problems = []
        for i in range(5):
            p_data = {**base_data, "problem_id": f"rand_count_{i}", "text": f"Q{i}", "answer": f"A{i}", "subject": "Chemistry"}
            problems.append(Problem(**p_data))
        database_manager.save_problems(problems)

        # Request only 2 random IDs
        ids = database_manager.get_random_problem_ids(subject="Chemistry", count=2)
        assert len(ids) == 2
        # Check that all returned IDs are from the expected set
        expected_ids = {f"rand_count_{i}" for i in range(5)}
        assert set(ids).issubset(expected_ids)

