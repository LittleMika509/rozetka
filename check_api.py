import requests

url = "https://xl-catalog-api.rozetka.com.ua/v4/goods/get"
params = {
    "front-type": "xl",
    "category_id": 80004,
    "page": 1,
    "lang": "ua"
}

r = requests.get(url, params=params)
print("Status:", r.status_code)
print("Text (first 500 chars):", r.text[:500])
