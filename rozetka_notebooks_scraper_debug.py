import requests
from bs4 import BeautifulSoup
import csv
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Cookie": (
        "SAPISID=-3EFsY_eU3RQCJye/AjctAPASwGMuub2Uw;"
        "SEARCH_SAMESITE=CgQI0Z0B;"
        "SID=g.a0000QhYdd02rIdfm0dbump4gZEPg8byi0VjNti6rqDFoIRnycHZNdeNU4w1KgtJTo-vHZHyWQACgYKARgSARcSFQHGX2MigeaJuMf3_rOt4vavV8HuOxoVAUF8yKptcPyeqIyP5C_-0Eee2qlr0076;"
        "SIDCC=AKEyXzWXtEsIC7zu6EjNFMJ7QwH2L67X0fLcIYSoICDi7kj5xWiAnLoFBMS31SXyHMxYiI2b8bo;"
        "slang=ua;"
        "social-auth=new;"
        "SSID=ACqLvhOg2tLRshUoh;"
        "SSID=ALOTTUiGj0SYEbh2H;"
        "t_gid=4bb87e9b-37f1-4074-8c2c-f498fcdd92b5-tuctebf9e22;"
        "t_pt_gid=4bb87e9b-37f1-4074-8c2c-f498fcdd92b5-tuctebf9e22;"
        "tmruid=Cgo9D2inZH6bfVOCN%2BEpAg;"
        "ts=1755800708;"
        "ttcsid=1755800707756::GyaENT42zEtCgwJ-ALek.1.1755802308284;"
        "uid=0d53de4d-1a3b-4cd7-aff1-d6706a72fd41;"
        "ussapp=zn6wMbh7yuoJ4LnQ0PZnPEvukoR2WdVAqOFqu8QR;"
        "uuid=17558007099102745175;"
        "vid=7618669821620569;"
        "xab_segment=24;"
        "xl_uid=Cgo8MminZH2ad3gsLFiIAg==;"
        "_gid=GA1.3.307964995.1755800706;"
        "_hjSession_3494164=eyJpZCI6IjYxNTI2MzM2LTRjY2ItNDM5Mi05MDE5LTEzYzc1YWQyYzQzMCIsImMiOjE3NTU4MDA3MDYxOTAsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxLCJzcCI6MH0=;"
        "_hjSessionUser_3494164=eyJpZCI6Ijc4MmVhMjkzLWZiNDAtNWRmNi05OTE5LTRhZTA1Y2VkMDA0NSIsImNyZWF0ZWQiOjE3NTU4MDA3MDYxODksImV4aXN0aW5nIjp0cnVlfQ==;"
        "_tt_enable_cookie=1;"
        "_ttp=01K36Y18MVGF3XFTRFRXQNB1TA_.tt.2;"
        "_uss-csrf=0ywpi/iuHEBHY6KAt1uD1OrMUhbQohW5o7j+l8rA7VQ8LBz8;"
        "ACCOUNT_CHOOSER=AFx_qI5P_G8lziLKaSJ0v-fU2bwnhCMVZtjMkxV5rlZ2keJyiaQp9Io9MiLzLkanzpkrlz2elwf9DSmIYMP_dj9Pv05X2UEaBnGdhMPJb8Yzws3e_4Tzu6WCLh9eUbyVN3iFVNMyNOYc;"
        "cf_clearance=HtvzeRnm5Ec0A2XommRZv3l1PTKp5zr0g7OFY4u0ftU-1755801831-1.2.1.1-OZvDNn8N2dkV2GiYFNnBTxnBj5SYq7H2hqcbvnv2WK67W4eYJFfLjHgU4fgbbTCVJtgXlSAIWl4CiLH6v2k_BzmygPl5RJzw_JR_D_tARzWazJZrqQnI6kNZZk6jPExIbnmFOFvJlYH04rfwo4SagafcGyHubSBnKnECBPs60wszZf6qk_rNMvjwy5RMpYSrRjSsR.8ZItCmXRZhDKhD6vH_1wrsJ6FEGxBmpaF2gts;"
    )
}

BASE_URL = "https://rozetka.com.ua/ua/notebooks/c80004/"

def parse_page(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Помилка {response.status_code} при зверненні до {url}")
        return [], None

    soup = BeautifulSoup(response.text, "lxml")
    
    products = []
    items = soup.select("div.goods-tile")
    for item in items:
        title_tag = item.select_one("a.goods-tile__heading")
        price_tag = item.select_one("span.goods-tile__price-value")
        if title_tag and price_tag:
            title = title_tag.text.strip()
            price = price_tag.text.strip().replace("\u2009", "")  # прибрати тонкий пробіл
            link = title_tag["href"]
            products.append({
                "title": title,
                "price": price,
                "link": link
            })

    # пагінація
    next_page_tag = soup.select_one("a.pagination__link.pagination__link_next")
    next_page_url = next_page_tag["href"] if next_page_tag else None

    return products, next_page_url

def scrape_rozetka():
    all_products = []
    url = BASE_URL
    while url:
        print(f"Парсинг сторінки: {url}")
        products, next_page_url = parse_page(url)
        all_products.extend(products)
        url = next_page_url
        time.sleep(1)  # щоб не блокували

    # запис у CSV
    with open("rozetka_notebooks.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "price", "link"])
        writer.writeheader()
        writer.writerows(all_products)
    
    print(f"Збережено {len(all_products)} товарів у rozetka_notebooks.csv")

if __name__ == "__main__":
    scrape_rozetka()
