import os
import sys
import subprocess
import json
import importlib.util
from pathlib import Path
import argparse
import ast # Для парсинга исходного кода Python

# --- Цвета для вывода ---
try:
    from colorama import init, Fore, Style
    init() # Инициализация colorama для Windows/Unix
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    # Заглушки, если colorama не установлена
    class MockFore: pass
    class MockStyle: pass
    Fore = MockFore()
    Style = MockStyle()
    Fore.RED = Fore.GREEN = Fore.YELLOW = Fore.CYAN = Fore.MAGENTA = Fore.RESET = ''
    Style.BRIGHT = Style.RESET_ALL = ''

# --- Конфигурация ---
PROJECT_ROOT = Path(__file__).parent.resolve()
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
DOCKERFILE_FILE = PROJECT_ROOT / "Dockerfile"
RENDER_YAML_FILE = PROJECT_ROOT / "render.yaml"
API_DIR = PROJECT_ROOT / "api"
SCRAPER_DIR = PROJECT_ROOT / "scraper"
UTILS_DIR = PROJECT_ROOT / "utils"
MODELS_DIR = PROJECT_ROOT / "models"
PROCESSORS_DIR = PROJECT_ROOT / "processors"
SERVICES_DIR = PROJECT_ROOT / "services"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CONFIG_DIR = PROJECT_ROOT / "config"
QDRANT_CONFIG_FILE = CONFIG_DIR / "qdrant_config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE_FILE = PROJECT_ROOT / ".env.example"

def parse_args():
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(description='Audit script for iXe project.')
    parser.add_argument('--summary-only', action='store_true', help='Print only the summary.')
    return parser.parse_args()

def color_print(text, color_code=Fore.WHITE):
    """Печатает текст с цветом, если colorama доступна."""
    if COLORS_AVAILABLE:
        print(f"{color_code}{text}{Fore.RESET}")
    else:
        print(text)

def run_command(cmd, shell=True):
    """Выполняет команду в shell и возвращает результат."""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=True)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip()

def get_imports_from_file(filepath):
    """Парсит Python-файл и возвращает множество импортированных модулей."""
    imports = set()
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0]) # Берем только корень импорта (e.g., 'os' из 'os.path')
            elif isinstance(node, ast.ImportFrom):
                if node.module: # from . import something не учитывается
                    imports.add(node.module.split('.')[0])
    except (SyntaxError, UnicodeDecodeError):
        pass # Игнорируем файлы с синтаксическими ошибками или неправильной кодировкой
    return imports

def get_all_imports_from_project(project_root):
    """Собирает все импорты из всех Python-файлов в проекте."""
    all_imports = set()
    for py_file in project_root.rglob("*.py"):
        all_imports.update(get_imports_from_file(py_file))
    return all_imports

def check_python_profiling():
    """Проверяет наличие инструментов профилирования."""
    color_print("--- 1. Оптимизация Python и Управление Памятью ---", Fore.CYAN)
    tools = ["memory_profiler", "py-spy", "cProfile", "tracemalloc"]
    found_tools = []
    for tool in tools:
        try:
            importlib.util.find_spec(tool.replace("-", "_"))
            found_tools.append(tool)
        except ImportError:
            pass
    if found_tools:
        color_print(f"  Найденные инструменты профилирования: {found_tools}", Fore.GREEN)
    else:
        color_print("  Найденные инструменты профилирования: Нет", Fore.RED)

    color_print("  Рекомендация: Рассмотрите установку memory_profiler или py-spy для профилирования.", Fore.YELLOW)
    color_print("  Также доступен встроенный модуль 'tracemalloc'.", Fore.YELLOW)
    color_print("  Рекомендация: Проверьте использование __slots__, генераторов, и эффективных структур данных (dict, set, collections.deque).", Fore.YELLOW)
    color_print("  Рекомендация: Используйте gc.collect() в стратегических местах, особенно после тяжелых операций.", Fore.YELLOW)


