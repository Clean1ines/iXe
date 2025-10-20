import os
import re
import sys
import time
from urllib.parse import urljoin
from pathlib import Path
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup # Добавляем BeautifulSoup для очистки HTML

PROJ = "AC437B34557F88EA4115D2F374B0A07B"
BASE = "https://ege.fipi.ru/bank/questions.php" # Базовый URL страницы
OUTHTML = "fipi_page1_wysiwyg_full.html"

def download_and_save_image_playwright(page, img_src, save_dir, guid, base_url, files_location_prefix):
    """Скачивает и сохраняет изображение, используя тот же контекст Playwright."""
    full_img_path = files_location_prefix + img_src
    img_url = urljoin(base_url, full_img_path)
    try:
        print(f"    Попытка скачать через Playwright: {img_url}")
        response = page.request.get(img_url)
        if response.ok:
            content = response.body()
            save_path = save_dir / guid / img_src.split('/')[-1]
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(content)
            print(f"  - Изображение сохранено: {save_path}")
            return f"assets/{PROJ}/{save_path.name}"
        else:
            print(f"  - Ошибка HTTP при скачивании через Playwright {img_url}: {response.status}")
            return img_src # Возвращаем оригинальный src, если не удалось скачать
    except Exception as e:
        print(f"  - Ошибка при скачивании через Playwright {img_url}: {e}")
        return img_src

def process_page_with_playwright(url, output_html_file):
    """Загружает страницу с помощью Playwright, дожидается рендеринга и извлекает qblocks."""
    print(f"Загрузка страницы с помощью Playwright: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ignore_https_errors=True
        )
        page = context.new_page()

        page.goto(url, wait_until="networkidle")
        print("  Страница загружена, ожидание выполнения JS...")

        try:
            has_mathjax = page.evaluate("window.MathJax !== undefined")
            if has_mathjax:
                print("  Обнаружен MathJax, ожидание завершения рендеринга формул...")
                page.evaluate("MathJax.Hub.promise")
                print("  MathJax завершил рендеринг.")
            else:
                print("  MathJax не обнаружен на странице.")
        except Exception as e:
            print(f"  Ошибка при ожидании MathJax: {e}. Продолжаем выполнение.")

        print("  Добавлена задержка 3 секунды...")
        time.sleep(3)

        print("  Извлечение qblocks...")
        qblocks = page.query_selector_all("div.qblock")

        processed_blocks_html = []

        try:
            files_location_prefix = page.evaluate("window.files_location || '../../'")
            print(f"  files_location_prefix определён как: '{files_location_prefix}'")
        except Exception as e:
            print(f"  Не удалось получить files_location из страницы, используем по умолчанию '../../': {e}")
            files_location_prefix = '../../'

        for i, block in enumerate(qblocks):
            block_id = block.get_attribute("id")
            print(f"    Обработка блока {i} (ID: {block_id})...")

            block_html = block.inner_html()
            print(f"      Исходный HTML блока {block_id} длина: {len(block_html)}")

            soup = BeautifulSoup(block_html, 'html.parser')

            # Найти и обработать вызовы функций вроде ShowPicture
            script_tags = soup.find_all('script', string=re.compile(r'ShowPicture', re.IGNORECASE))
            print(f"      Найдено {len(script_tags)} скриптов с ShowPicture в блоке {block_id}.")

            for script_tag in script_tags:
                script_content = script_tag.get_text()
                img_match = re.search(r"ShowPicture\w*\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", script_content, re.IGNORECASE)
                if img_match:
                    img_src_from_script = img_match.group(1)
                    print(f"        Найден путь к изображению в скрипте: {img_src_from_script}")
                    local_path = download_and_save_image_playwright(page, img_src_from_script, Path("data/assets"), PROJ, BASE, files_location_prefix)
                    new_img_tag = soup.new_tag('img')
                    new_img_tag['src'] = local_path
                    new_img_tag['alt'] = 'Изображение задания'
                    # --- НОВЫЙ КОД: Заменяем скрипт на новый тег ---
                    script_tag.replace_with(new_img_tag)
                    print(f"          Заменён скрипт на <img src='{local_path}'>")

                    # --- НОВЫЙ КОД: Удаление старых img тегов, созданных document.write ---
                    # Найдём все теги img в текущем soup
                    all_img_tags = soup.find_all('img')
                    # Удалим все, кроме нового тега, который мы создали
                    for img_tag in all_img_tags:
                        # Проверим, совпадает ли src с тем, что мы только что вставили
                        if img_tag.get('src') != new_img_tag.get('src'):
                            print(f"          Удалён старый тег <img> с src: {img_tag.get('src')}")
                            img_tag.decompose() # Удаляем тег из дерева
                        else:
                            # Если src совпадает, это наш новый тег, оставляем его
                            pass
                    # --- /НОВЫЙ КОД ---
                else:
                    print(f"        Не удалось извлечь путь к изображению из скрипта: {script_content[:100]}...")

            # Удаление MathML тегов
            for math_tag in soup.find_all(['math', 'mml:math'], recursive=True):
                 math_tag.decompose()

            # Удаляем оставшиеся теги <script> (хотя после replace_with их быть не должно)
            for script_tag in soup.find_all('script'):
                script_tag.decompose()

            cleaned_block_html = str(soup)
            processed_blocks_html.append(cleaned_block_html)

        browser.close()

        print(f"Сохранение результата в {output_html_file}")
        with open(output_html_file, 'w', encoding='utf-8') as f:
            # Добавляем meta charset для правильной кодировки кириллицы в браузере
            for i, block_html in enumerate(processed_blocks_html):
                f.write(f"<div class='processed_qblock' id='processed_qblock_{i}'>\n")
                f.write(block_html)
                f.write("\n</div>\n<hr>\n")
            f.write("</body></html>\n")

        print(f"Обработка завершена. Результат сохранён в {output_html_file}")

def main():
    url = f"{BASE}?proj={PROJ}"
    process_page_with_playwright(url, OUTHTML)

if __name__ == "__main__":
    main()
