import pytest
from bs4 import BeautifulSoup
from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter

@pytest.fixture
def adapter():
    return HTMLMetadataExtractorAdapter()

def test_extract_task_number(adapter):
    html = "<div><span class='canselect'>TASK123</span> СВОЙСТВА ЗАДАНИЯ Задание 7 КЭС:2.1</div>"
    header = BeautifulSoup(html, 'html.parser').div
    result = adapter.extract(header)
    assert result["task_number"] == 7

def test_extract_kes_codes(adapter):
    html = "<div>КЭС: 1.2.3, Кодификатор: 4.5 Требование: 3</div>"
    header = BeautifulSoup(html, 'html.parser').div
    result = adapter.extract(header)
    assert sorted(result["kes_codes"]) == ["1.2.3", "4.5"]
    assert sorted(result["kos_codes"]) == ["3"]

def test_double_encoded_text(adapter):
    # Simulate double-encoded text by encoding and decoding
    original_text = "КЭС: 4.1 Производная функции"
    # Emulate double encoding: UTF-8 bytes interpreted as Windows-1251
    double_encoded = original_text.encode('utf-8').decode('windows-1251')
    
    header = BeautifulSoup(f"<div>{double_encoded}</div>", 'html.parser').div
    result = adapter.extract(header)
    assert "4.1" in result["kes_codes"]

def test_complex_double_encoded_text(adapter):
    # Simulate complex double-encoded text
    original_text = "КЭС: 4.1 Производная функции. Кодификатор: 4.2 Применение производной к исследованию функций"
    double_encoded = original_text.encode('utf-8').decode('windows-1251')
    
    header = BeautifulSoup(f"<div>{double_encoded}</div>", 'html.parser').div
    result = adapter.extract(header)
    assert any(code.startswith("4.1") for code in result["kes_codes"])
    assert any(code.startswith("4.2") for code in result["kes_codes"])
