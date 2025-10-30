# run_core_api.py
# Скрипт для запуска Core API с фиктивными зависимостями через uvicorn напрямую

from utils.database_manager import DatabaseManager
from utils.local_storage import LocalStorage
from utils.answer_checker import FIPIAnswerChecker
import config
from pathlib import Path

# Инициализация фиктивных зависимостей
# Укажите путь к вашей существующей базе данных
DB_PATH = "data/math/fipi_data.db" # Измени путь, если нужно
db_manager = DatabaseManager(DB_PATH)
# Убедитесь, что таблицы инициализированы
db_manager.initialize_db()

# Инициализация LocalStorage (можно указать путь к JSON файлу или использовать in-memory)
storage_file = "data/math/answers.json" # Измени путь, если нужно
storage = LocalStorage(Path(storage_file)) # Передаем Path объект

# Инициализация AnswerChecker
checker = FIPIAnswerChecker(base_url=config.FIPI_QUESTIONS_URL)

# Создание приложения *внутри* if __name__ == "__main__" блока
def create_app():
    from api.core_api import create_core_app
    return create_core_app(db_manager, storage, checker)

if __name__ == "__main__":
    import uvicorn
    # Запуск сервера, передаем строку импорта для reload
    # uvicorn будет импортировать функцию create_app и вызывать её
    uvicorn.run("run_core_api:create_app", host="0.0.0.0", port=8001, reload=False, factory=True) # Отключили reload и изменили порт обратно на 8001
