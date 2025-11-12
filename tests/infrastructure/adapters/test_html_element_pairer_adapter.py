import pytest
from bs4 import BeautifulSoup
from infrastructure.adapters.html_element_pairer_adapter import ElementPairer

@pytest.fixture
def mock_html():
    return """
    <html>
    <body>
        <div id="i40B442" class="header-container">Header 1</div>
        <div id="q40B442" class="qblock">Question 1</div>
        <div id="i40B443" class="header-container">Header 2</div>
        <div id="q40B443" class="qblock">Question 2</div>
    </body>
    </html>
    """

def test_element_pairer_basic(mock_html):
    soup = BeautifulSoup(mock_html, 'html.parser')
    pairer = ElementPairer()
    pairs = pairer.pair(soup)
    assert len(pairs) == 2
    assert pairs[0][0].get('id') == 'i40B442'
    assert pairs[0][1].get('id') == 'q40B442'
