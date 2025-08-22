# Використаємо офіційний образ Python
From python:3.12-slim

# Встановимо робочу директорію всередині контейнера
WORKDIR /app

# Скопіюємо requirements.txt у контейнер
COPY requirements.txt .

# Встановимо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# Скопіюємо код у контейнер
COPY rozetka_notebooks_scraper.py .

# Запустимо скрипт
ENTRYPOINT ["python", "rozetka_notebooks_scraper.py"]