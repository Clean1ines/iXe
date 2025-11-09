import logging
from bs4 import BeautifulSoup
from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_header_structure():
    """Анализирует структуру header-элементов в реальных данных"""
    # Пример из логов пользователя
    header_html = '<div id="i40B442" class="None">iСВОЙСТВА ЗАДАНИЯКЭС:7.5 Коорд...</div>'
    soup = BeautifulSoup(header_html, 'html.parser')
    header = soup.find('div')
    
    logger.info("=== АНАЛИЗ СТРУКТУРЫ HEADER-ЭЛЕМЕНТА ===")
    logger.info(f"Тип объекта: {type(header)}")
    
    # Проверяем доступные атрибуты
    logger.info("\nДОСТУПНЫЕ АТРИБУТЫ И МЕТОДЫ:")
    attrs = [attr for attr in dir(header) if not attr.startswith('_')]
    logger.info(f"Всего атрибутов/методов: {len(attrs)}")
    logger.info("Ключевые атрибуты: " + ', '.join([attr for attr in attrs if attr in ['text', 'string', 'attrs', 'get_text', 'find', 'find_all']]))
    
    # Проверяем содержимое
    logger.info("\nСОДЕРЖИМОЕ ЭЛЕМЕНТА:")
    logger.info(f"attrs: {header.attrs}")
    logger.info(f"string: {header.string}")
    logger.info(f"text (свойство): {getattr(header, 'text', 'not available')}")
    logger.info(f"get_text(): {header.get_text(strip=True)}")
    
    # Проверяем, есть ли кастомные атрибуты
    logger.info("\nКАСТОМНЫЕ АТРИБУТЫ:")
    for attr in ['extracted_id', 'text', 'content']:
        if hasattr(header, attr):
            logger.info(f"  {attr}: {getattr(header, attr)}")
        elif attr in header.attrs:
            logger.info(f"  {attr} (в attrs): {header.attrs[attr]}")
    
    # Пробуем извлечь метаданные
    logger.info("\nПОПЫТКА ИЗВЛЕЧЬ МЕТАДАННЫЕ:")
    adapter = HTMLMetadataExtractorAdapter()
    try:
        result = adapter.extract_metadata_from_header(header)
        logger.info(f"Результат: {result}")
    except Exception as e:
        logger.error(f"Ошибка при извлечении: {e}")

if __name__ == "__main__":
    analyze_header_structure()
