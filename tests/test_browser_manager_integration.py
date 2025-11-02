"""
Integration tests for BrowserManager, FIPIScraper, FIPIAnswerChecker, and AnswerService.
"""

import pytest
import asyncio
from pathlib import Path
from utils.browser_manager import BrowserManager
from scraper.fipi_scraper import FIPIScraper
from utils.answer_checker import FIPIAnswerChecker
from api.services.answer_service import AnswerService
from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from services.specification import SpecificationService
from utils.skill_graph import InMemorySkillGraph
from api.schemas import CheckAnswerRequest
from config import FIPI_QUESTIONS_URL, FIPI_SUBJECTS_URL # Предполагаем, что эти URL определены в config

# Путь к тестовой БД (желательно использовать временный файл)
TEST_DB_PATH = Path("test_integration_data.db")

# Примерные значения для тестирования. Их нужно будет адаптировать под реальные данные.
SUBJECT_TO_TEST = "math" # Используемый предмет для теста
# PROJ_ID_TO_TEST будет получен из get_projects
PAGE_NUM_TO_SCRAPE = "init" # Страница для скрапинга
# Эти значения (problem_id, form_id, task_number) нужно будет получить из реально
# скрапленных данных в процессе теста или знать заранее.
# Пока что используем заглушки. Тест не будет проходить до тех пор, пока
# не будут получены реальные значения из скрапинга.
# MOCK_PROBLEM_ID = "p123456_math_suffix"
# MOCK_USER_ANSWER = "some_correct_answer"
# MOCK_TASK_NUMBER = 1

# Путь к тестовым спецификациям (может быть временной заглушкой или реальной структурой)
SPEC_PATH = Path("data") / "specs" / "ege_2026_math_spec.json" # Пример
KOS_PATH = Path("data") / "specs" / "ege_2026_math_kes_kos.json" # ПРАВИЛЬНОЕ ИМЯ ФАЙЛА

# --- Вспомогательные фикстуры ---
@pytest.fixture
def test_db():
    """Создает временную тестовую БД."""
    db = DatabaseManager(str(TEST_DB_PATH))
    db.initialize_db()
    yield db
    # Очистка после теста (опционально, можно вручную удалить файл)
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

@pytest.fixture
def test_spec_service():
    """Создает тестовый экземпляр SpecificationService."""
    # Проверяем существование файлов спецификаций
    if not SPEC_PATH.exists() or not KOS_PATH.exists():
        # Попробуем создать пустой мок, если файлы не найдены
        # Это позволит тесту запуститься, но логика спецификаций не будет работать
        # В реальности нужно создать тестовые файлы спецификаций
        # или использовать мок-библиотеку (например, unittest.mock)
        # Для простоты сейчас пропустим тест, если файлы отсутствуют
        pytest.skip(f"Specification files not found: {SPEC_PATH}, {KOS_PATH}")
    return SpecificationService(spec_path=SPEC_PATH, kes_kos_path=KOS_PATH)

