#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import csv
import random
import time
from bs4 import BeautifulSoup

URL = "https://rozetka.com.ua/ua/notebooks/c80004/page={}"

OUTPUT_FILE = "notebooks.csv"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/124.0"
]

def get_html(url):
    """Завантажити html з випадком агентом і затримкою"""
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    time.sleep(random.uniform(2, 5))
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def parse_page(html):
    """"Парсинг сторінки і збір товарів"""
    soup = BeautifulSoup(html, "html.parser")
    products = []

    cards = soup.select(".goods-tile")
    for card in cards:
        # Назва
        name_tag = card.select_one(".goods-tile__title")
        name = name_tag.get_text(strip=True) if name_tag else "—"

        # Ціна
        price_tag = card.select_one(".goods-tile__price-value")
        price = price_tag.get_text(strip=True).replace("\u202f", "") if price_tag else "—"

        # Посилання
        link_tag = card.select_one("a.goods-tile__heading")
        link = link_tag["href"] if link_tag else "—"

        products.append([name, price, link])

    return products

def save_to_csv(products, filename):
    """Зберігаємо список товарів у CSV"""
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Назва", "Ціна", "Посилання"])  # заголовки
        writer.writerows(products)

def main():
    all_products = []
    for page in range(1, 3):  # поки спробуємо лише 2 сторінки
        print(f"Парсимо сторінку {page}...")
        html = get_html(URL.format(page))
        products = parse_page(html)
        if not products:
            print("Більше товарів немає, зупиняємось.")
            break
        all_products.extend(products)

    save_to_csv(all_products, OUTPUT_FILE)
    print(f"✅ Готово! Збережено {len(all_products)} товарів у {OUTPUT_FILE}")

if __name__ == "__main__":
    main()