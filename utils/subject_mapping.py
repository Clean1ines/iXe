"""
Module for centralized subject name mappings.

This module defines mappings between official Russian subject names,
short aliases for directories, internal subject keys used by the application
(e.g., for BrowserManager, Database storage), and FIPI project IDs (proj_id).
"""

# --- МАППИНГ: Официальное название → короткий алиас (например, для имён папок) ---
SUBJECT_ALIAS_MAP = {
    "Математика. Профильный уровень": "promath",
    "Математика. Базовый уровень": "basemath",
    "Информатика и ИКТ": "inf",
    "Русский язык": "rus",
    "Физика": "phys",
    "Химия": "chem",
    "Биология": "bio",
    "История": "hist",
    "Обществознание": "soc",
    "Литература": "lit",
    "География": "geo",
    "Английский язык": "eng",
    "Немецкий язык": "de",
    "Французский язык": "fr",
    "Испанский язык": "es",
    "Китайский язык": "zh",
}

# --- МАППИНГ: Алиас (например, из SUBJECT_ALIAS_MAP) → внутренний ключ subject ---
# Используется для сопоставления с proj_id, ключами в BrowserManager, и т.д.
SUBJECT_KEY_MAP = {
    "promath": "math",
    "basemath": "math", # Может быть отдельным, если логика различается
    "inf": "informatics",
    "rus": "russian",
    "phys": "physics",
    "chem": "chemistry",
    "bio": "biology",
    "hist": "history",
    "soc": "social",
    "lit": "literature",
    "geo": "geography",
    "eng": "english",
    "de": "german",
    "fr": "french",
    "es": "spanish",
    "zh": "chinese",
}

# --- МАППИНГ: Внутренний ключ subject → FIPI proj_id ---
# Эти ID нужно уточнить и заполнить актуальными значениями.
SUBJECT_TO_PROJ_ID_MAP = {
    "math": "AC437B34557F88EA4115D2F374B0A07B", # Пример для математики (профиль)
    "informatics": "INFORMATICS_PROJ_ID", # Заменить на реальный ID
    "russian": "RUSSIAN_PROJ_ID", # Заменить на реальный ID
    # Добавить другие предметы по мере необходимости
    # "physics": "...",
    # "chemistry": "...",
    # ...
}

# --- Обратное сопоставление: внутренний ключ subject → официальное название ---
# Полезно, например, для отображения или поиска по subject
SUBJECT_TO_OFFICIAL_NAME_MAP = {
    v: k for k, v in SUBJECT_ALIAS_MAP.items() # Базируется на SUBJECT_ALIAS_MAP
}

# Добавим резервные значения, если алиас не найден в SUBJECT_KEY_MAP или SUBJECT_TO_PROJ_ID_MAP
# DEFAULT_SUBJECT_KEY = "unknown"
# DEFAULT_ALIAS = "unknown"
# DEFAULT_PROJ_ID = "UNKNOWN_PROJ_ID"

def get_alias_from_official_name(official_name: str) -> str:
    """
    Get the short alias for a given official Russian subject name.

    Args:
        official_name: The official Russian name of the subject.

    Returns:
        The short alias, or a sanitized version of the name if not found in the map.
    """
    alias = SUBJECT_ALIAS_MAP.get(official_name)
    if not alias:
        # Fallback: sanitize and use latinized version
        alias = "".join(c if c.isalnum() else "_" for c in official_name.lower())
        alias = alias[:20]  # limit length
    return alias

def get_subject_key_from_alias(alias: str) -> str:
    """
    Get the internal subject key for a given short alias.

    Args:
        alias: The short alias for the subject.

    Returns:
        The internal subject key, or 'unknown' if not found in the map.
    """
    return SUBJECT_KEY_MAP.get(alias, "unknown")

def get_proj_id_for_subject(subject_key: str) -> str:
    """
    Get the FIPI proj_id for a given internal subject key.

    Args:
        subject_key: The internal subject key (e.g., 'math', 'informatics').

    Returns:
        The FIPI proj_id, or a default value if not found in the map.
    """
    return SUBJECT_TO_PROJ_ID_MAP.get(subject_key, "UNKNOWN_PROJ_ID")

def get_official_name_from_alias(alias: str) -> str:
    """
    Get the official Russian subject name for a given short alias.

    Args:
        alias: The short alias for the subject.

    Returns:
        The official Russian name, or 'Unknown' if not found in the map.
    """
    return SUBJECT_TO_OFFICIAL_NAME_MAP.get(alias, "Unknown")

# Примеры использования:
# alias = get_alias_from_official_name("Математика. Профильный уровень")  # -> "promath"
# subject_key = get_subject_key_from_alias("promath")  # -> "math"
# proj_id = get_proj_id_for_subject("math") # -> "AC437B34557F88EA4115D2F374B0A07B"
# official_name = get_official_name_from_alias("promath")  # -> "Математика. Профильный уровень"

