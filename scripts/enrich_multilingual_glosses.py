#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enriches token glosses in articles.json with real multilingual translations.
Fixes the fallback issue where non-lexicon tokens defaulted to their source form.
Populates real translations for support languages (tr, es, de, fr, en).
"""

import json
import os
import sys
import re
import urllib.request
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor

CACHE_FILE = os.path.join(os.path.dirname(__file__), "translation_cache.json")


def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Warning: could not save cache: {e}")


def fetch_translation(word, src_lang, tgt_lang):
    if not word or len(word.strip()) == 0:
        return ""
    w = word.strip()
    # Punctuation check
    if re.match(r"^[^\w]+$", w):
        return w

    url = f"https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl={src_lang}&tl={tgt_lang}&q={urllib.parse.quote(w)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                res = data[0] if isinstance(data[0], str) else (data[0][0] if isinstance(data[0], list) and len(data[0]) > 0 else "")
                if res and res.strip().lower() != w.lower():
                    return res.strip()
    except Exception:
        pass

    return ""


def enrich_articles(articles_path="articles.json", target_languages=None, max_workers=25):
    if target_languages is None:
        target_languages = ["en"]
    print(f"Reading {articles_path} for source languages: {target_languages}...")
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    cache = load_cache()
    print(f"Loaded {len(cache)} cached word translations.")

    # 1. Collect words needing translation
    needed = set() # (word_clean, src_lang, tgt_lang)

    for art in articles:
        languages = art.get("languages", {})
        for src_lang in target_languages:
            src_data = languages.get(src_lang, {})
            for lvl, lvl_data in src_data.items():
                for p in lvl_data.get("paragraphs", []):
                    for s in p:
                        for tok in s.get("tokens", []):
                            raw_tok = tok.get("token", "").strip()
                            clean_tok = re.sub(r"[^\w'-]", "", raw_tok, flags=re.UNICODE).strip()
                            if not clean_tok or len(clean_tok) <= 1:
                                continue

                            gloss = tok.get("gloss", {})
                            tr_val = gloss.get("tr", "")
                            if not tr_val or tr_val.strip().lower() == clean_tok.lower():
                                cache_key = f"{src_lang}_tr_{clean_tok.lower()}"
                                if cache_key not in cache:
                                    needed.add((clean_tok, src_lang, "tr"))

    print(f"Found {len(needed)} unique word queries to fetch for {target_languages}.")

    if needed:
        completed = 0
        total = len(needed)

        def worker(item):
            w, s_lang, t_lang = item
            k = f"{s_lang}_{t_lang}_{w.lower()}"
            if k in cache:
                return k, cache[k]
            trans = fetch_translation(w, s_lang, t_lang)
            return k, trans

        print(f"Translating in parallel with {max_workers} workers...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for k, trans in executor.map(worker, needed):
                if trans:
                    cache[k] = trans
                completed += 1
                if completed % 100 == 0 or completed == total:
                    print(f"  Progress: {completed}/{total} ({completed/total*100:.1f}%)")
                    save_cache(cache)

        save_cache(cache)
        print("✓ All translations fetched and cached.")

    # 2. Apply enriched translations back to articles.json
    updated_tokens = 0
    for art in articles:
        languages = art.get("languages", {})
        for src_lang in target_languages:
            src_data = languages.get(src_lang, {})
            for lvl, lvl_data in src_data.items():
                for p in lvl_data.get("paragraphs", []):
                    for s in p:
                        for tok in s.get("tokens", []):
                            raw_tok = tok.get("token", "").strip()
                            clean_tok = re.sub(r"[^\w'-]", "", raw_tok, flags=re.UNICODE).strip()
                            if not clean_tok:
                                continue

                            gloss = tok.get("gloss", {})
                            tr_val = gloss.get("tr", "")

                            if not tr_val or tr_val.strip().lower() == clean_tok.lower():
                                cache_key = f"{src_lang}_tr_{clean_tok.lower()}"
                                if cache_key in cache and cache[cache_key]:
                                    gloss["tr"] = cache[cache_key]
                                    tok["gloss"] = gloss
                                    updated_tokens += 1

    print(f"Updated {updated_tokens} tokens with genuine Turkish translations!")

    print(f"Writing updated database to {articles_path}...")
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("✓ Successfully saved articles.json")


if __name__ == "__main__":
    langs = sys.argv[1].split(",") if len(sys.argv) > 1 else ["en"]
    enrich_articles("articles.json", target_languages=langs, max_workers=25)