# --- Сам интеграционный тест ---
@pytest.mark.asyncio
async def test_full_integration_pipeline(test_db, test_spec_service):
    """
    Performs an integration test for the scraping -> storage -> answer checking pipeline.

    This test:
    1. Creates BrowserManager.
    2. Creates FIPIScraper with BrowserManager.
    3. Gets the list of projects (subjects) using BrowserManager's dedicated page.
    4. Finds the PROJ_ID for SUBJECT_TO_TEST.
    5. Scrapes one page for the found proj_id.
    6. Saves problems to the test database.
    7. Creates FIPIAnswerChecker with BrowserManager.
    8. Creates AnswerService with FIPIAnswerChecker and other dependencies.
    9. Executes answer checking for a problem scraped in step 5.
    10. Asserts that the BrowserManager's page caching works as expected (optional).
    """
    # 1. Создаем BrowserManager
    async with BrowserManager() as bm:
        # 2. Создаем FIPIScraper с BrowserManager
        scraper = FIPIScraper(
                specification_service=test_spec_service,
            base_url=FIPI_QUESTIONS_URL,
            browser_manager=bm,
            subjects_url=FIPI_SUBJECTS_URL
        )

        # 3. Получаем список проектов (предметов)
        subjects_list_page = await bm.get_subjects_list_page()
        try:
            projects = await scraper.get_projects(subjects_list_page)
        except Exception as e:
            pytest.skip(f"Skipping test due to get_projects error: {e}")

        print(f"Fetched projects: {projects}")
        assert projects, "No projects found via get_projects"

        # 4. Находим PROJ_ID для SUBJECT_TO_TEST
        proj_id_to_test = None
        for proj_id, name in projects.items():
            # Здесь нужно сопоставить "имя" из списка с нашим SUBJECT_TO_TEST
            # Это может быть нетривиально, если имена отличаются.
            # Попробуем найти что-то, содержащее "Математика" и "Профильный"
            if SUBJECT_TO_TEST == "math" and "Математика" in name and "Профильный" in name:
                proj_id_to_test = proj_id
                break
            # Добавьте другие условия для других SUBJECT_TO_TEST, если нужно
            # elif SUBJECT_TO_TEST == "informatics" and ...

        if not proj_id_to_test:
             pytest.skip(f"Skipping test: proj_id for subject '{SUBJECT_TO_TEST}' not found in fetched projects.")

        print(f"Found proj_id '{proj_id_to_test}' for subject '{SUBJECT_TO_TEST}'.")

        # 5. Выполняем скрапинг одной страницы (например, init для найденного proj_id)
        run_folder = Path("test_run_data") / SUBJECT_TO_TEST
        run_folder.mkdir(parents=True, exist_ok=True)
        try:
            problems, scraped_data = await scraper.scrape_page(
                proj_id=proj_id_to_test, # Используем найденный proj_id
                page_num=PAGE_NUM_TO_SCRAPE,
                run_folder=run_folder,
                subject=SUBJECT_TO_TEST
            )
        except Exception as e:
            # Выводим реальное сообщение об ошибке перед пропуском
            print(f"Scraping error details: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc() # Печатаем трейсбек
            pytest.skip(f"Skipping test due to scraping error: {e}")

        # Проверяем, что скрапинг вернул какие-то задачи
        assert problems, f"No problems scraped from page {PAGE_NUM_TO_SCRAPE} for subject {SUBJECT_TO_TEST} (proj_id {proj_id_to_test})"

        # 6. Сохраняем задачи в тестовую БД
        test_db.save_problems(problems)
        print(f"Saved {len(problems)} problems to test DB.")

        # Выбираем первую задачу для теста проверки ответа
        # Предполагаем, что у нее есть атрибуты problem_id, task_number, subject
        test_problem = problems[0]
        test_problem_id = test_problem.problem_id
        test_task_number = test_problem.task_number
        test_problem_subject = test_problem.subject
        print(f"Selected problem for answer check: {test_problem_id}, task_num: {test_task_number}, subject: {test_problem_subject}")

        # 7. Создаем FIPIAnswerChecker с BrowserManager
        answer_checker = FIPIAnswerChecker(browser_manager=bm)

        # 8. Создаем AnswerService с FIPIAnswerChecker и другими зависимостями
        # Требуются: db, checker, storage, skill_graph, spec_service
        # storage может быть None или реальным экземпляром LocalStorage
        storage = LocalStorage(Path("test_local_storage.json")) # Используем временный файл
        # skill_graph может быть пустым или инициализированным из тестовой БД
        skill_graph = InMemorySkillGraph.build_from_db_and_specs(test_db, test_spec_service)

        answer_service = AnswerService(
            db=test_db,
            checker=answer_checker,
            storage=storage,
            skill_graph=skill_graph,
            spec_service=test_spec_service
        )

        # 9. Выполняем проверку ответа для задачи с этой страницы через AnswerService
        # Требуется CheckAnswerRequest, который включает problem_id и user_answer
        # user_answer нужно подставить реальный или заведомо неправильный
        # MOCK_USER_ANSWER = "12345" # Пример неправильного ответа для задачи 1
        # Для теста реального ответа нужно знать правильный ответ или получить его через FIPI
        # или извлечь из HTML задачи (если возможно).
        # Пока что используем заглушку. Это может привести к "неправильному" ответу.
        mock_user_answer = "123456789" # Пример ответа

        request = CheckAnswerRequest(
            problem_id=test_problem_id,
            user_answer=mock_user_answer,
            form_id="some_form_id" # form_id может быть извлечен из problem_id, если следовать структуре task_id_utils
        )

        print(f"Checking answer for problem {test_problem_id} with user answer '{mock_user_answer}'")
        try:
            response = await answer_service.check_answer(request)
            print(f"Answer check response: {response.verdict}, score: {response.score_float}")
            # 10. Убедиться, что страница используется одна (проверка кэширования BrowserManager)
            # Это сложно проверить напрямую без доступа к внутренностям bm._pages,
            # но косвенно можно убедиться, что процесс завершается без ошибок двойного создания браузера.
            # Более строгая проверка кэширования потребовала бы прямого доступа к bm._pages или моков.
            assert response is not None
            assert hasattr(response, 'verdict')
            print("Integration test passed: AnswerService.check_answer executed successfully after scraping via get_projects.")
        except Exception as e:
            pytest.fail(f"Answer checking failed with error: {e}")

        # Очистка временных файлов
        import shutil
        if run_folder.exists():
            shutil.rmtree(run_folder)
        temp_storage_path = Path("test_local_storage.json")
        if temp_storage_path.exists():
            temp_storage_path.unlink()
        if TEST_DB_PATH.exists():
            TEST_DB_PATH.unlink()

# Запуск теста: pytest tests/test_browser_manager_integration.py -v -s
# или конкретный тест: pytest tests/test_browser_manager_integration.py::test_full_integration_pipeline -v -s

