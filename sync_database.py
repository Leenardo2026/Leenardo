#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Database Synchronization Tool
---------------------------------
Enforces articles.json as the SINGLE CANONICAL SOURCE OF TRUTH.
Generates articles-data.js solely as a lightweight runtime representation
enabling 100% offline, zero-CORS file:// protocol execution.
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_JSON = BASE_DIR / "articles.json"
ARTICLES_DATA_JS = BASE_DIR / "articles-data.js"

def sync_database():
    if not ARTICLES_JSON.exists():
        print(f"Error: {ARTICLES_JSON} does not exist.")
        return False

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Serialize to compact JS variable (defining both ARTICLES_DATA and articlesDatabase for complete compatibility)
    json_str = json.dumps(data, ensure_ascii=False)
    js_content = f"/* Auto-generated from canonical articles.json. Do not edit directly. */\nwindow.ARTICLES_DATA = {json_str};\nwindow.articlesDatabase = window.ARTICLES_DATA;\n"

    with open(ARTICLES_DATA_JS, "w", encoding="utf-8") as f:
        f.write(js_content)

    print(f"✓ Synchronized {len(data)} articles from canonical {ARTICLES_JSON.name} -> runtime {ARTICLES_DATA_JS.name} ({ARTICLES_DATA_JS.stat().st_size:,} bytes).")

    # Automatically generate SEO static pages, sitemap.xml, robots.txt, and redirects
    try:
        from build_seo import generate_seo
        generate_seo()
    except Exception as e:
        print(f"⚠️ Warning: generate_seo failed: {e}")

    return True

if __name__ == "__main__":
    success = sync_database()
    sys.exit(0 if success else 1)
