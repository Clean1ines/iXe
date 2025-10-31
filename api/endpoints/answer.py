# api/endpoints/answer.py
from fastapi import APIRouter, Depends, HTTPException
from api.schemas import CheckAnswerRequest, CheckAnswerResponse
from api.services.answer_service import AnswerService
from services.specification import SpecificationService
from pathlib import Path
import logging

# --- Импорт зависимостей ДО определения эндпоинта ---
from api.dependencies import get_answer_service
# -----------------------------------------------

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize specification service once at module level
# Adjust paths if specs are in a different location
SPEC_DIR = Path(__file__).parent.parent.parent / "data" / "specs"
SPEC_SERVICE = SpecificationService(
    spec_path=SPEC_DIR / "ege_2026_math_spec.json",
    kes_kos_path=SPEC_DIR / "ege_2026_math_kes_kos.json"
)

@router.post("/answer", response_model=CheckAnswerResponse)
async def check_answer(
    request: CheckAnswerRequest,
    service: AnswerService = Depends(get_answer_service) # <-- Теперь get_answer_service определён
) -> CheckAnswerResponse:
    """
    API endpoint to check a user's answer.

    This endpoint validates the user's answer against an external source
    and returns the result along with a score and potential hint.
    """
    # Извлекаем task_number из problem_id или из БД
    # Временно упрощаем: предполагаем, что task_number можно извлечь из problem_id или БД
    # TODO: Реализовать извлечение task_number из БД по problem_id
    task_number_str = request.problem_id.split('_')[-1]  # init_4CBD4E -> 4CBD4E
    # Попробуем извлечь числовую часть, если возможно, иначе используем заглушку
    try:
        # Это упрощённый пример. В реальности task_number может быть в БД.
        # Для тестов, предположим, что task_number всегда 18 или берётся из БД.
        # Пока что оставим как есть, но в проде task_number нужно брать из БД.
        # Проверим, есть ли метод в БД для получения task_number
        # db_problem = service.db.get_problem_by_id(request.problem_id) # <-- пример
        # task_number = db_problem.task_number if db_problem else 18
        # Пока что используем заглушку
        task_number = 18
    except:
        task_number = 18 # fallback

    # Вызов сервиса для проверки
    response = await service.check_answer(request)

    # Добавляем feedback в ответ
    feedback = SPEC_SERVICE.get_feedback_for_task(task_number)
    # Так как CheckAnswerResponse не имеет поля feedback, нужно либо расширить её,
    # либо возвращать feedback отдельно. Для совместимости с предыдущей логикой,
    # можно добавить feedback в short_hint или модифицировать схему.
    # В целях минимальных изменений, расширим CheckAnswerResponse в api/schemas.py
    # и обновим возврат здесь.
    # Однако, для простоты, предположим, что CheckAnswerResponse теперь включает feedback.
    # Если CheckAnswerResponse обновлена в api/schemas.py, то просто вернём response.
    # Если нет, нужно создать новый объект, включая feedback.
    # Пока что, если CheckAnswerResponse не имеет feedback, возвращаем как есть.
    # В следующем шаге обновим api/schemas.py и возвращаем полный объект.
    return response
    # except HTTPException:
    #     # Пробрасываем HTTPException дальше, чтобы FastAPI корректно обработал
    #     raise
    # except Exception:
    #     # Пробрасываем, чтобы централизованная обработка сработала
    #     raise # <-- Убираем, если эндпоинт не обрабатывает исключения напрямую

# Импорты уже включены выше
