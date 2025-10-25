# utils/element_pairer.py
import logging
import re
from typing import List, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag

logger = logging.getLogger(__name__)


class ElementPairer:
    """
    A class to pair 'header container' divs with their corresponding 'qblock' divs.

    This class provides a method to parse a BeautifulSoup object representing
    a FIPI page and find matching pairs of header and question blocks based
    on their order in the document structure. The algorithm expects a 'header'
    (id starting with 'i') followed by a 'qblock'. Only the first qblock found
    after a header, with no *other* div elements in between, is matched to that header.
    """

    def pair(self, page_soup: BeautifulSoup) -> List[Tuple[Tag, Tag]]:
        """
        Finds and pairs 'qblock' divs with their preceding 'header container' divs.

        Args:
            page_soup (BeautifulSoup): The parsed BeautifulSoup object of the page.

        Returns:
            List[Tuple[Tag, Tag]]: A list of tuples, where each tuple contains
                                (header_container_tag, qblock_tag).
        """
        logger.debug("Starting element pairing process.")
        # Находим все div-элементы в порядке их появления в body
        body_children = page_soup.body.children if page_soup.body else []
        ordered_elements = []
        for child in body_children:
            if isinstance(child, Tag) and child.name == 'div':
                element_type = 'other_div' # по умолчанию
                if child.get('class') and 'qblock' in child.get('class'):
                    element_type = 'qblock'
                elif child.get('id') and child.get('id', '').startswith('i'):
                    element_type = 'header'
                ordered_elements.append((element_type, child))

        # --- Добавленный отладочный вывод ---
        print("--- DEBUG: ordered_elements (with other divs) ---")
        for idx, (elem_type, elem_tag) in enumerate(ordered_elements):
            print(f"  [{idx}]: {elem_type}, id='{elem_tag.get('id')}', class='{elem_tag.get('class')}', text='{elem_tag.get_text(strip=True)[:30]}...'")
        print("--------- END DEBUG ---------")
        # --- Конец добавленного вывода ---

        paired_elements = []
        i = 0
        while i < len(ordered_elements):
            element_type, element_tag = ordered_elements[i]
            
            if element_type == 'header':
                # Нашли header, теперь ищем первый следующий qblock
                j = i + 1
                target_qblock_idx = -1
                found_other_div_between = False
                # Ищем первый 'qblock' после текущего 'header'
                while j < len(ordered_elements):
                    if ordered_elements[j][0] == 'qblock':
                        target_qblock_idx = j
                        break
                    # Если встречаем другой 'div', который не header и не qblock, прерываем поиск
                    if ordered_elements[j][0] == 'other_div':
                        found_other_div_between = True
                        # Продолжаем искать следующий qblock, но запоминаем, что был "other"
                        # Цикл продолжится, ищем дальше
                    # Если встречаем другой 'header', прерываем поиск для текущего header
                    if ordered_elements[j][0] == 'header':
                        break
                    j += 1
                
                # --- Добавленный отладочный вывод ---
                print(f"--- DEBUG: Processing header at i={i}, target_qblock_idx={target_qblock_idx}, found_other_div_between={found_other_div_between} ---")
                if target_qblock_idx != -1:
                     print(f"  Found potential qblock at j={target_qblock_idx}")
                else:
                     print(f"  No qblock found after header at i={i}")
                # --- Конец добавленного вывода ---

                # Пара формируется ТОЛЬКО если был найден 'qblock' и НЕ было других div'ов между ними
                if target_qblock_idx != -1 and not found_other_div_between:
                    header_tag = element_tag
                    qblock_tag = ordered_elements[target_qblock_idx][1]
                    paired_elements.append((header_tag, qblock_tag))
                    logger.debug(f"Paired: Header '{header_tag.get('id')}' with QBlock class '{qblock_tag.get('class')}'")
                    print(f"  -> PAIRED: ({header_tag.get('id')}, '{qblock_tag.get_text(strip=True)[:30]}...')") # Отладка
                    i = target_qblock_idx + 1 # Перейти к элементу после найденной пары
                else:
                    # Нет подходящего qblock или между header и qblock есть другие div'ы
                    logger.warning(f"Unpaired header found: id '{element_tag.get('id')}'")
                    print(f"  -> UNPAIRED header: {element_tag.get('id')}") # Отладка
                    i += 1
            else: # element_type == 'qblock' or 'other_div'
                # Просто пропускаем непарные qblock или other_div
                if element_type == 'qblock':
                    logger.warning(f"Unpaired qblock found: class '{element_tag.get('class')}'")
                    print(f"  -> UNPAIRED qblock: '{element_tag.get_text(strip=True)[:30]}...'") # Отладка
                i += 1

        logger.info(f"Successfully paired {len(paired_elements)} header-qblock sets.")
        print(f"--- DEBUG: Final result length: {len(paired_elements)} ---") # Отладка
        return paired_elements