def check_dockerfile():
    """Проверяет структуру Dockerfile."""
    color_print("\n--- 2. Оптимизация Docker-образов ---", Fore.CYAN)
    if not DOCKERFILE_FILE.exists():
        color_print(f"  Файл {DOCKERFILE_FILE} не найден в корне проекта ({PROJECT_ROOT}).", Fore.RED)
        color_print("  Рекомендация: Создайте Dockerfile в корне проекта для контейнеризации.", Fore.YELLOW)
        return

    try:
        with open(DOCKERFILE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        color_print(f"  Ошибка чтения {DOCKERFILE_FILE}: невозможно декодировать как UTF-8.", Fore.RED)
        return

    # Улучшенная проверка многоступенчатой сборки
    lines = content.splitlines()
    from_count = 0
    builder_stage_found = False
    runtime_stage_found = False
    copy_from_builder_found = False

    for line in lines:
        stripped_line = line.strip().upper()
        if stripped_line.startswith('FROM'):
            from_count += 1
            if 'AS' in stripped_line:
                builder_stage_found = True
            else:
                if builder_stage_found and not runtime_stage_found:
                    runtime_stage_found = True
        elif stripped_line.startswith('COPY') and '--FROM=' in stripped_line.upper():
            copy_from_builder_found = True

    has_multistage = from_count > 1 and builder_stage_found and runtime_stage_found and copy_from_builder_found
    has_user_install = "pip install --user" in content
    has_cache_purge = "pip cache purge" in content
    has_dockerignore = (PROJECT_ROOT / ".dockerignore").exists()
    has_slim_base = "slim" in content.lower()

    # Проверка установки playwright install в runtime стадии
    has_playwright_install_in_main_stage = False
    if runtime_stage_found:
        runtime_start_idx = -1
        for i in reversed(range(len(lines))):
            if lines[i].strip().upper().startswith('FROM') and 'AS' not in lines[i].strip().upper():
                runtime_start_idx = i
                break
        if runtime_start_idx != -1:
            runtime_content = "\n".join(lines[runtime_start_idx:])
            copy_from_line_idx = -1
            for i, line in enumerate(lines[runtime_start_idx:]):
                if '--FROM=' in line.upper():
                    copy_from_line_idx = i
                    break
            if copy_from_line_idx != -1:
                if 'PLAYWRIGHT INSTALL' in content[runtime_start_idx + copy_from_line_idx:].upper():
                    has_playwright_install_in_main_stage = True

    # Проверка установки qdrant в Dockerfile
    has_qdrant_install = "qdrant" in content.lower()

    color_print(f"  Многоступенчатая сборка: {'Да' if has_multistage else 'Нет'}", Fore.GREEN if has_multistage else Fore.RED)
    color_print(f"  Использование pip install --user: {'Да' if has_user_install else 'Нет'}", Fore.GREEN if has_user_install else Fore.RED)
    color_print(f"  Очистка кэша pip: {'Да' if has_cache_purge else 'Нет'}", Fore.GREEN if has_cache_purge else Fore.RED)
    color_print(f"  Наличие .dockerignore: {'Да' if has_dockerignore else 'Нет'}", Fore.GREEN if has_dockerignore else Fore.RED)
    color_print(f"  Использование slim базового образа: {'Да' if has_slim_base else 'Нет'}", Fore.GREEN if has_slim_base else Fore.RED)

    if has_playwright_install_in_main_stage:
        color_print("  ВНИМАНИЕ: 'playwright install' найден в финальной стадии Dockerfile. Это НЕДОПУСТИМО для веб-API сервиса!", Fore.RED)
    if has_qdrant_install:
        color_print("  ВНИМАНИЕ: 'qdrant' найден в Dockerfile. Убедитесь, что Qdrant запускается как ОТДЕЛЬНЫЙ сервис, а не устанавливается в веб-API.", Fore.YELLOW)

    if not has_multistage:
        color_print("  Рекомендация: Реализуйте многоступенчатую сборку (multi-stage build).", Fore.YELLOW)
    if not has_cache_purge:
        color_print("  Рекомендация: Добавьте 'RUN pip cache purge' в Dockerfile.", Fore.YELLOW)
    if not has_dockerignore:
        color_print("  Рекомендация: Создайте .dockerignore и исключите venv/, .git/, tests/, node_modules/.", Fore.YELLOW)


def check_requirements():
    """Проверяет зависимости и сравнивает с импортами."""
    color_print("\n--- 3. Оптимизация зависимостей и `requirements.txt` ---", Fore.CYAN)
    if not REQUIREMENTS_FILE.exists():
        color_print(f"  Файл {REQUIREMENTS_FILE} не найден.", Fore.RED)
        return

    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
            req_lines = f.readlines()
    except UnicodeDecodeError:
        color_print(f"  Ошибка чтения {REQUIREMENTS_FILE}: невозможно декодировать как UTF-8.", Fore.RED)
        return

    # 1. Сравнение с импортами (упрощенная версия - список всех .py файлов)
    color_print("  Сравнение с импортами (требуется ручная проверка или pipreqs):", Fore.YELLOW)
    color_print("    - Установите 'pipreqs': pip install pipreqs", Fore.YELLOW)
    color_print("    - Запустите: pipreqs . --force", Fore.YELLOW)
    color_print("    - Сравните результат с requirements.txt и удалите неиспользуемые зависимости.", Fore.YELLOW)
    color_print("    - Проверьте 'pipdeptree' для анализа зависимостей.", Fore.YELLOW)

    # 2. Проверка версий
    reqs_with_versions = [line.strip() for line in req_lines if '==' in line]
    reqs_without_versions = [line.strip() for line in req_lines if '==' not in line and line.strip() and not line.strip().startswith('#')]
    color_print(f"  Зависимостей с фиксированной версией (==): {len(reqs_with_versions)}", Fore.GREEN)
    color_print(f"  Зависимостей без фиксированной версии: {len(reqs_without_versions)}", Fore.RED)
    if reqs_without_versions:
        color_print(f"    Зависимости без фиксированной версии: {reqs_without_versions}", Fore.RED)
        color_print("  Рекомендация: Укажите конкретные версии (==) в requirements.txt для стабильности.", Fore.YELLOW)

    # 3. Проверка на критические зависимости в веб-API
    req_content_lower = "".join(req_lines).lower()
    has_playwright_in_reqs = 'playwright' in req_content_lower
    has_qdrant_client_in_reqs = 'qdrant-client' in req_content_lower

    if has_playwright_in_reqs:
        color_print("  ВНИМАНИЕ: 'playwright' найден в requirements.txt. Убедитесь, что он НЕ установлен в веб-API сервисе!", Fore.RED)
    if has_qdrant_client_in_reqs:
        color_print("  ВНИМАНИЕ: 'qdrant-client' найден в requirements.txt. Убедитесь, что он НЕ установлен в веб-API сервисе!", Fore.RED)

    # 4. Разделение зависимостей (проверка на наличие dev-requirements.txt)
    dev_req_file = PROJECT_ROOT / "dev-requirements.txt"
    color_print(f"  Наличие dev-requirements.txt: {'Да' if dev_req_file.exists() else 'Нет'}", Fore.GREEN if dev_req_file.exists() else Fore.YELLOW)
    if not dev_req_file.exists():
        color_print("  Рекомендация: Рассмотрите создание dev-requirements.txt для зависимостей разработки/тестирования.", Fore.YELLOW)

def check_unused_dependencies():
    """Проверяет, какие зависимости из requirements.txt не используются в коде."""
    color_print("\n--- 3.1 Анализ неиспользуемых зависимостей ---", Fore.CYAN)
    if not REQUIREMENTS_FILE.exists():
        color_print(f"  Файл {REQUIREMENTS_FILE} не найден. Пропуск анализа.", Fore.RED)
        return

    try:
        with open(REQUIREMENTS_FILE, 'r', encoding='utf-8') as f:
            req_lines = f.readlines()
    except UnicodeDecodeError:
        color_print(f"  Ошибка чтения {REQUIREMENTS_FILE}: невозможно декодировать как UTF-8.", Fore.RED)
        return

    # Извлекаем имена пакетов из requirements.txt (без версий, без комментариев)
    req_packages = set()
    for line in req_lines:
        line = line.strip()
        if line and not line.startswith('#'):
            # Убираем версию и спецификаторы (e.g., ==, >=, <)
            package_name = line.split('=')[0].split('[')[0].split('>')[0].split('<')[0].split('!')[0].strip()
            req_packages.add(package_name.lower())

    # Извлекаем импорты из кода
    code_imports = get_all_imports_from_project(PROJECT_ROOT)
    # print(f"DEBUG: req_packages: {req_packages}") # Для отладки
    # print(f"DEBUG: code_imports: {code_imports}") # Для отладки

    # Находим неиспользуемые зависимости
    unused_deps = req_packages - code_imports

    if unused_deps:
        color_print(f"  Найдены потенциально неиспользуемые зависимости в requirements.txt ({len(unused_deps)}):", Fore.RED)
        for dep in sorted(unused_deps):
            color_print(f"    - {dep}", Fore.RED)
        color_print("  Рекомендация: Проверьте, действительно ли эти пакеты не нужны. Их можно удалить из requirements.txt.", Fore.YELLOW)
    else:
        color_print("  Неиспользуемых зависимостей, найденных в requirements.txt, не обнаружено.", Fore.GREEN)

    # Находим импорты, отсутствующие в requirements.txt (потенциально забытые)
    missing_from_reqs = code_imports - req_packages
    # Убираем стандартную библиотеку Python
    stdlib = set(sys.builtin_module_names)
    # Примерный список модулей стандартной библиотеки (для более точной проверки нужно использовать pkgutil)
    # Этот список не полный, но покрывает основные.
    stdlib.update(['abc', 'aifc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'audioop', 'base64', 'bdb', 'binascii', 'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code', 'codecs', 'codeop', 'collections', 'colorsys', 'compileall', 'concurrent', 'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg', 'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm', 'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings', 'ensurepip', 'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext', 'glob', 'graphlib', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http', 'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io', 'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache', 'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math', 'mimetypes', 'mmap', 'modulefinder', 'msilib', 'msvcrt', 'multiprocessing', 'netrc', 'nis', 'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev', 'parser', 'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform', 'plistlib', 'poplib', 'posix', 'pprint', 'profile', 'pstats', 'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri', 'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy', 'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver', 'spwd', 'sqlite3', 'ssl', 'stat', 'statistics', 'statvfs', 'string', 'stringprep', 'struct', 'subprocess', 'sunau', 'symbol', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny', 'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading', 'time', 'timeit', 'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types', 'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv', 'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound', 'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport', 'zlib', 'zoneinfo'])
    missing_from_reqs = missing_from_reqs - stdlib

    if missing_from_reqs:
        color_print(f"\n  Найдены импорты, отсутствующие в requirements.txt ({len(missing_from_reqs)}):", Fore.YELLOW)
        for imp in sorted(missing_from_reqs):
            color_print(f"    - {imp}", Fore.YELLOW)
        color_print("  Рекомендация: Проверьте, нужно ли добавить эти пакеты в requirements.txt (или dev-requirements.txt).", Fore.YELLOW)


def check_playwright_usage():
    """Проверяет использование Playwright."""
    color_print("\n--- 4. Оптимизация Playwright ---", Fore.CYAN)
    browser_manager_file = UTILS_DIR / "browser_manager.py"
    browser_pool_manager_file = UTILS_DIR / "browser_pool_manager.py"
    answer_checker_file = UTILS_DIR / "answer_checker.py"
    scraper_file = SCRAPER_DIR / "fipi_scraper.py"
    scrape_script = SCRIPTS_DIR / "scrape_tasks.py"

    files_to_check = [browser_manager_file, browser_pool_manager_file, answer_checker_file, scraper_file, scrape_script]
    found_playwright_usage = any(f.exists() for f in files_to_check)

    if found_playwright_usage:
        color_print("  Использование Playwright обнаружено в следующих файлах:", Fore.GREEN)
        for f in files_to_check:
            if f.exists():
                color_print(f"    - {f}", Fore.GREEN)
        color_print("  Рекомендация: Убедитесь, что BrowserManager и BrowserPoolManager корректно управляют жизненным циклом браузеров и страниц.", Fore.YELLOW)
        color_print("  Рекомендация: Проверьте использование headless=True и отключения ненужных ресурсов (изображения, CSS, JS).", Fore.YELLOW)
    else:
        color_print("  Использование Playwright не обнаружено в стандартных местах.", Fore.RED)


def check_qdrant_config():
    """Проверяет конфигурацию Qdrant."""
    color_print("\n--- 5. Оптимизация Qdrant ---", Fore.CYAN)
    if not QDRANT_CONFIG_FILE.exists():
        color_print("  Файл конфигурации Qdrant (config/qdrant_config.yaml) не найден.", Fore.RED)
        color_print("  Рекомендация: Создайте config/qdrant_config.yaml и настройте параметры, такие как quantization, hnsw_config, optimizer_config.", Fore.YELLOW)
        return

    color_print(f"  Файл конфигурации Qdrant найден: {QDRANT_CONFIG_FILE}", Fore.GREEN)
    try:
        with open(QDRANT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        color_print(f"  Ошибка чтения {QDRANT_CONFIG_FILE}: невозможно декодировать как UTF-8.", Fore.RED)
        return
    has_quantization = "quantization" in content.lower()
    has_hnsw = "hnsw" in content.lower()
    has_optimizer = "optimizer" in content.lower()

    color_print(f"    Наличие настроек quantization: {'Да' if has_quantization else 'Нет'}", Fore.GREEN if has_quantization else Fore.RED)
    color_print(f"    Наличие настроек hnsw: {'Да' if has_hnsw else 'Нет'}", Fore.GREEN if has_hnsw else Fore.RED)
    color_print(f"    Наличие настроек optimizer: {'Да' if has_optimizer else 'Нет'}", Fore.GREEN if has_optimizer else Fore.RED)
    color_print("  Рекомендация: Изучите и настройте параметры конфигурации Qdrant для уменьшения потребления памяти.", Fore.YELLOW)


def check_sqlite_usage():
    """Проверяет использование SQLite."""
    color_print("\n--- 6. Оптимизация доступа к базе данных (SQLite) ---", Fore.CYAN)
    db_manager_file = UTILS_DIR / "database_manager.py"
    if db_manager_file.exists():
        color_print(f"  Использование DatabaseManager обнаружено: {db_manager_file}", Fore.GREEN)
        color_print("  Рекомендация: Проверьте использование пула соединений (SQLAlchemy QueuePool).", Fore.YELLOW)
        color_print("  Рекомендация: Убедитесь, что транзакции объединяют несколько операций.", Fore.YELLOW)
        color_print("  Рекомендация: Проверьте наличие индексов на часто используемых полях (WHERE, JOIN, ORDER BY).", Fore.YELLOW)
        color_print("  Рекомендация: Рассмотрите включение WAL режима (PRAGMA journal_mode=WAL;).", Fore.YELLOW)
        color_print("  Рекомендация: Используйте executemany для пакетных операций.", Fore.YELLOW)
        color_print("  Рекомендация: Избегайте SELECT *.", Fore.YELLOW)
    else:
        color_print("  Файл DatabaseManager не найден.", Fore.RED)


def check_architecture():
    """Проверяет архитектурные аспекты."""
    color_print("\n--- 7. Архитектурные и Алгоритмические Оптимизации ---", Fore.CYAN)
    has_separation = all(d.exists() for d in [API_DIR, SCRAPER_DIR, UTILS_DIR, MODELS_DIR, PROCESSORS_DIR])
    color_print(f"  Наличие разделения на слои (api, scraper, utils, models, processors): {'Да' if has_separation else 'Нет'}", Fore.GREEN if has_separation else Fore.RED)

    cache_found = False
    for py_file in PROJECT_ROOT.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
                if "lru_cache" in file_content or "cache" in file_content.lower():
                    cache_found = True
                    color_print(f"    Найдено упоминание кэширования в: {py_file}", Fore.GREEN)
                    break
        except UnicodeDecodeError:
            continue
    color_print(f"  Наличие потенциального кэширования (lru_cache и др.): {'Да' if cache_found else 'Нет'}", Fore.GREEN if cache_found else Fore.RED)

    color_print("  Рекомендация: Проверьте эффективность алгоритмов в QuizService, TaskNumberInferer, QdrantProblemRetriever.", Fore.YELLOW)
    color_print("  Рекомендация: Убедитесь, что асинхронные операции (I/O) действительно асинхронны (async/await).", Fore.YELLOW)


def check_logging():
    """Проверяет настройку логирования."""
    color_print("\n--- 8. Мониторинг и Логирование ---", Fore.CYAN)
    logging_config_file = UTILS_DIR / "logging_config.py"
    if logging_config_file.exists():
        color_print(f"  Использование logging_config.py обнаружено: {logging_config_file}", Fore.GREEN)
        color_print("  Рекомендация: Проверьте уровни логирования (INFO, WARNING, ERROR) и их использование в коде.", Fore.YELLOW)
        color_print("  Рекомендация: Постоянно мониторьте логи Render Dashboard на предмет ошибок и SIGKILL/Out of memory.", Fore.YELLOW)
    else:
        color_print("  Файл logging_config.py не найден.", Fore.RED)
        color_print("  Рекомендация: Рассмотрите централизованную настройку логирования.", Fore.YELLOW)

def check_config():
    """Проверяет управление конфигурацией."""
    color_print("\n--- 9. Управление конфигурацией ---", Fore.CYAN)
    color_print(f"  Наличие .env: {'Да' if ENV_FILE.exists() else 'Нет'}", Fore.GREEN if ENV_FILE.exists() else Fore.RED)
    color_print(f"  Наличие .env.example: {'Да' if ENV_EXAMPLE_FILE.exists() else 'Нет'}", Fore.GREEN if ENV_EXAMPLE_FILE.exists() else Fore.YELLOW)
    if not ENV_EXAMPLE_FILE.exists():
        color_print("  Рекомендация: Создайте .env.example с примерами переменных окружения.", Fore.YELLOW)

def generate_summary(report_lines):
    """Генерирует краткий итог."""
    summary_lines = [
        "\n" + "="*40,
        "КРАТКИЙ ИТОГ АУДИТА",
        "="*40
    ]
    problem_count = sum(1 for line in report_lines if any(x in line for x in [Fore.RED, "ВНИМАНИЕ:", "Рекомендация:"]))
    missing_items = sum(1 for line in report_lines if "Нет" in line and "Наличие" in line)
    summary_lines.append(f"Найдено потенциальных проблем / областей для улучшения: {problem_count}")
    summary_lines.append(f"Найдено отсутствующих элементов (файлов/настроек): {missing_items}")
    summary_lines.extend([
        "\n--- Ключевые области для оптимизации: ---",
        "- Dockerfile (многоступенчатая сборка, очистка кэша, ОТСУТСТВИЕ playwright install в runtime)",
        "- requirements.txt (удаление лишних зависимостей, фиксация версий, ОТСУТСТВИЕ playwright/qdrant-client в веб-API)",
        "- Управление памятью в Python (особенно с Playwright)",
        "- Конфигурация Qdrant (quantization и др.)",
        "- Доступ к SQLite (транзакции, индексы, WAL)",
        "- Неиспользуемые зависимости в requirements.txt",
        "="*40
    ])
    return summary_lines


def main():
    args = parse_args()
    print("=== Аудит проекта iXe (Улучшенная версия с анализом зависимостей) ===\n")
    report_lines = []
    report_lines.append("=== Аудит проекта iXe (Улучшенная версия с анализом зависимостей) ===\n")

    import io
    from contextlib import redirect_stdout

    # Обновленный список проверок
    checks_to_run = [
        check_python_profiling, check_dockerfile, check_requirements,
        check_unused_dependencies, # Новая проверка
        check_playwright_usage, check_qdrant_config, check_sqlite_usage,
        check_architecture, check_logging, check_config
    ]

    for check_func in checks_to_run:
        f = io.StringIO()
        with redirect_stdout(f):
            check_func()
        output = f.getvalue()
        if not args.summary_only:
            print(output)
        report_lines.append(output)

    summary_lines = generate_summary(report_lines)
    summary_text = "\n".join(summary_lines)
    print(summary_text)
    report_lines.append(summary_text)

    report_filename = PROJECT_ROOT / "audit_report.txt"
    with open(report_filename, 'w', encoding='utf-8') as report_file:
        report_file.write("\n".join(report_lines))

    color_print(f"\n--- Аудит завершен. Полный отчет сохранен в {report_filename} ---", Fore.MAGENTA)

    if args.summary_only:
        print("\n(Выведен только краткий итог по флагу --summary-only)")


if __name__ == "__main__":
    main()

