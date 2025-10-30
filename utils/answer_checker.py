"""Модуль для проверки ответов через headless-браузер (Playwright) на сайте ФИПИ."""

import logging
from typing import Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

class FIPIAnswerChecker:
    def __init__(self, base_url: str = "https://ege.fipi.ru") -> None:
        self.base_url = base_url.rstrip("/")

    async def check_answer(self, task_id: str, form_id: str, user_answer: str) -> Dict[str, Any]:
        logger.info(f"Checking answer for task {task_id} via Playwright on FIPI")
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # Увеличиваем таймауты
                page.set_default_timeout(30000)  # 30 секунд

                proj_id = "AC437B34557F88EA4115D2F374B0A07B"
                main_url = f"{self.base_url}/bank/index.php?proj={proj_id}"
                
                # Ждём полной загрузки сети
                await page.goto(main_url, wait_until="networkidle", timeout=30000)
                
                # Явное ожидание появления хотя бы одного блока
                await page.wait_for_selector(".processed_qblock", timeout=30000)
                # 3. Находим нужный блок по data-task-id
                block_selector = f'div.processed_qblock[data-task-id="{task_id}"]'
                block = await page.query_selector(block_selector)
                if not block:
                    await browser.close()
                    return {"status": "error", "message": f"Task block {task_id} not found", "raw_response": ""}

                # 4. Вводим ответ в поле внутри этого блока
                input_selector = f'{block_selector} input[name="answer"]'
                await page.fill(input_selector, user_answer)
                logger.debug(f"Filled answer for task {task_id}")

                # 5. Нажимаем кнопку "Ответить" в том же блоке
                button_selector = f'{block_selector} .answer-button:has-text("Ответить")'
                await page.click(button_selector)
                logger.debug(f"Clicked 'Ответить' for task {task_id}")

                # 6. Ждём обновления статуса
                status_selector = f'{block_selector} .task-status'
                await page.wait_for_function(
                    f'document.querySelector("{status_selector}").classList.contains("task-status-2") || '
                    f'document.querySelector("{status_selector}").classList.contains("task-status-3")',
                    timeout=8000
                )

                # 7. Читаем результат
                status_el = await page.query_selector(status_selector)
                status_class = await status_el.get_attribute("class") or ""
                status_text = await status_el.inner_text() or ""

                await browser.close()

                if "task-status-3" in status_class:
                    return {"status": "correct", "message": "ВЕРНО", "raw_response": status_text}
                elif "task-status-2" in status_class:
                    return {"status": "incorrect", "message": "НЕВЕРНО", "raw_response": status_text}
                else:
                    return {"status": "error", "message": "Неизвестный статус", "raw_response": status_text}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout for task {task_id}: {e}")
            return {"status": "error", "message": "Таймаут при проверке", "raw_response": str(e)}
        except Exception as e:
            logger.error(f"Playwright error for task {task_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка: {type(e).__name__}", "raw_response": str(e)}
