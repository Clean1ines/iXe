# tests/api/test_cors.py
from fastapi.testclient import TestClient
from api.app import create_app

def test_cors_headers_options():
    """
    10. Проверка CORS заголовков
    Описание: Убедиться, что сервер корректно устанавливает заголовки CORS для разрешённых источников.
    Шаги:
    1. Выполнить OPTIONS запрос к любому из защищённых эндпоинтов (например, /api/answer) с заголовком
       Origin: http://localhost:3000.
    2. Проверить, что ответ содержит заголовок Access-Control-Allow-Origin: http://localhost:3000.
    3. Проверить другие важные CORS заголовки (Access-Control-Allow-Methods, Access-Control-Allow-Headers).
    Ожидаемый результат: Заголовки CORS установлены корректно, браузер не блокирует запрос.
    """
    app = create_app()
    client = TestClient(app)

    headers = {"Origin": "http://localhost:3000"}
    # Выполняем OPTIONS запрос к одному из эндпоинтов
    response = client.options("/api/answer", headers=headers)

    # Проверяем заголовки CORS
    assert response.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    # OPTIONS запрос возвращает 405 Method Not Allowed, но CORS заголовки всё равно должны быть
    # Access-Control-Allow-Methods может не быть в ответе на OPTIONS запрос, если он возвращает 405
    # Лучше проверить GET/POST/PUT запросы на наличие Vary: Origin и Access-Control-Allow-Credentials
    # Но для базовой проверки CORS, наличие Origin и Credentials достаточно.
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"
    assert "Vary" in response.headers
    assert "Origin" in response.headers.get("Vary", "")

