# test_check.py
import asyncio
from utils.answer_checker import FIPIAnswerChecker

async def test():
    checker = FIPIAnswerChecker()
    # Используйте реальный task_id из вашей БД, например '71BC43'
    result = await checker.check_answer(
        task_id="71BC43",
        form_id="q71BC43",  # или как в вашем HTML: data-form-id
        user_answer="5"     # заведомо верный или неверный ответ
    )
    print("Result:", result)

asyncio.run(test())