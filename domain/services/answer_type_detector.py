"""Domain service for detecting answer types from HTML content."""

from typing import Dict, Any
import re
from bs4 import BeautifulSoup


class AnswerTypeService:
    """Service for detecting answer types from HTML content."""

    def detect_answer_type(self, html_content: str) -> str:
        """
        Detect the type of answer expected based on HTML content.

        Args:
            html_content: HTML content of the task

        Returns:
            Answer type as string (short, extended, multiple_choice, etc.)
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for specific patterns that indicate answer type
        # Check for input fields with name 'answer'
        answer_inputs = soup.find_all('input', attrs={'name': 'answer'})
        
        if not answer_inputs:
            return 'unknown'
        
        # Determine type based on input characteristics
        for inp in answer_inputs:
            input_type = inp.get('type', 'text').lower()
            if input_type == 'text':
                # Check if it's a longer answer
                maxlength = inp.get('maxlength', '')
                if maxlength and int(maxlength) > 20:
                    return 'extended'
                else:
                    return 'short'
            elif input_type in ['radio', 'checkbox']:
                return 'multiple_choice'
        
        # Default to short if we can't determine
        return 'short'
