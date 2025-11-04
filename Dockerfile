FROM python:3.11-slim as builder

WORKDIR /app

# Системные зависимости для Playwright (только в builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements/requirements_web.txt requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Очистка pip кэша
RUN pip cache purge

# Установка Playwright (браузер) в builder стадии
RUN playwright install chromium

FROM python:3.11-slim as runtime

WORKDIR /app

# Системные зависимости для runtime (только необходимые для запуска)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Копируем установленные пакеты из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Копируем системные библиотеки из builder (если нужно для playwright)
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Копируем только необходимые файлы проекта (без requirements)
COPY . .

# Переменные окружения
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV PYTHONUNBUFFERED=1

# Запуск через run.py
CMD ["python", "run.py"]
