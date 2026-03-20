import re
import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "http://books.toscrape.com/"
CATALOGUE_URL = urljoin(BASE_URL, "catalogue/")
START_URL = urljoin(CATALOGUE_URL, "page-1.html")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def get_soup(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def rating_to_number(rating_class: str) -> int:
    mapping = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5
    }
    return mapping.get(rating_class, 0)


def parse_book_list_page(url: str) -> list[dict]:
    soup = get_soup(url)
    books = []

    articles = soup.select("article.product_pod")

    for article in articles:
        title_tag = article.select_one("h3 a")
        price_tag = article.select_one(".price_color")
        availability_tag = article.select_one(".availability")
        rating_tag = article.select_one("p.star-rating")

        relative_link = title_tag["href"]
        detail_url = urljoin(url, relative_link)

        title = title_tag["title"].strip()
        price = clean_text(price_tag.get_text()) if price_tag else ""
        availability = clean_text(availability_tag.get_text()) if availability_tag else ""

        rating = 0
        if rating_tag:
            classes = rating_tag.get("class", [])
            for cls in classes:
                if cls in ["One", "Two", "Three", "Four", "Five"]:
                    rating = rating_to_number(cls)
                    break

        books.append({
            "title": title,
            "price": price,
            "availability": availability,
            "rating": rating,
            "detail_url": detail_url
        })

    return books


def parse_book_detail(url: str) -> dict:
    soup = get_soup(url)

    product_main = soup.select_one(".product_main")
    title = ""
    price = ""
    availability = ""
    rating = 0

    if product_main:
        title_tag = product_main.select_one("h1")
        price_tag = product_main.select_one(".price_color")
        availability_tag = product_main.select_one(".availability")
        rating_tag = product_main.select_one("p.star-rating")

        title = clean_text(title_tag.get_text()) if title_tag else ""
        price = clean_text(price_tag.get_text()) if price_tag else ""
        availability = clean_text(availability_tag.get_text()) if availability_tag else ""

        if rating_tag:
            classes = rating_tag.get("class", [])
            for cls in classes:
                if cls in ["One", "Two", "Three", "Four", "Five"]:
                    rating = rating_to_number(cls)
                    break

    breadcrumb_links = soup.select("ul.breadcrumb li a")
    category = ""
    if len(breadcrumb_links) >= 3:
        category = clean_text(breadcrumb_links[2].get_text())

    description = ""
    desc_header = soup.find("div", id="product_description")
    if desc_header:
        desc_paragraph = desc_header.find_next_sibling("p")
        if desc_paragraph:
            description = clean_text(desc_paragraph.get_text())

    product_info = {
        "upc": "",
        "product_type": "",
        "price_excl_tax": "",
        "price_incl_tax": "",
        "tax": "",
        "num_reviews": ""
    }

    table = soup.select_one("table.table.table-striped")
    if table:
        rows = table.select("tr")
        for row in rows:
            th = row.select_one("th")
            td = row.select_one("td")
            if not th or not td:
                continue

            key = clean_text(th.get_text()).lower()
            value = clean_text(td.get_text())

            if key == "upc":
                product_info["upc"] = value
            elif key == "product type":
                product_info["product_type"] = value
            elif key == "price (excl. tax)":
                product_info["price_excl_tax"] = value
            elif key == "price (incl. tax)":
                product_info["price_incl_tax"] = value
            elif key == "tax":
                product_info["tax"] = value
            elif key == "number of reviews":
                product_info["num_reviews"] = value

    return {
        "title": title,
        "category": category,
        "price": price,
        "availability": availability,
        "rating": rating,
        "description": description,
        "upc": product_info["upc"],
        "product_type": product_info["product_type"],
        "price_excl_tax": product_info["price_excl_tax"],
        "price_incl_tax": product_info["price_incl_tax"],
        "tax": product_info["tax"],
        "num_reviews": product_info["num_reviews"],
        "detail_url": url
    }


def get_all_catalogue_pages() -> list[str]:
    page_urls = []
    page_number = 1

    while True:
        page_url = urljoin(CATALOGUE_URL, f"page-{page_number}.html")

        try:
            response = requests.get(page_url, headers=HEADERS, timeout=30)
            if response.status_code != 200:
                break
            page_urls.append(page_url)
            print(f"Found catalogue page: {page_url}")
            page_number += 1
        except requests.RequestException:
            break

    return page_urls


def scrape_all_books() -> pd.DataFrame:
    all_rows = []

    page_urls = get_all_catalogue_pages()
    print(f"\nTotal catalogue pages found: {len(page_urls)}\n")

    for page_index, page_url in enumerate(page_urls, start=1):
        print(f"Scraping list page {page_index}/{len(page_urls)}: {page_url}")
        books_on_page = parse_book_list_page(page_url)

        for book_index, book in enumerate(books_on_page, start=1):
            try:
                print(f"  Scraping detail {book_index}/{len(books_on_page)}: {book['title']}")
                detail_data = parse_book_detail(book["detail_url"])
                all_rows.append(detail_data)
                time.sleep(0.2)
            except Exception as e:
                print(f"  Error scraping {book['detail_url']}: {e}")

    df = pd.DataFrame(all_rows)
    return df


def main():
    df = scrape_all_books()
    df.to_csv("books_to_scrape.csv", index=False, encoding="utf-8")
    print("\nSaved file: books_to_scrape.csv")
    print(f"Total books scraped: {len(df)}")


if __name__ == "__main__":
    main()