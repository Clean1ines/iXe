"""Module for centralized subject name mappings.

This module defines mappings between official Russian subject names, short aliases,
internal subject keys, and FIPI project IDs. It serves as the central point for
subject identification across the application.
"""

# --- МАППИНГ: Официальное русское название → короткий алиас ---
# Используется для генерации путей к файлам и определения alias внутри Problem и других моделей.
SUBJECT_ALIAS_MAP = {
    "Математика. Базовый уровень": "math",
    "Математика. Профильный уровень": "promath", # NEW
    "Информатика и ИКТ": "inf",
    "Русский язык": "rus",
    "Физика": "phis",
    "Химия": "him",
    "Биология": "bio",
    "История": "hist",
    "Обществознание": "soc",
    "Литература": "lit",
    "География": "geo",
    "Английский язык": "eng",
    "Немецкий язык": "ger",
    "Французский язык": "fra",
    "Испанский язык": "esp",
    "Китайский язык": "chi"
}

# --- МАППИНГ: Алиас (например, из SUBJECT_ALIAS_MAP) → внутренний ключ subject ---
# Используется для идентификации предмета в логике приложения (например, в API, кэшах).
# В идеале, должен совпадать с алиасом, но может отличаться для удобства.
SUBJECT_KEY_MAP = {
    "math": "math",
    "promath": "promath", # NEW
    "inf": "informatics",
    "rus": "russian",
    "phis": "physics",
    "him": "chemistry",
    "bio": "biology",
    "hist": "history",
    "soc": "social",
    "lit": "literature",
    "geo": "geography",
    "eng": "english",
    "ger": "german",
    "fra": "french",
    "esp": "spanish",
    "chi": "chinese"
}

# --- МАППИНГ: Внутренний ключ subject → FIPI proj_id ---
# Используется для формирования URL при скрапинге.
SUBJECT_TO_PROJ_ID_MAP = {
    "math": "E040A72A1A3DABA14C90C97E0B6EE7DC",  # Математика. Базовый уровень
    "promath": "AC437B34557F88EA4115D2F374B0A07B", # NEW: Математика. Профильный уровень
    "informatics": "B9ACA5BBB2E19E434CD6BEC25284C67F",  # Информатика и ИКТ
    "russian": "AF0ED3F2557F8FFC4C06F80B6803FD26",  # Русский язык
    "physics": "BA1F39653304A5B041B656915DC36B38",  # Физика
    "chemistry": "5BAC840990A3AF0A4EE80D1B5A1F9527",  # Химия
    "biology": "CA9D848A31849ED149D382C32A7A2BE4",  # Биология
    "history": "068A227D253BA6C04D0C832387FD0D89",  # История
    "social": "756DF168F63F9A6341711C61AA5EC578",  # Обществознание
    "literature": "4F431E63B9C9B25246F00AD7B5253996",  # Литература
    "geography": "20E79180061DB32845C11FC7BD87C7C8",  # География
    "english": "4B53A6CB75B0B5E1427E596EB4931A2A",  # Английский язык
    "german": "B5963A8D84CF9020461EAE42F37F541F",  # Немецкий язык
    "french": "5BAC840990A3AF0A4EE80D1B5A1F9527",  # Французский язык (ошибка? тот же ID что и химия)
    "spanish": "8C65A335D93D9DA047C42613F61416F3",  # Испанский язык
    "chinese": "F6298F3470D898D043E18BC680F60434",  # Китайский язык
}

# --- МАППИНГ: Алиас → официальное русское название ---
# Используется для отображения человекочитаемых названий.
SUBJECT_TO_OFFICIAL_NAME_MAP = {
    v: k for k, v in SUBJECT_ALIAS_MAP.items() # Базируется на SUBJECT_ALIAS_MAP
}
# SUBJECT_TO_OFFICIAL_NAME_MAP['promath'] будет 'Математика. Профильный уровень' автоматически

# Добавим резервные значения, если алиас не найден в SUBJECT_KEY_MAP или SUBJECT_TO_PROJ_ID_MAP
# DEFAULT_SUBJECT_KEY = "unknown"
# DEFAULT_ALIAS = "unknown"
# DEFAULT_PROJ_ID = "UNKNOWN_PROJ_ID"

def get_alias_from_official_name(official_name: str) -> str:
    """
    Get the short alias for a given official Russian subject name.

    Args:
        official_name (str): The official Russian name of the subject (e.g., 'Математика. Профильный уровень').

    Returns:
        str: The short alias (e.g., 'promath'), or 'unknown' if not found.
    """
    alias = SUBJECT_ALIAS_MAP.get(official_name)
    # if alias is None:
    #     logger.warning(f"get_alias_from_official_name: No alias found for official name: {official_name}")
    #     return DEFAULT_ALIAS
    return alias or "unknown"

def get_subject_key_from_alias(alias: str) -> str:
    """
    Get the internal subject key for a given short alias.

    Args:
        alias (str): The short alias for the subject (e.g., 'promath').

    Returns:
        str: The internal subject key (e.g., 'promath'), or 'unknown' if not found.
    """
    # return SUBJECT_KEY_MAP.get(alias, DEFAULT_SUBJECT_KEY)
    return SUBJECT_KEY_MAP.get(alias, "unknown")

def get_proj_id_for_subject(subject_key: str) -> str:
    """
    Get the FIPI proj_id for a given internal subject key.

    Args:
        subject_key (str): The internal subject key (e.g., 'promath').

    Returns:
        str: The FIPI proj_id (e.g., 'AC437B34557F88EA4115D2F374B0A07B'), or 'UNKNOWN_PROJ_ID' if not found.
    """
    # return SUBJECT_TO_PROJ_ID_MAP.get(subject_key, DEFAULT_PROJ_ID)
    return SUBJECT_TO_PROJ_ID_MAP.get(subject_key, "UNKNOWN_PROJ_ID")

def get_official_name_from_alias(alias: str) -> str:
    """
    Get the official Russian subject name for a given short alias.

    Args:
        alias (str): The short alias (e.g., 'promath').

    Returns:
        str: The official Russian name (e.g., 'Математика. Профильный уровень'), or 'Unknown' if not found.
    """
    # return SUBJECT_TO_OFFICIAL_NAME_MAP.get(alias, DEFAULT_OFFICIAL_NAME)
    return SUBJECT_TO_OFFICIAL_NAME_MAP.get(alias, "Unknown")
