"""
Module for checking answers against the official FIPI answer service.
This module provides the FIPIAnswerChecker class which handles the interaction
with FIPI's answer checking service using Playwright for browser automation.
"""
import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from utils.browser_pool_manager import BrowserPoolManager

logger = logging.getLogger(__name__)

class FIPIAnswerChecker:
    """
    A class to check answers against the official FIPI service.
    
    This class handles the browser automation required to submit answers
    to the FIPI checking service and parse the results. It manages page
    navigation, form filling, and result extraction.
    """
    
    def __init__(self, browser_pool: BrowserPoolManager):
        """
        Initializes the answer checker with a browser manager.
        
        Args:
            browser_manager (BrowserManager): Instance to manage browser context and pages.
        """
        self.browser_pool = browser_manager
        logger.debug("FIPIAnswerChecker initialized with BrowserManager")
    
    async def check_answer(
        self,
        task_id: str,
        user_answer: str,
        subject: str = "math"
    ) -> Tuple[str, float]:
        """
        Checks a user's answer against the official FIPI service.
        
        Args:
            task_id (str): The task identifier (e.g., "40B442")
            user_answer (str): The user's answer to check
            subject (str): Subject name for context (default: "math")
        
        Returns:
            Tuple[str, float]: (verdict, score) where verdict is "correct", "incorrect", or "error",
            and score is a float between 0.0 and 1.0 (or -1.0 for errors)
        """
        logger.info(f"Checking answer for task {task_id} with user answer '{user_answer}'")
        
        try:
            # Navigate to the answer checking page
            check_url = f"https://fipi.ru/answer-checking?task={task_id}&subject={subject}"
            page = await self.browser_manager.get_page(check_url)
            
            try:
                # Wait for the answer input field to be available
                await page.wait_for_selector("#user_answer", timeout=60000)
                
                # Fill in the user's answer
                await page.fill("#user_answer", user_answer)
                
                # Submit the form
                await page.click("#submit_answer")
                
                # Wait for the result to appear
                await page.wait_for_selector(".answer-result", timeout=60000)
                
                # Extract the result
                verdict_element = await page.query_selector(".verdict")
                score_element = await page.query_selector(".score")
                
                verdict = "error"
                score = -1.0
                
                if verdict_element:
                    verdict_text = await verdict_element.text_content()
                    if "верно" in verdict_text.lower():
                        verdict = "correct"
                    elif "неверно" in verdict_text.lower():
                        verdict = "incorrect"
                
                if score_element:
                    score_text = await score_element.text_content()
                    try:
                        # Extract numeric score from text like "Score: 1.0"
                        score_match = re.search(r'[\d.]+', score_text)
                        if score_match:
                            score = float(score_match.group())
                    except (ValueError, TypeError):
                        logger.warning(f"Could not parse score from '{score_text}'")
                
                logger.info(f"Answer check result for task {task_id}: verdict={verdict}, score={score}")
                return verdict, score
                
            except PlaywrightTimeoutError as e:
                logger.error(f"Timeout for task {task_id}: {e}")
                return "error", -1.0
            except Exception as e:
                logger.error(f"Error checking answer for task {task_id}: {e}", exc_info=True)
                return "error", -1.0
            finally:
                # Return the page to the pool
                await self.browser_manager.return_page(page)
                
        except Exception as e:
            logger.error(f"Browser error while checking answer for task {task_id}: {e}", exc_info=True)
            return "error", -1.0
