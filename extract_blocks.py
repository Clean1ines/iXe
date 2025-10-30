# extract_blocks.py
import os
from bs4 import BeautifulSoup

INPUT_DIR = "problems/Математика__Профильный_уровень/blocks"
OUTPUT_DIR = "frontend/public/blocks/math"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filename in os.listdir(INPUT_DIR):
    if not filename.endswith(".html"):
        continue

    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(input_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Найти первый (или единственный) блок с классом processed_qblock
    block = soup.find("div", class_="processed_qblock")
    if not block:
        print(f"⚠️  Блок не найден в {filename}")
        continue

    # Сохранить только HTML содержимое блока
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(block))

    print(f"✅ Извлечён: {filename}")

print(f"\nГотово! Блоки сохранены в: {OUTPUT_DIR}")