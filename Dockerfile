# Использовать официальный стабильный образ Python
FROM python:3.11-slim

# Настройка переменных окружения, чтобы Python не буферизировал логи
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Установка рабочей директории в контейнере
WORKDIR /app

# Установка системных зависимостей (необходимы для сборки некоторых библиотек, например psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей и их установка
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Копирование всего проекта в контейнер
COPY . /app/

# Открытие порта для Gunicorn
EXPOSE 8000

# Команда для запуска приложения (замените bot_manager на имя папки с вашим settings.py)
CMD ["gunicorn", "bot_manager.wsgi:application", "--bind", "0.0.0.0:8000"]
