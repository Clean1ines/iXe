import pytest
from domain.services.answer_type_detector import AnswerTypeService


class TestAnswerTypeService:
    """Unit tests for AnswerTypeService."""

    @pytest.fixture
    def answer_type_service(self):
        """Create an AnswerTypeService instance."""
        return AnswerTypeService()

    def test_detect_answer_type_short_text(self, answer_type_service):
        """Test detection of short text answers."""
        html_content = '<input type="text" name="answer" maxlength="10">'
        
        result = answer_type_service.detect_answer_type(html_content)
        
        assert result == "short"

    def test_detect_answer_type_extended_text(self, answer_type_service):
        """Test detection of extended text answers."""
        html_content = '<input type="text" name="answer" maxlength="100">'
        
        result = answer_type_service.detect_answer_type(html_content)
        
        assert result == "extended"

    def test_detect_answer_type_multiple_choice(self, answer_type_service):
        """Test detection of multiple choice answers."""
        html_content = '''
        <input type="radio" name="answer" value="a"> A
        <input type="radio" name="answer" value="b"> B
        <input type="radio" name="answer" value="c"> C
        '''
        
        result = answer_type_service.detect_answer_type(html_content)
        
        assert result == "multiple_choice"

    def test_detect_answer_type_unknown(self, answer_type_service):
        """Test detection when no answer input is found."""
        html_content = '<div>No answer input here</div>'
        
        result = answer_type_service.detect_answer_type(html_content)
        
        assert result == "unknown"

    def test_detect_answer_type_default_short(self, answer_type_service):
        """Test default detection for text input without maxlength."""
        html_content = '<input type="text" name="answer">'
        
        result = answer_type_service.detect_answer_type(html_content)
        
        assert result == "short"
