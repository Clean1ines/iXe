FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей ОС (для Playwright)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Установка Playwright
RUN curl -sS https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Установка Playwright браузеров
RUN playwright install chromium

# Копирование данных и кода
COPY data/ ./data/
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["sh", "-c", "uvicorn core_api_render:app --host 0.0.0.0 --port $PORT"]