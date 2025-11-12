import pytest
from bs4 import BeautifulSoup
from infrastructure.adapters.fipi_html_metadata_extractor import MetadataExtractor

@pytest.fixture
def mock_header():
    html = """
    <div class="header-container">
        <span class="canselect">TASK-123</span>
        <div>Задание 5</div>
        <div>КЭС: 2.1</div>
        <div>КОС: 3.2</div>
    </div>
    """
    return BeautifulSoup(html, 'html.parser').find('div', class_='header-container')

def test_metadata_extractor_basic(mock_header):
    extractor = MetadataExtractor()
    metadata = extractor.extract(mock_header)
    assert metadata['task_id'] == 'TASK-123'
    assert metadata['task_number'] == 5
    assert '2.1' in metadata['kes_codes']
    assert '3.2' in metadata['kos_codes']
