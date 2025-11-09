import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

def debug_real_headers():
    """Анализирует реальные header-объекты как они используются в скрапере"""
    # Создаем объект, имитирующий реальный header из скрапинга
    class RealHeader:
        def __init__(self):
            self.id = 'i40B442'
            self.extracted_id = '40B442'
            self.text = 'iСВОЙСТВА ЗАДАНИЯКЭС:7.5 Коорд...'
            self.attrs = {'id': 'i40B442', 'class': 'None'}
            self.name = 'div'
        
        def get_text(self, strip=False):
            return self.text.strip() if strip else self.text
        
        def get(self, attr_name, default=None):
            return self.attrs.get(attr_name, default)

    # Тестируем реальный header-объект
    print("=== АНАЛИЗ РЕАЛЬНОГО HEADER-ОБЪЕКТА ИЗ СКРАПЕРА ===")
    real_header = RealHeader()
    
    print(f"Тип объекта: {type(real_header)}")
    print(f"extracted_id: {real_header.extracted_id}")
    print(f"text: {real_header.text}")
    print(f"get_text(strip=True): '{real_header.get_text(strip=True)}'")
    print(f"attrs: {real_header.attrs}")
    print(f"id: {real_header.get('id')}")
    
    # Проверяем, как это будет работать в адаптере
    print("\n=== ТЕСТИРОВАНИЕ АДАПТЕРА С РЕАЛЬНЫМ ОБЪЕКТОМ ===")
    from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter
    
    adapter = HTMLMetadataExtractorAdapter()
    result = adapter.extract_metadata_from_header(real_header)
    print(f"Результат извлечения: {result}")

if __name__ == "__main__":
    debug_real_headers()
