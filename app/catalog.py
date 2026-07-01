import json
import os
from rapidfuzz import fuzz

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")

_catalog_cache = None


def load_catalog():
    """Loads catalog.json once and caches it in memory."""
    global _catalog_cache
    if _catalog_cache is None:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            _catalog_cache = json.load(f)
    return _catalog_cache


def search_catalog(query: str, k: int = 10):
    """
    Returns top-k catalog items ranked by fuzzy text match
    against name + description + test_type fields.
    """
    catalog = load_catalog()
    if not query.strip():
        return []

    scored = []
    for item in catalog:
        searchable_text = f"{item.get('name', '')} {item.get('description', '')} {item.get('test_type_full', '')}"
        score = fuzz.token_set_ratio(query, searchable_text)
        if score > 0:
            scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:k] if score > 30]


def get_item_by_name(name: str):
    """Exact-ish lookup for compare functionality."""
    catalog = load_catalog()
    name_lower = name.lower().strip()
    for item in catalog:
        if name_lower in item.get("name", "").lower():
            return item
    return None