import json
import os
from rapidfuzz import fuzz

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")
_catalog_cache = None

def load_catalog():
    global _catalog_cache
    if _catalog_cache is None:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            _catalog_cache = json.load(f)
    return _catalog_cache

def search_catalog(query: str, k: int = 12):
    catalog = load_catalog()
    if not query.strip():
        return []
    
    scored = []
    q = query.lower()
    for item in catalog:
        text = f"{item.get('name','')} {item.get('description','')}".lower()
        score = fuzz.token_set_ratio(q, text)
        if score > 28:
            scored.append((score, item))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:k]]

def get_item_by_name(name: str):
    catalog = load_catalog()
    for item in catalog:
        if name.lower() in item.get("name", "").lower():
            return item
    return None