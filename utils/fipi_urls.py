"""Module containing FIPI website URLs."""

# FIPI Base URL
FIPI_BASE_URL = "https://ege.fipi.ru"

# FIPI Subjects Listing Page (the actual page with subject links)
FIPI_SUBJECTS_LIST_URL = f"{FIPI_BASE_URL}/bank/index.php"

# FIPI Questions Page Base URL (used for scraping individual tasks)
FIPI_QUESTIONS_URL = f"{FIPI_BASE_URL}/bank/questions.php"

# FIPI Bank Root (can be used if needed, currently shows only copyright)
FIPI_BANK_ROOT_URL = f"{FIPI_BASE_URL}/bank"
