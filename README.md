# Final Project

## Web Scraping with Python

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate      # Mac/Linux
.venv\Scripts\activate         # Windows
```

### 2. Install requirements

```bash
pip install -r requirements.txt
```

---

## Run the scraper

```bash
python3 scrape.py
```

---

## What this scraper does

This project scrapes data from the website **https://books.toscrape.com/**.

It automatically:

* navigates through all catalogue pages
* visits each book page
* extracts relevant information
* saves the data into a CSV file

---

## What we scrape

Each **book** is treated as a resource.

For every book, we collect:

* title
* category
* price (GBP)
* availability (number of books in stock)
* rating (1–5)
* description
* UPC (unique identifier)
* product type
* price excluding tax (GBP)
* price including tax (GBP)
* tax (GBP)
* number of reviews

---

## Output

The script generates:

```
books.csv
```

This dataset contains all scraped books and is ready for analysis.
