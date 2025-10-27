FROM python:3.11-slim

WORKDIR /app

# Install build dependencies (for lxml, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the pre-scraped database (must exist in ./data/fipi_data.db)
COPY data/fipi_data.db ./data/fipi_data.db

# Copy source code
COPY . .

# Ensure non-buffered output
ENV PYTHONUNBUFFERED=1

# Render passes PORT at runtime
CMD ["sh", "-c", "uvicorn api.core_api_render:app --host 0.0.0.0 --port $PORT"]
