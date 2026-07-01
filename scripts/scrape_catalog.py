import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")

CDX_API = "http://web.archive.org/cdx/search/cdx"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get_all_catalog_urls():
    """Pulls every archived SHL product-catalog 'view' URL from the Wayback Machine."""
    patterns = [
        "shl.com/solutions/products/product-catalog/view/*",
        "shl.com/products/product-catalog/view/*",
    ]
    urls = set()
    for pattern in patterns:
        params = {
            "url": pattern,
            "output": "text",
            "fl": "original",
            "collapse": "urlkey",
            "limit": "3000",
        }
        resp = requests.get(CDX_API, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            line = line.strip()
            if line:
                # normalize to https, no trailing junk
                clean = line.replace("http://", "https://").split(" ")[0]
                urls.add(clean.rstrip("/") + "/")
    return sorted(urls)

def slug_to_name(url):
    """Converts URL slug to readable assessment name."""
    slug = url.rstrip("/").split("/")[-1]
    name = slug.replace("-", " ").title()
    name = name.replace(" New", " (New)").replace(" R1", " (R1)").replace(" R2", " (R2)")
    return name


def scrape_detail_page(url):
    """Extracts assessment info - name from URL slug, description from page if possible."""
    name = slug_to_name(url)
    if not name:
        return None

    description = ""
    duration = ""
    test_type = ""

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            body_text = soup.get_text(" ", strip=True)

            # Duration
            match = re.search(r"(\d+)\s*minutes", body_text, re.IGNORECASE)
            if match:
                duration = f"{match.group(1)} minutes"

            # Description - skip browser warning lines, find first real sentence
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if len(text) > 40 and "browser" not in text.lower() and "cookie" not in text.lower():
                    description = text
                    break

            # Test type from meta or body keywords
            if "personality" in body_text.lower() or "opq" in body_text.lower():
                test_type = "P"
            elif "ability" in body_text.lower() or "reasoning" in body_text.lower() or "numerical" in body_text.lower() or "verbal" in body_text.lower():
                test_type = "A"
            elif "knowledge" in body_text.lower() or "multi-choice" in body_text.lower() or "technical" in body_text.lower():
                test_type = "K"
            elif "simulation" in body_text.lower() or "coding" in body_text.lower():
                test_type = "S"
            elif "behavior" in body_text.lower() or "situational" in body_text.lower() or "judgment" in body_text.lower():
                test_type = "B"
            elif "motivation" in body_text.lower():
                test_type = "P"
            elif "360" in name or "feedback" in name.lower():
                test_type = "D"

    except Exception as e:
        print(f"  warn: {url} -> {e}")

    return {
        "name": name,
        "url": url,
        "description": description,
        "duration": duration,
        "test_type": test_type,
    }

def main():
    print("Fetching catalog URL list from Wayback Machine CDX API...")
    urls = get_all_catalog_urls()
    print(f"Found {len(urls)} unique catalog URLs.")

    catalog = []
    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] {url}")
        item = scrape_detail_page(url)
        if item:
            catalog.append(item)
        time.sleep(0.3)  # be polite to SHL's servers

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(catalog)} items to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()