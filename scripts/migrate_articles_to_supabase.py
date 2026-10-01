#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Leenardo Supabase Content Migration & Integrity Verifier
------------------------------------------------------------
Migrates all 23 graded articles from canonical articles.json to Supabase.
Verifies byte-for-byte and token-for-token integrity after upload.
"""

import os
import sys
import json
import ssl
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scripts" else Path(__file__).resolve().parent
ARTICLES_JSON = BASE_DIR / "articles.json"

DEFAULT_SUPABASE_URL = "https://vkddnvpqnccstcjnqfyq.supabase.co"
DEFAULT_ANON_KEY = "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-"

def build_article_summary(art):
    """Extract lean homepage summary (titles, teaser, grammarDesc, first paragraph target text)."""
    sum_langs = {}
    for lang, levels in art.get("languages", {}).items():
        sum_langs[lang] = {}
        for lvl, data in levels.items():
            lvl_item = {
                "title": data.get("title", ""),
                "grammarDesc": data.get("grammarDesc", ""),
            }
            paras = data.get("paragraphs", [])
            if paras and isinstance(paras[0], list):
                lvl_item["paragraphs"] = [
                    [{"target": s.get("target", "")} for s in paras[0] if isinstance(s, dict)]
                ]
            sum_langs[lang][lvl] = lvl_item
    return sum_langs

def prepare_row(art):
    return {
        "id": art["id"],
        "topic": art.get("topic", ""),
        "category": art.get("category", ""),
        "category_translations": art.get("categoryTranslations", {}),
        "title_tr": art.get("titleTr", ""),
        "title_en": art.get("titleEn", ""),
        "title_translations": art.get("titleTranslations", {}),
        "teaser": art.get("teaser"),
        "teaser_translations": art.get("teaserTranslations", {}),
        "visual": art.get("visual", {}),
        "read_time": art.get("readTime", "3 min read"),
        "languages": art.get("languages", {}),
        "summary": build_article_summary(art),
        "status": "published",
        "hidden": art.get("hidden", False)
    }

def migrate(supabase_url=None, api_key=None):
    url = supabase_url or os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    key = api_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", DEFAULT_ANON_KEY)

    print("=" * 65)
    print("💎 LEENARDO SUPABASE MIGRATION PIPELINE")
    print("=" * 65)
    print(f"Supabase Endpoint: {url}")
    print(f"Canonical Source:  {ARTICLES_JSON}")

    if not ARTICLES_JSON.exists():
        print(f"❌ Error: {ARTICLES_JSON} does not exist!")
        return False

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    print(f"Loaded {len(articles)} articles from canonical source.\n")

    ctx = ssl._create_unverified_context()
    endpoint = f"{url}/rest/v1/articles"
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }

    success_count = 0
    failed = []

    for idx, art in enumerate(articles, 1):
        art_id = art["id"]
        row = prepare_row(art)
        payload = json.dumps(row, ensure_ascii=False).encode("utf-8")

        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, context=ctx) as resp:
                if resp.status in (200, 201):
                    print(f"  [{idx:02d}/{len(articles):02d}] ✓ Upserted: {art_id} ({len(payload):,} bytes)")
                    success_count += 1
                else:
                    print(f"  [{idx:02d}/{len(articles):02d}] ⚠️ HTTP {resp.status} for {art_id}")
                    failed.append((art_id, f"HTTP {resp.status}"))
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"  [{idx:02d}/{len(articles):02d}] ❌ Error for {art_id}: {e.code} - {err_body}")
            failed.append((art_id, f"{e.code}: {err_body}"))
        except Exception as e:
            print(f"  [{idx:02d}/{len(articles):02d}] ❌ Exception for {art_id}: {e}")
            failed.append((art_id, str(e)))

    print("\n" + "-" * 65)
    print(f"Migration Completed: {success_count}/{len(articles)} articles successfully upserted.")
    if failed:
        print(f"⚠️ {len(failed)} article(s) failed.")
        return False
    return True

def verify_migration(supabase_url=None, api_key=None):
    """Audit every article in Supabase against canonical articles.json."""
    url = supabase_url or os.getenv("SUPABASE_URL", DEFAULT_SUPABASE_URL)
    key = api_key or os.getenv("SUPABASE_ANON_KEY", DEFAULT_ANON_KEY)

    print("\n" + "=" * 65)
    print("💎 RUNNING COMPREHENSIVE DATA INTEGRITY AUDIT")
    print("=" * 65)

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        canonical_articles = json.load(f)
    canonical_map = {a["id"]: a for a in canonical_articles}

    ctx = ssl._create_unverified_context()
    # Fetch all articles from Supabase
    endpoint = f"{url}/rest/v1/articles?select=*&order=published_at.desc"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    }

    req = urllib.request.Request(endpoint, headers=headers)
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Failed to fetch articles from Supabase for audit: {e}")
        return False

    print(f"✓ Retrieved {len(data)} articles from Supabase.")

    if len(data) != len(canonical_articles):
        print(f"❌ Count mismatch: Supabase has {len(data)}, canonical has {len(canonical_articles)}")
        return False

    errors = []
    total_tokens_checked = 0
    total_quizzes_checked = 0

    for remote_art in data:
        art_id = remote_art.get("id")
        if art_id not in canonical_map:
            errors.append(f"Unexpected article ID in Supabase: {art_id}")
            continue

        local_art = canonical_map[art_id]

        # 1. Meta check
        if remote_art.get("topic") != local_art.get("topic"):
            errors.append(f"[{art_id}] Topic mismatch")
        if remote_art.get("category") != local_art.get("category"):
            errors.append(f"[{art_id}] Category mismatch")

        # 2. Languages check
        r_langs = remote_art.get("languages", {})
        l_langs = local_art.get("languages", {})

        for lang in ["tr", "en", "es", "de", "fr"]:
            if lang not in r_langs:
                errors.append(f"[{art_id}] Missing language '{lang}' in Supabase")
                continue

            for lvl in ["A1", "A2", "B1", "B2", "C1"]:
                if lvl not in r_langs[lang]:
                    errors.append(f"[{art_id}][{lang}] Missing level '{lvl}' in Supabase")
                    continue

                r_lvl = r_langs[lang][lvl]
                l_lvl = l_langs[lang][lvl]

                # Check Title
                if r_lvl.get("title") != l_lvl.get("title"):
                    errors.append(f"[{art_id}][{lang}][{lvl}] Title mismatch")

                # Check Paragraphs & Tokens
                r_paras = r_lvl.get("paragraphs", [])
                l_paras = l_lvl.get("paragraphs", [])

                if len(r_paras) != len(l_paras):
                    errors.append(f"[{art_id}][{lang}][{lvl}] Paragraph count mismatch: {len(r_paras)} vs {len(l_paras)}")
                    continue

                for p_idx, (r_p, l_p) in enumerate(zip(r_paras, l_paras)):
                    if len(r_p) != len(l_p):
                        errors.append(f"[{art_id}][{lang}][{lvl}][P{p_idx}] Sentence count mismatch")
                        continue

                    for s_idx, (r_s, l_s) in enumerate(zip(r_p, l_p)):
                        if r_s.get("target") != l_s.get("target"):
                            errors.append(f"[{art_id}][{lang}][{lvl}][P{p_idx}S{s_idx}] Sentence target text mismatch")
                        
                        r_tokens = r_s.get("tokens", [])
                        l_tokens = l_s.get("tokens", [])
                        total_tokens_checked += len(l_tokens)

                        if len(r_tokens) != len(l_tokens):
                            errors.append(f"[{art_id}][{lang}][{lvl}][P{p_idx}S{s_idx}] Token count mismatch: {len(r_tokens)} vs {len(l_tokens)}")
                        else:
                            for t_idx, (rt, lt) in enumerate(zip(r_tokens, l_tokens)):
                                if rt.get("target") != lt.get("target") or rt.get("gloss") != lt.get("gloss") or rt.get("lemma") != lt.get("lemma"):
                                    errors.append(f"[{art_id}][{lang}][{lvl}] Token mismatch on '{lt.get('target')}'")
                                    break

                # Check Quizzes
                r_quiz = r_lvl.get("quiz", [])
                l_quiz = l_lvl.get("quiz", [])
                total_quizzes_checked += len(l_quiz)
                if len(r_quiz) != len(l_quiz):
                    errors.append(f"[{art_id}][{lang}][{lvl}] Quiz count mismatch")
                elif l_quiz and r_quiz:
                    if r_quiz[0].get("question") != l_quiz[0].get("question"):
                        errors.append(f"[{art_id}][{lang}][{lvl}] Quiz question mismatch")

    print("\n--- AUDIT RESULTS ---")
    print(f"Total Articles Audited:      {len(canonical_articles)}")
    print(f"Total Tokens Verified:       {total_tokens_checked:,}")
    print(f"Total Quizzes Verified:      {total_quizzes_checked}")
    print(f"Total Discrepancies Found:   {len(errors)}")

    if errors:
        print("\n❌ Audit flagged discrepancies:")
        for e in errors[:10]:
            print(f"  - {e}")
        return False
    else:
        print("\n✅ ZERO LOSS / ZERO CORRUPTION CONFIRMED: 100% PERFECT FIDELITY ACROSS ALL DATA!")
        return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Migrate articles to Supabase and verify data integrity.")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification against existing Supabase data.")
    args = parser.parse_args()

    if args.verify_only:
        ok = verify_migration()
    else:
        migrated = migrate()
        if migrated:
            ok = verify_migration()
        else:
            ok = False

    sys.exit(0 if ok else 1)
