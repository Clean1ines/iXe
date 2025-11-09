import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)

def get_real_header_type():
    # Пример HTML из реального скрапинга
    html = '''
    <div id="i40B442" class="None">
        iСВОЙСТВА ЗАДАНИЯКЭС:7.5 Коорд...
    </div>
    '''
    soup = BeautifulSoup(html, 'html.parser')
    header = soup.find('div')
    
    print(f"Тип объекта: {type(header)}")
    print(f"Доступные атрибуты: {dir(header)}")
    print(f"Атрибуты элемента: {header.attrs}")
    print(f"Текст через get_text(): '{header.get_text(strip=True)}'")
    print(f"Текст через string: '{header.string}'")
    print(f"Наличие свойства text: {hasattr(header, 'text')}")
    print(f"Значение свойства text: {getattr(header, 'text', 'not available')}")

if __name__ == "__main__":
    get_real_header_type()
