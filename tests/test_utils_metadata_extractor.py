"""
Unit tests for the MetadataExtractor class.
"""
import unittest
from bs4 import BeautifulSoup
from bs4.element import Tag
from utils.metadata_extractor import MetadataExtractor


class TestMetadataExtractor(unittest.TestCase):
    """
    Test cases for the MetadataExtractor class.
    """

    def setUp(self):
        """
        Set up the MetadataExtractor instance for tests.
        """
        self.extractor = MetadataExtractor()

    def test_extract_task_id_found(self):
        """
        Test extracting task_id when canselect span is present with text.
        """
        html = '<div><span class="canselect">TASK123</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "TASK123", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_task_id_not_found(self):
        """
        Test extracting task_id when canselect span is not present.
        """
        html = '<div><span class="other-class">TASK123</span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_task_id_empty_text(self):
        """
        Test extracting task_id when canselect span is present but has no text.
        """
        html = '<div><span class="canselect"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_form_id_found(self):
        """
        Test extracting form_id when answer-button span is present with correct onclick.
        """
        html = '<div><span class="answer-button" onclick="checkButtonClick(\'form123\')"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": "form123"}
        self.assertEqual(result, expected)

    def test_extract_form_id_not_found_no_onclick(self):
        """
        Test extracting form_id when answer-button span is present but has no onclick.
        """
        html = '<div><span class="answer-button"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_form_id_not_found_no_answer_button(self):
        """
        Test extracting form_id when answer-button span is not present.
        """
        html = '<div><span class="other-class" onclick="checkButtonClick(\'form123\')"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_form_id_not_found_invalid_onclick(self):
        """
        Test extracting form_id when answer-button span has an invalid onclick format.
        """
        html = '<div><span class="answer-button" onclick="someOtherFunction(\'form123\')"></span></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)

    def test_extract_both_task_id_and_form_id(self):
        """
        Test extracting both task_id and form_id when both are present.
        """
        html = '''
        <div>
            <span class="canselect">TASK123</span>
            <span class="answer-button" onclick="checkButtonClick('form123')"></span>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "TASK123", "form_id": "form123"}
        self.assertEqual(result, expected)

    def test_extract_empty_when_no_relevant_elements(self):
        """
        Test extracting metadata when header container has no relevant elements.
        """
        html = '<div><p>Some other content</p></div>'
        soup = BeautifulSoup(html, 'html.parser')
        header_container = soup.find('div')
        result = self.extractor.extract(header_container)
        expected = {"task_id": "", "form_id": ""}
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
