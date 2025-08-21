#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rozetka Notebooks Scraper
-------------------------
Парсить всі сторінки каталогу ноутбуків на Rozetka та зберігає CSV
з полями: link, name, price, price_discount.

✅ Обмеження з ТЗ:
- Використовую тільки стандартні модулі Python для мережі/IO/логіки.
- Для HTML використовую одну зовнішню бібліотеку: beautifulsoup4 (bs4).

Анти‑бот тактика:
- Випадковий User‑Agent та затримки між запитами.
- Повторні спроби із експоненційним backoff.
- Опціональна ротація проксі (HTTP/HTTPS/SOCKS — якщо налаштовано системно).

Запуск:
    python rozetka_notebooks_scraper.py \
        --out notebooks.csv \
        --min-delay 2.0 \
        --max-delay 5.0 \
        --max-retries 5 \
        --start-page 1

Порада: якщо з'являються 429/403 — збільшіть затримки, зменшіть швидкість,
        або використайте проксі (див. --proxy-file).
"""
import csv
import random
import re
import sys
import time
import argparse
import json
from pathlib import Path
from typing import Iterable, Optional, Tuple, Dict, Any, List
from urllib.parse import urlparse, urlunparse, urlencode, parse_qsl
from urllib.request import Request, urlopen, build_opener, ProxyHandler
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup

CATALOG_URL = "https://rozetka.com.ua/ua/notebooks/c80004/"

USER_AGENTS = [
    # A small rotating pool; feel free to extend
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

HEADERS_BASE = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

PRICE_NUM_RE = re.compile(r"[\d\s]+")

def rand_ua() -> str:
    return random.choice(USER_AGENTS)

def smart_delay(min_delay: float, max_delay: float):
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)

def with_query(url: str, **params) -> str:
    """
    Append or replace query params in URL.
    """
    parts = list(urlparse(url))
    q = dict(parse_qsl(parts[4], keep_blank_values=True))
    q.update({k: v for k, v in params.items() if v is not None})
    parts[4] = urlencode(q, doseq=True)
    return urlunparse(parts)

def make_opener(proxy: Optional[str] = None):
    if proxy:
        return build_opener(ProxyHandler({
            "http": proxy,
            "https": proxy,
        }))
    return build_opener()

def fetch(url: str, opener, timeout: float, max_retries: int, backoff_base: float,
          min_delay: float, max_delay: float) -> bytes:
    """
    Fetch with retries, UA rotation and polite delays.
    """
    attempt = 0
    while True:
        smart_delay(min_delay, max_delay)
        headers = dict(HEADERS_BASE)
        headers["User-Agent"] = rand_ua()
        req = Request(url, headers=headers, method="GET")
        try:
            with opener.open(req, timeout=timeout) as resp:
                if resp.status >= 400:
                    raise HTTPError(url, resp.status, "HTTP error", resp.headers, None)
                return resp.read()
        except HTTPError as e:
            # If 404 or no products => bubble up for graceful stop;
            # If 429/403 — backoff harder
            if e.code in (404,):
                raise
            attempt += 1
            if attempt > max_retries:
                raise
            sleep_for = (backoff_base ** attempt) + random.uniform(0, 1.0)
            # be extra gentle on 429/403
            if e.code in (429, 403):
                sleep_for *= 2.5
            time.sleep(sleep_for)
        except URLError as e:
            attempt += 1
            if attempt > max_retries:
                raise
            sleep_for = (backoff_base ** attempt) + random.uniform(0, 1.0)
            time.sleep(sleep_for)

def extract_price(text: Optional[str]) -> Optional[int]:
    if not text:
        return None
    m = PRICE_NUM_RE.search(text)
    if not m:
        return None
    # Remove spaces and convert to int
    try:
        return int(m.group(0).replace(" ", ""))
    except ValueError:
        return None

def parse_products(html: bytes) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")

    # Rozetka cards often have classes like 'goods-tile' or 'catalog-grid__cell'.
    # We'll try a few selectors to be robust.
    cards = soup.select(".goods-tile") or soup.select("[data-goods-id] .goods-tile") or []

    results = []
    for card in cards:
        # Title + link
        a = card.select_one(".goods-tile__title a, a.goods-tile__heading, a.goods-tile__title")
        if not a:
            a = card.select_one("a.goods-tile__picture")
        name = (a.get_text(strip=True) if a else None) or (card.get("data-name") if card else None)
        link = (a.get("href") if a and a.has_attr("href") else None)
        # Normalize absolute links if needed
        if link and link.startswith("//"):
            link = "https:" + link

        # Current (actual/discounted) price
        cur_price_el = (
            card.select_one(".goods-tile__price-value") or
            card.select_one(".goods-tile__price .price__digits") or
            card.select_one("[data-testid='price']")
        )
        cur_price = extract_price(cur_price_el.get_text(strip=True) if cur_price_el else None)

        # Old (pre-discount) price — a few class variants seen on Rozetka
        old_price_el = (
            card.select_one(".goods-tile__price--old .goods-tile__price-value") or
            card.select_one(".goods-tile__old-price .goods-tile__price-value") or
            card.select_one(".goods-tile__price_old .goods-tile__price-value") or
            card.select_one(".goods-tile__price--old") or
            card.select_one(".old-price")
        )
        old_price = extract_price(old_price_el.get_text(strip=True) if old_price_el else None)

        # Map to requested columns:
        #   price            — базова ціна (до знижки) якщо є, інакше поточна
        #   price_discount   — ціна зі знижкою (поточна), якщо є знижка
        price = old_price if old_price else cur_price
        price_discount = cur_price if old_price else None

        if link and name and (price or price_discount):
            results.append({
                "link": link,
                "name": name,
                "price": price if price is not None else "",
                "price_discount": price_discount if price_discount is not None else "",
            })

    return results

def next_page_url(base_url: str, page: int) -> str:
    # Rozetka розуміє ?page=N
    return with_query(base_url, page=page)

def read_proxies(file_path: Optional[str]) -> List[str]:
    if not file_path:
        return []
    p = Path(file_path)
    if not p.exists():
        print(f"[WARN] Proxy file not found: {p}", file=sys.stderr)
        return []
    proxies = []
    if p.suffix.lower() in (".txt",):
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            proxies.append(line)
    elif p.suffix.lower() in (".json",):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, list):
                proxies = [str(x) for x in data]
        except Exception as e:
            print(f"[WARN] Can't parse JSON proxies: {e}", file=sys.stderr)
    return proxies

def rotate_proxy(proxies: List[str], idx: int) -> Optional[str]:
    if not proxies:
        return None
    return proxies[idx % len(proxies)]

def crawl(out_path: str,
          min_delay: float,
          max_delay: float,
          max_retries: int,
          timeout: float,
          backoff_base: float,
          start_page: int,
          max_pages: Optional[int],
          proxy_file: Optional[str]) -> int:
    """
    Returns number of rows written.
    """
    proxies = read_proxies(proxy_file)
    proxy_idx = 0

    rows_written = 0
    seen_links = set()

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["link", "name", "price", "price_discount"])
        writer.writeheader()

        page = start_page
        pages_done = 0

        while True:
            if max_pages is not None and pages_done >= max_pages:
                break

            url = next_page_url(CATALOG_URL, page=page)
            proxy = rotate_proxy(proxies, proxy_idx) if proxies else None
            opener = make_opener(proxy)

            try:
                html = fetch(url, opener=opener, timeout=timeout, max_retries=max_retries,
                             backoff_base=backoff_base, min_delay=min_delay, max_delay=max_delay)
            except HTTPError as e:
                # 404 or persistent error — stop
                print(f"[INFO] Stopping at page {page}: HTTP {e.code}", file=sys.stderr)
                break
            except URLError as e:
                print(f"[WARN] Network error at page {page}: {e}", file=sys.stderr)
                break

            products = parse_products(html)
            if not products:
                print(f"[INFO] No products found on page {page}. Stopping.", file=sys.stderr)
                break

            added = 0
            for item in products:
                if item["link"] in seen_links:
                    continue
                writer.writerow(item)
                seen_links.add(item["link"])
                added += 1

            rows_written += added
            pages_done += 1
            page += 1
            proxy_idx += 1  # rotate proxy each page

            print(f"[OK] Page {page-1}: +{added} items (total {rows_written}).", file=sys.stderr)

    return rows_written

def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Rozetka notebooks scraper → CSV")
    ap.add_argument("--out", default="notebooks.csv", help="Шлях до CSV файлу (default: notebooks.csv)")
    ap.add_argument("--min-delay", type=float, default=2.0, help="Мінімальна затримка між запитами, сек (default: 2.0)")
    ap.add_argument("--max-delay", type=float, default=5.0, help="Максимальна затримка між запитами, сек (default: 5.0)")
    ap.add_argument("--max-retries", type=int, default=5, help="Максимум повторних спроб для одного запиту (default: 5)")
    ap.add_argument("--timeout", type=float, default=30.0, help="Таймаут запиту, сек (default: 30)")
    ap.add_argument("--backoff-base", type=float, default=1.8, help="Основа експоненційного backoff (default: 1.8)")
    ap.add_argument("--start-page", type=int, default=1, help="З якої сторінки починати (default: 1)")
    ap.add_argument("--max-pages", type=int, default=None, help="Максимальна кількість сторінок для обходу (default: всі)")
    ap.add_argument("--proxy-file", type=str, default=None, help="Файл із списком проксі (.txt або .json), напр.: http://user:pass@host:port")
    args = ap.parse_args(argv)

    # sanity
    if args.max_delay < args.min_delay:
        args.max_delay = args.min_delay

    total = crawl(out_path=args.out,
                  min_delay=args.min_delay,
                  max_delay=args.max_delay,
                  max_retries=args.max_retries,
                  timeout=args.timeout,
                  backoff_base=args.backoff_base,
                  start_page=args.start_page,
                  max_pages=args.max_pages,
                  proxy_file=args.proxy_file)

    print(f"Done. Wrote {total} rows to {args.out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
