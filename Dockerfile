# Використаємо офіційний образ Python
FROM python:3.12-slim

# Встановимо робочу директорію
WORKDIR /app

# Скопіюємо requirements.txt
COPY requirements.txt .

# Встановимо бібліотеки
RUN pip install --no-cache-dir -r requirements.txt

# Скопіюємо код у контейнер
COPY rozetka_notebooks_scraper.py .

# Команда за замовчуванням
ENTRYPOINT ["python", "rozetka_notebooks_scraper.py"]
