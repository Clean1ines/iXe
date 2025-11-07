import pytest
from unittest.mock import Mock, AsyncMock
from pathlib import Path

from domain.services.task_classifier import TaskClassificationService, TaskClassificationResult
from domain.services.answer_type_detector import AnswerTypeService
from domain.services.metadata_enhancer import MetadataExtractionService
from utils.task_number_inferer import TaskNumberInferer
from services.specification import SpecificationService
from processors.html import (
    ImageScriptProcessor,
    FileLinkProcessor,
    TaskInfoProcessor,
    InputFieldRemover,
    MathMLRemover,
    UnwantedElementRemover
)
from processors.html_processor_interface import IHTMLProcessor


class TestDomainServiceIntegration:
    """Integration tests for domain services working together."""

    @pytest.fixture
    def mock_spec_service(self):
        """Create a mock SpecificationService."""
        return Mock(spec=SpecificationService)

    @pytest.fixture
    def mock_task_inferer(self):
        """Create a mock TaskNumberInferer."""
        return Mock(spec=TaskNumberInferer)

    def test_full_classification_workflow(self, mock_task_inferer):
        """Test the full workflow of task classification using domain services."""
        # Create services
        task_classifier = TaskClassificationService(task_inferer=mock_task_inferer)
        answer_type_service = AnswerTypeService()
        
        # Setup mock
        mock_task_inferer.infer.return_value = 15
        
        # Test data
        kes_codes = ["1.1", "2.3"]
        kos_codes = ["4.5"]
        html_content = '<input type="text" name="answer" maxlength="100">'
        
        # Execute
        answer_type = answer_type_service.detect_answer_type(html_content)
        classification_result = task_classifier.classify_task(kes_codes, kos_codes, answer_type)
        
        # Verify
        assert classification_result.task_number == 15
        assert classification_result.difficulty_level == "advanced"
        assert classification_result.max_score == 2
        mock_task_inferer.infer.assert_called_once_with(kes_codes, "extended")

    def test_metadata_enhancement_workflow(self, mock_spec_service):
        """Test metadata enhancement with specification service."""
        metadata_enhancer = MetadataExtractionService(specification_service=mock_spec_service)
        
        # Setup mocks
        mock_spec_service.explain_kes.return_value = "Test KES explanation"
        mock_spec_service.explain_kos.return_value = "Test KOS explanation"
        
        # Test data
        extracted_meta = {
            'kes_codes': ['1.1'],
            'kos_codes': ['2.1'],
            'other_field': 'value'
        }
        
        # Execute
        enhanced_meta = metadata_enhancer.enhance_metadata(extracted_meta)
        
        # Verify
        assert enhanced_meta['kes_explanations'] == ['Test KES explanation']
        assert enhanced_meta['kos_explanations'] == ['Test KOS explanation']
        assert enhanced_meta['other_field'] == 'value'
        mock_spec_service.explain_kes.assert_called_once_with('1.1')
        mock_spec_service.explain_kos.assert_called_once_with('2.1')

    def test_html_processors_implement_interface(self):
        """Test that all HTML processors implement IHTMLProcessor interface."""
        processors = [
            ImageScriptProcessor(),
            FileLinkProcessor(),
            TaskInfoProcessor(),
            InputFieldRemover(),
            MathMLRemover(),
            UnwantedElementRemover()
        ]
        
        for processor in processors:
            assert isinstance(processor, IHTMLProcessor), f"{type(processor).__name__} does not implement IHTMLProcessor"


class TestHTMLProcessingPipeline:
    """Integration tests for HTML processing pipeline."""

    @pytest.mark.asyncio
    async def test_process_html_content_through_pipeline(self):
        """Test processing HTML content through multiple processors."""
        # Create processors
        processors = [
            MathMLRemover(),
            InputFieldRemover(),
            TaskInfoProcessor()
        ]
        
        # Sample HTML content
        html_content = """
        <html>
            <body>
                <math><mi>x</mi></math>
                <input type="text" name="answer">
                <div class="info-button">Info</div>
                <p>Test content</p>
            </body>
        </html>
        """
        
        context = {'run_folder_page': Path('/tmp')}
        
        # Process through each processor
        current_content = html_content
        for processor in processors:
            current_content, metadata = await processor.process(current_content, context)
        
        # Verify transformations
        # MathML should be removed
        assert '<math>' not in current_content
        # Input with name 'answer' should be removed
        assert 'name="answer"' not in current_content
        # Info button onclick should be updated
        assert 'toggleInfo(this)' in current_content
