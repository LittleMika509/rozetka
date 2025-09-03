# Rozetka Notebooks Scraper + API

Цей проєкт сладається з:
- `app.py` - Flask API для перегляду ноутбуків у базі (невеликий сервер, який віддає дані з бази у JSON) (`/`, `/notebooks`)
- `/` - перевірка чи працює сервер
- `/notebooks`- список ноутбуків із бази
- `rozetka_notebooks_scraper.py` - парсер ноутбуків з Rozetka у CSV та SQLite

----

# Збірка Docker образу

У директорії з `Dockerfile` виконати:

```bash
docker build -t rozetka-scraper .