"""Module for checking answers via headless browser (Playwright) on the FIPI website."""

import logging
from typing import Dict, Any
from playwright.async_api import TimeoutError as PlaywrightTimeout
from utils.browser_manager import BrowserManager

logger = logging.getLogger(__name__)

class FIPIAnswerChecker:
    def __init__(self, browser_manager: BrowserManager, base_url: str = "https://ege.fipi.ru") -> None:
        self.browser_manager = browser_manager
        self.base_url = base_url.rstrip("/")

    async def check_answer(self, task_id: str, form_id: str, user_answer: str, subject: str) -> Dict[str, Any]:
        """
        Checks the user's answer via Playwright on the FIPI website.

        Args:
            task_id: The task ID
            form_id: The form ID (not used in the current implementation)
            user_answer: The user's answer
            subject: The subject of the task (used to get the correct page from BrowserManager)

        Returns:
            A dictionary with the check results
        """
        logger.info(f"Checking answer for task {task_id} (subject: {subject}) via Playwright on FIPI")
        try:
            page = await self.browser_manager.get_page(subject)
            # Increase timeouts
            page.set_default_timeout(30000)  # 30 seconds

            # Explicit wait for at least one block to appear
            await page.wait_for_selector(".processed_qblock", timeout=30000)
            # 3. Find the required block by data-task-id
            block_selector = f'div.processed_qblock[data-task-id="{task_id}"]'
            block = await page.query_selector(block_selector)
            if not block:
                return {"status": "error", "message": f"Task block {task_id} not found", "raw_response": ""}

            # 4. Fill the answer field inside this block
            input_selector = f'{block_selector} input[name="answer"]'
            await page.fill(input_selector, user_answer)
            logger.debug(f"Filled answer for task {task_id}")

            # 5. Click the "Answer" button in the same block
            button_selector = f'{block_selector} .answer-button:has-text("Ответить")'
            await page.click(button_selector)
            logger.debug(f"Clicked 'Ответить' for task {task_id}")

            # 6. Wait for the status to update
            status_selector = f'{block_selector} .task-status'
            await page.wait_for_function(
                f'document.querySelector("{status_selector}").classList.contains("task-status-2") || '
                f'document.querySelector("{status_selector}").classList.contains("task-status-3")',
                timeout=8000
            )

            # 7. Read the result
            status_el = await page.query_selector(status_selector)
            status_class = await status_el.get_attribute("class") or ""
            status_text = await status_el.inner_text() or ""

            if "task-status-3" in status_class:
                return {"status": "correct", "message": "CORRECT", "raw_response": status_text}
            elif "task-status-2" in status_class:
                return {"status": "incorrect", "message": "INCORRECT", "raw_response": status_text}
            else:
                return {"status": "error", "message": "Unknown status", "raw_response": status_text}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout for task {task_id}: {e}")
            return {"status": "error", "message": "Timeout during check", "raw_response": str(e)}
        except Exception as e:
            logger.error(f"Playwright error for task {task_id}: {e}", exc_info=True)
            return {"status": "error", "message": f"Error: {type(e).__name__}", "raw_response": str(e)}

    @staticmethod
    def get_proj_id_by_subject(subject: str) -> str:
        """
        Returns the proj_id by subject name.

        Args:
            subject: The subject name

        Returns:
            proj_id for accessing tasks on the FIPI website
        """
        # TODO: Fill in the actual proj_ids for all subjects
        proj_ids = {
            "math": "AC437B34557F88EA4115D2F374B0A07B",
            "informatics": "INFORMATICS_PROJ_ID",  # Replace with the actual ID
            "russian": "RUSSIAN_PROJ_ID"  # Replace with the actual ID
        }
        return proj_ids.get(subject.lower(), "AC437B34557F88EA4115D2F374B0A07B")  # default to math

