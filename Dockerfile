FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Переменные окружения по умолчанию
ENV TELEGRAM_BOT_TOKEN=""
ENV MISTRAL_API_KEY=""
ENV MISTRAL_MODEL="mistral-small-latest"
ENV LOG_LEVEL="INFO"

# Создаём non-root пользователя для безопасности 
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Healthcheck (для docker-compose)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import os; exit(0 if os.getenv('TELEGRAM_BOT_TOKEN') else 1)" || exit 1

CMD ["python", "main.py"]