from typing import List, Dict, Any, Optional
from pathlib import Path
from bs4.element import Tag
from domain.interfaces.html_processor import IHTMLProcessor
from domain.models.problem_builder import ProblemBuilder
from domain.models.problem_schema import Problem


class HTMLProcessingService:
    """Application service for HTML processing operations."""
    
    def __init__(self, html_processor: IHTMLProcessor):
        self.html_processor = html_processor

    async def process_html_block_to_problem(
        self,
        header_container: Tag,
        qblock: Tag,
        block_index: int,
        subject: str,
        base_url: str,
        run_folder_page: Path,
        **kwargs
    ) -> Problem:
        """
        Process HTML block and convert to Problem instance.
        
        Args:
            header_container: The BeautifulSoup Tag containing the header panel.
            qblock: The BeautifulSoup Tag containing the question block.
            block_index: The index of this block in the overall page processing.
            subject: The subject name (e.g., "math", "informatics").
            base_url: The base URL of the scraped page.
            run_folder_page: Path to the run folder for this page's assets.
            
        Returns:
            A Problem instance built from the processed block.
        """
        # Process HTML block using domain interface
        processed_data = await self.html_processor.process_html_block(
            header_container, qblock, block_index, subject, base_url, **kwargs
        )
        
        # Build Problem instance from processed data
        problem_builder = ProblemBuilder()
        problem = problem_builder.build_problem(
            problem_id=processed_data.get('problem_id'),
            subject=subject,
            type=processed_data.get('type'),
            text=processed_data.get('text'),
            answer=processed_data.get('answer'),
            options=processed_data.get('options'),
            assignment_text=processed_data.get('assignment_text'),
            kes_codes=processed_data.get('kes_codes', []),
            kos_codes=processed_data.get('kos_codes', []),
            task_number=processed_data.get('task_number', 0),
            exam_part=processed_data.get('exam_part'),
            difficulty=processed_data.get('difficulty'),
            max_score=processed_data.get('max_score'),
            topics=processed_data.get('topics', []),
            requirements=processed_data.get('requirements', []),
        )
        
        return problem
