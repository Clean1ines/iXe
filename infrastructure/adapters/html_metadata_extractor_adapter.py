import logging
import re
from typing import Dict, List, Any
from bs4 import Tag

logger = logging.getLogger(__name__)

class HTMLMetadataExtractorAdapter:
    def extract_metadata_from_header(self, header_container: Tag) -> Dict[str, Any]:
        """
        Извлекает метаданные из header-элемента в формате bs4.element.Tag
        """
        logger.debug(f"Processing header of type: {type(header_container)}")
        
        # 1. Извлекаем ID из атрибута id
        header_id = header_container.get('id', '')
        task_id = header_id.lstrip('i') if header_id.startswith('i') else ''
        logger.debug(f"Extracted task_id from id attribute: '{task_id}'")
        
        # 2. Извлекаем текст
        header_text = header_container.get_text(strip=True)
        logger.debug(f"Raw header text: '{header_text[:100]}'")
        
        # 3. Исправляем двойную кодировку
        if self._needs_encoding_fix(header_text):
            fixed_text = self._fix_encoding(header_text)
            logger.debug(f"Fixed header text: '{fixed_text[:100]}'")
            header_text = fixed_text
        
        # 4. Извлекаем метаданные
        task_number = self._extract_task_number(header_text)
        kes_codes = self._extract_kes_codes(header_text)
        kos_codes = self._extract_kos_codes(header_text)
        
        return {
            "task_id": task_id,
            "task_number": task_number,
            "kes_codes": kes_codes,
            "kos_codes": kos_codes
        }

    def _needs_encoding_fix(self, text: str) -> bool:
        """Проверяет необходимость исправления двойной кодировки"""
        if not text:
            return False
        # Проверяем на характерные паттерны двойной кодировки
        patterns = [
            r'РљРРЎ',  # "КЭС" в двойной кодировке
            r'РљРћРЎ',  # "КОС" в двойной кодировке
            r'[РС][^\x00-\x7F]{2,}'  # 'Р' или 'С' с несколькими не-ASCII символами
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def _fix_encoding(self, text: str) -> str:
        """Исправляет двойную кодировку текста"""
        try:
            return text.encode('windows-1251').decode('utf-8', errors='replace')
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            logger.warning(f"Encoding fix failed: {e}")
            return text

    def _extract_task_number(self, text: str) -> int:
        """Извлекает номер задания из текста"""
        if not text:
            return 0
            
        # Паттерны для поиска номера задания
        patterns = [
            r'Задание\s*(\d+)',
            r'№\s*(\d+)',
            r'Номер\s+(\d+)',
            r'Свойства\s+задания\s+(\d+)',
            r'СВОЙСТВА\s+ЗАДАНИЯ\s+(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1).isdigit():
                return int(match.group(1))
        
        # Поиск отдельных чисел в диапазоне 1-30
        numbers = re.findall(r'\b([1-9]|[12]\d|30)\b', text)
        for num_str in numbers:
            if num_str.isdigit():
                num = int(num_str)
                if 1 <= num <= 30:
                    return num
        
        return 0

    def _extract_kes_codes(self, text: str) -> List[str]:
        """Извлекает коды КЭС из текста"""
        patterns = [
            r'КЭС\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'Кодификатор\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'[КK][ЭE][СC]\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'РљРРЎ\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)'  # Для двойной кодировки
        ]
        return self._extract_codes(text, patterns)

    def _extract_kos_codes(self, text: str) -> List[str]:
        """Извлекает коды КОС из текста"""
        patterns = [
            r'КОС\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'Требование\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'[КK][ОO][СC]\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)',
            r'РљРћРЎ\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)*)'  # Для двойной кодировки
        ]
        return self._extract_codes(text, patterns)

    def _extract_codes(self, text: str, patterns: List[str]) -> List[str]:
        """Вспомогательный метод для извлечения кодов"""
        codes = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Если это результат с группами захвата
                        code = match[0].strip() if match[0] else ''
                    else:
                        code = match.strip()
                    if code and re.match(r'^\d+\.\d+(?:\.\d+)*$', code):
                        codes.append(code)
        
        # Убираем дубликаты
        return list(set(codes))
