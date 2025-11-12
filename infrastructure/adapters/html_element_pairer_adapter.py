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
    on their order and IDs in the document structure.
    It correctly handles sequences like 'qblock' -> 'header' and 'header' -> 'qblock'.
    A 'qblock' (e.g., id='q40B442') is paired with a 'header' (e.g., id='i40B442')
    if their IDs match (qXXXX -> iXXXX).
    """

    def pair(self, page_soup: BeautifulSoup) -> List[Tuple[Tag, Tag]]:
        """
        Finds and pairs 'qblock' divs with their corresponding 'header container' divs
        based on matching IDs.

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
                    # Извлекаем ID qblock, убирая 'q'
                    q_id = child.get('id', '').lstrip('q')
                    element_id = q_id if q_id else None
                elif child.get('id') and child.get('id', '').startswith('i'):
                    element_type = 'header'
                    # Извлекаем ID header, убирая 'i'
                    h_id = child.get('id', '').lstrip('i')
                    element_id = h_id if h_id else None
                else:
                    element_id = None
                ordered_elements.append((element_type, child, element_id))

        # --- Добавленный отладочный вывод ---
        print("--- DEBUG: ordered_elements (with other divs) ---")
        for idx, (elem_type, elem_tag, elem_id) in enumerate(ordered_elements):
            print(f"  [{idx}]: {elem_type}, id='{elem_tag.get('id')}', class='{elem_tag.get('class')}', extracted_id='{elem_id}', text='{elem_tag.get_text(strip=True)[:30]}...'")
        print("--------- END DEBUG ---------")
        # --- Конец добавленного вывода ---

        paired_elements = []
        # Список для отслеживания уже использованных индексов (для header и qblock)
        used_indices = set()

        # Проходим по списку
        i = 0
        while i < len(ordered_elements):
            element_type, element_tag, element_id = ordered_elements[i]

            if element_type == 'qblock' and element_id:
                # Нашли qblock с ID. Проверим, был ли он использован.
                if i in used_indices:
                    i += 1
                    continue

                # Ищем *ближайший следующий* непарный header с *совпадающим* ID.
                next_header_idx = -1
                j = i + 1
                while j < len(ordered_elements):
                    next_type, next_tag, next_id = ordered_elements[j]
                    if next_type == 'header' and next_id == element_id and j not in used_indices:
                        next_header_idx = j
                        break
                    # Если встречаем другой qblock раньше header, останавливаем поиск
                    if next_type == 'qblock':
                        break
                    j += 1

                # --- Добавленный отладочный вывод ---
                print(f"--- DEBUG: Processing qblock at i={i} (id={element_id}), next_matching_header_idx={next_header_idx} ---")
                # --- Конец добавленного вывода ---

                if next_header_idx != -1:
                    # Найден непарный следующий header с совпадающим ID. Создаём пару.
                    qblock_tag = element_tag
                    header_tag = ordered_elements[next_header_idx][1]
                    paired_elements.append((header_tag, qblock_tag)) # (header, qblock)
                    used_indices.add(i)
                    used_indices.add(next_header_idx)
                    logger.debug(f"Paired: QBlock class '{qblock_tag.get('class')}' (id q{element_id}) with Header '{header_tag.get('id')}' (id i{element_id}) (next)")
                    print(f"  -> PAIRED (q->h, next): (i{element_id}, '...{qblock_tag.get_text(strip=True)[:30]}...')") # Отладка
                else:
                    # Не нашли подходящий header после. Попробуем найти *ближайший предыдущий* непарный header с совпадающим ID.
                    prev_header_idx = -1
                    j = i - 1
                    while j >= 0:
                        prev_type, prev_tag, prev_id = ordered_elements[j]
                        if prev_type == 'header' and prev_id == element_id and j not in used_indices:
                            prev_header_idx = j
                            break
                        # Если встречаем другой qblock раньше header, останавливаем поиск
                        if prev_type == 'qblock':
                            break
                        j -= 1

                    # --- Добавленный отладочный вывод ---
                    print(f"--- DEBUG: Processing qblock at i={i} (id={element_id}), prev_matching_header_idx={prev_header_idx} ---")
                    # --- Конец добавленного вывода ---

                    if prev_header_idx != -1:
                        # Найден непарный предыдущий header с совпадающим ID. Создаём пару.
                        header_tag = ordered_elements[prev_header_idx][1]
                        qblock_tag = element_tag
                        paired_elements.append((header_tag, qblock_tag)) # (header, qblock)
                        used_indices.add(prev_header_idx)
                        used_indices.add(i)
                        logger.debug(f"Paired: QBlock class '{qblock_tag.get('class')}' (id q{element_id}) with Header '{header_tag.get('id')}' (id i{element_id}) (prev)")
                        print(f"  -> PAIRED (q->h, prev): (i{element_id}, '...{qblock_tag.get_text(strip=True)[:30]}...')") # Отладка
                    # Если нет подходящего header ни до, ни после, qblock остаётся непарным.

            elif element_type == 'header' and element_id:
                # Нашли header с ID. Проверим, был ли он использован.
                if i in used_indices:
                    i += 1
                    continue

                # Ищем *ближайший предыдущий* непарный qblock с *совпадающим* ID.
                prev_qblock_idx = -1
                j = i - 1
                while j >= 0:
                    prev_type, prev_tag, prev_id = ordered_elements[j]
                    if prev_type == 'qblock' and prev_id == element_id and j not in used_indices:
                        prev_qblock_idx = j
                        break
                    # Если встречаем другой header раньше qblock, останавливаем поиск
                    if prev_type == 'header':
                        break
                    j -= 1

                # --- Добавленный отладочный вывод ---
                print(f"--- DEBUG: Processing header at i={i} (id={element_id}), prev_matching_qblock_idx={prev_qblock_idx} ---")
                # --- Конец добавленного вывода ---

                if prev_qblock_idx != -1:
                    # Найден непарный предыдущий qblock с совпадающим ID. Создаём пару.
                    header_tag = element_tag
                    qblock_tag = ordered_elements[prev_qblock_idx][1]
                    paired_elements.append((header_tag, qblock_tag)) # (header, qblock)
                    used_indices.add(i)
                    used_indices.add(prev_qblock_idx)
                    logger.debug(f"Paired: Header '{header_tag.get('id')}' (id i{element_id}) with QBlock class '{qblock_tag.get('class')}' (id q{element_id}) (prev)")
                    print(f"  -> PAIRED (h->q, prev): (i{element_id}, '...{qblock_tag.get_text(strip=True)[:30]}...')") # Отладка
                else:
                    # Не нашли подходящий qblock до. Попробуем найти *ближайший следующий* непарный qblock с совпадающим ID.
                    next_qblock_idx = -1
                    j = i + 1
                    while j < len(ordered_elements):
                        next_type, next_tag, next_id = ordered_elements[j]
                        if next_type == 'qblock' and next_id == element_id and j not in used_indices:
                            next_qblock_idx = j
                            break
                        # Если встречаем другой header раньше qblock, останавливаем поиск
                        if next_type == 'header':
                            break
                        j += 1

                    # --- Добавленный отладочный вывод ---
                    print(f"--- DEBUG: Processing header at i={i} (id={element_id}), next_matching_qblock_idx={next_qblock_idx} ---")
                    # --- Конец добавленного вывода ---

                    if next_qblock_idx != -1:
                        # Найден непарный следующий qblock с совпадающим ID. Создаём пару.
                        header_tag = element_tag
                        qblock_tag = ordered_elements[next_qblock_idx][1]
                        paired_elements.append((header_tag, qblock_tag)) # (header, qblock)
                        used_indices.add(i)
                        used_indices.add(next_qblock_idx)
                        logger.debug(f"Paired: Header '{header_tag.get('id')}' (id i{element_id}) with QBlock class '{qblock_tag.get('class')}' (id q{element_id}) (next)")
                        print(f"  -> PAIRED (h->q, next): (i{element_id}, '...{qblock_tag.get_text(strip=True)[:30]}...')") # Отладка
                    # Если нет подходящего qblock ни до, ни после, header остаётся непарным.

            # other_div или элемент без ID просто пропускаем
            i += 1

        # Теперь пройдемся по оставшимся элементам, чтобы вывести непарные
        for idx, (elem_type, elem_tag, elem_id) in enumerate(ordered_elements):
            if idx not in used_indices:
                if elem_type == 'header':
                    logger.warning(f"Unpaired header found: id '{elem_tag.get('id')}'")
                    print(f"  -> UNPAIRED header: {elem_tag.get('id')}") # Отладка
                elif elem_type == 'qblock':
                    logger.warning(f"Unpaired qblock found: class '{elem_tag.get('class')}', id '{elem_tag.get('id')}'")
                    print(f"  -> UNPAIRED qblock: '{elem_tag.get_text(strip=True)[:30]}...' (id {elem_tag.get('id')})") # Отладка

        logger.info(f"Successfully paired {len(paired_elements)} header-qblock sets.")
        print(f"--- DEBUG: Final result length: {len(paired_elements)} ---") # Отладка
        return paired_elements

