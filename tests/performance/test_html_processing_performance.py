import time
import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock

from domain.services.task_classifier import TaskClassificationService
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from utils.task_number_inferer import TaskNumberInferer
from processors.html import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)


class TestHTMLProcessingPerformance:
    """Performance tests for HTML processing components."""

    @pytest.mark.asyncio
    async def test_html_processing_pipeline_performance(self):
        """Test that HTML processing pipeline performs within acceptable time limits."""
        # Create processors
        processors = [
            MathMLRemover(),
            InputFieldRemover(),
            TaskInfoProcessor(),
            FileLinkProcessor(),
            ImageScriptProcessor(),
        ]
        
        # Sample HTML content (larger than typical)
        html_content = """
        <html>
            <body>
                <math><mi>x</mi><mo>=</mo><mfrac><mrow><mo>-</mo><mi>b</mi><mo>±</mo><msqrt><msup><mi>b</mi><mn>2</mn></msup><mo>-</mo><mn>4</mn><mi>a</mi><mi>c</mi></msqrt></mrow><mrow><mn>2</mn><mi>a</mi></mrow></mfrac></math>
                <input type="text" name="answer" maxlength="100">
                <div class="info-button">Info</div>
                <p>Find the value of x in the quadratic equation.</p>
                <p>Additional content to make the HTML larger...</p>
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                <p>Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
                <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.</p>
                <p>Nisi ut aliquip ex ea commodo consequat.</p>
                <p>Duis aute irure dolor in reprehenderit in voluptate velit esse.</p>
                <p>Cillum dolore eu fugiat nulla pariatur.</p>
                <p>Excepteur sint occaecat cupidatat non proident.</p>
                <p>Sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
                <p>More content to test performance with larger HTML...</p>
                <p>More content to test performance with larger HTML...</p>
                <p>More content to test performance with larger HTML...</p>
                <p>More content to test performance with larger HTML...</p>
                <p>More content to test performance with larger HTML...</p>
            </body>
        </html>
        """ * 10  # Repeat to make it larger
        
        context = {
            'run_folder_page': Path('/tmp'),
            'downloader': Mock(),
            'base_url': 'https://example.com'
        }
        
        # Measure processing time
        start_time = time.time()
        
        current_content = html_content
        for processor in processors:
            current_content, metadata = await processor.process(current_content, context)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"HTML processing time for all processors: {processing_time:.4f} seconds")
        
        # Assert that processing time is acceptable (less than 1 second for this content)
        assert processing_time < 1.0, f"HTML processing took too long: {processing_time:.4f}s"
        
        # Verify that transformations were applied
        assert '<math>' not in current_content  # MathML should be removed
        assert 'name="answer"' not in current_content  # Input with name 'answer' should be removed
        assert 'toggleInfo(this)' in current_content  # Info button onclick should be updated

    def test_domain_service_performance(self):
        """Test that domain services perform within acceptable time limits."""
        # Mock inferer
        mock_inferer = Mock(spec=TaskNumberInferer)
        mock_inferer.infer.return_value = 5
        
        # Create services
        task_classifier = TaskClassificationService(mock_inferer)
        answer_type_service = AnswerTypeService()
        
        # Measure classification time
        start_time = time.time()
        
        for i in range(100):  # Test multiple calls
            result = task_classifier.classify_task(
                kes_codes=[f"1.{i%10}", f"2.{i%5}"],
                kos_codes=[f"3.{i%7}"],
                answer_type="short"
            )
        
        classification_time = time.time() - start_time
        avg_classification_time = classification_time / 100
        
        print(f"Average task classification time: {avg_classification_time:.6f} seconds")
        
        # Assert that average classification time is acceptable (less than 10ms per call)
        assert avg_classification_time < 0.01, f"Average classification took too long: {avg_classification_time:.6f}s"
        
        # Measure answer type detection time
        html_content = '<input type="text" name="answer" maxlength="100">'
        
        start_time = time.time()
        
        for i in range(100):  # Test multiple calls
            answer_type = answer_type_service.detect_answer_type(html_content)
        
        detection_time = time.time() - start_time
        avg_detection_time = detection_time / 100
        
        print(f"Average answer type detection time: {avg_detection_time:.6f} seconds")
        
        # Assert that average detection time is acceptable (less than 10ms per call)
        assert avg_detection_time < 0.01, f"Average answer type detection took too long: {avg_detection_time:.6f}s"
