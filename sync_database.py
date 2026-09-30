#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Database Synchronization Tool
---------------------------------
Enforces articles.json as the SINGLE CANONICAL SOURCE OF TRUTH.
Generates:
1. articles-data.js: Full runtime representation for article.html and articles/*.html (with full token glosses).
2. articles-summary.js & articles-summary.json: Lightweight representation for index.html (homepage metadata and excerpts, stripping heavy tokens).
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_JSON = BASE_DIR / "articles.json"
ARTICLES_DATA_JS = BASE_DIR / "articles-data.js"
ARTICLES_SUMMARY_JS = BASE_DIR / "articles-summary.js"
ARTICLES_SUMMARY_JSON = BASE_DIR / "articles-summary.json"

def build_summary(articles):
    summary = []
    for art in articles:
        item = {k: v for k, v in art.items() if k != "languages"}
        item["languages"] = {}
        for lang, levels in art.get("languages", {}).items():
            item["languages"][lang] = {}
            for lvl, data in levels.items():
                lvl_item = {
                    "title": data.get("title", ""),
                    "grammarDesc": data.get("grammarDesc", ""),
                }
                # Keep first paragraph sentences (target text only) for homepage excerpt generation
                paras = data.get("paragraphs", [])
                if paras and isinstance(paras[0], list):
                    lvl_item["paragraphs"] = [
                        [{"target": s.get("target", "")} for s in paras[0] if isinstance(s, dict)]
                    ]
                item["languages"][lang][lvl] = lvl_item
        summary.append(item)
    return summary

def sync_database():
    if not ARTICLES_JSON.exists():
        print(f"Error: {ARTICLES_JSON} does not exist.")
        return False

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Full runtime artifact for article reading pages (articles-data.js)
    json_str_full = json.dumps(data, ensure_ascii=False)
    js_content_full = (
        "/* Auto-generated from canonical articles.json. Do not edit directly. */\n"
        f"window.ARTICLES_DATA = {json_str_full};\n"
        "window.articlesDatabase = window.ARTICLES_DATA;\n"
    )
    with open(ARTICLES_DATA_JS, "w", encoding="utf-8") as f:
        f.write(js_content_full)

    # 2. Lightweight summary artifact for homepage (articles-summary.js & articles-summary.json)
    summary_data = build_summary(data)
    json_str_summary = json.dumps(summary_data, ensure_ascii=False)
    js_content_summary = (
        "/* Auto-generated summary from canonical articles.json for lightweight homepage. Do not edit directly. */\n"
        f"window.ARTICLES_SUMMARY = {json_str_summary};\n"
        "window.ARTICLES_DATA = window.ARTICLES_SUMMARY;\n"
        "window.articlesDatabase = window.ARTICLES_SUMMARY;\n"
    )
    with open(ARTICLES_SUMMARY_JS, "w", encoding="utf-8") as f:
        f.write(js_content_summary)

    with open(ARTICLES_SUMMARY_JSON, "w", encoding="utf-8") as f:
        f.write(json_str_summary)

    print(f"✓ Synchronized {len(data)} articles:")
    print(f"  - Canonical source:     {ARTICLES_JSON.name} ({ARTICLES_JSON.stat().st_size:,} bytes)")
    print(f"  - Reading runtime:      {ARTICLES_DATA_JS.name} ({ARTICLES_DATA_JS.stat().st_size:,} bytes)")
    print(f"  - Homepage summary JS:  {ARTICLES_SUMMARY_JS.name} ({ARTICLES_SUMMARY_JS.stat().st_size:,} bytes)")
    print(f"  - Homepage summary JSON:{ARTICLES_SUMMARY_JSON.name} ({ARTICLES_SUMMARY_JSON.stat().st_size:,} bytes)")
    return True

if __name__ == "__main__":
    success = sync_database()
    sys.exit(0 if success else 1)

