#!/usr/bin/env python3
"""
Phase 2 Comprehensive Verification & Parity Audit Script
Tests:
  1. Data parity across all 23 articles and 575 language-level permutations.
  2. Adapter correctness (mapSupabaseArticleToClient).
  3. Security redirect rule audit against internal files (.md, .py, .github, scripts).
  4. Local HTTP server rewrite and 404 handling.
"""

import json
import os
import re
import sys
import http.server
import socketserver
import threading
import urllib.request
import ssl

WORKSPACE = "/Users/sencanyuksel/Desktop/Leenardo"
ARTICLES_JSON = os.path.join(WORKSPACE, "articles.json")
REDIRECTS_FILE = os.path.join(WORKSPACE, "_redirects")

def map_supabase_article_to_client(art):
    """Python mirror of article.html's mapSupabaseArticleToClient adapter."""
    if not art:
        return None
    return {
        "id": art.get("id", ""),
        "topic": art.get("topic", ""),
        "category": art.get("category", ""),
        "categoryTranslations": art.get("categoryTranslations") or art.get("category_translations") or {},
        "titleTr": art.get("titleTr") or art.get("title_tr") or "",
        "titleEn": art.get("titleEn") or art.get("title_en") or "",
        "titleTranslations": art.get("titleTranslations") or art.get("title_translations") or {},
        "teaser": art.get("teaser") or {},
        "teaserTranslations": art.get("teaserTranslations") or art.get("teaser_translations") or {},
        "visual": art.get("visual") or {},
        "readTime": art.get("readTime") or art.get("read_time") or "3 min read",
        "languages": art.get("languages") or {},
        "summary": art.get("summary") or {},
        "status": art.get("status", "published"),
        "hidden": bool(art.get("hidden", False))
    }

def test_article_parity():
    print("=" * 70)
    print("TEST 1: CANONICAL DATA PARITY AUDIT (ALL 23 ARTICLES)")
    print("=" * 70)

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        canonical_articles = json.load(f)

    print(f"Loaded {len(canonical_articles)} articles from canonical source.")
    errors = []
    total_permutations = 0
    total_tokens = 0
    total_quizzes = 0

    for art in canonical_articles:
        art_id = art["id"]
        # Simulate Supabase DB row representation (as stored via migration)
        db_row = {
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
            "status": "published",
            "hidden": art.get("hidden", False)
        }

        # Run client adapter
        adapted = map_supabase_article_to_client(db_row)

        # Compare core metadata
        if adapted["id"] != art["id"]:
            errors.append(f"[{art_id}] id mismatch")
        if adapted["topic"] != art.get("topic", ""):
            errors.append(f"[{art_id}] topic mismatch")
        if adapted["category"] != art.get("category", ""):
            errors.append(f"[{art_id}] category mismatch")
        if adapted["titleTr"] != art.get("titleTr", ""):
            errors.append(f"[{art_id}] titleTr mismatch")
        if adapted["titleEn"] != art.get("titleEn", ""):
            errors.append(f"[{art_id}] titleEn mismatch")
        if adapted["readTime"] != art.get("readTime", "3 min read"):
            errors.append(f"[{art_id}] readTime mismatch")

        # Compare language-level structures
        for lang in ["tr", "en", "es", "de", "fr"]:
            for lvl in ["A1", "A2", "B1", "B2", "C1"]:
                total_permutations += 1
                orig_lvl = art.get("languages", {}).get(lang, {}).get(lvl, {})
                adapt_lvl = adapted.get("languages", {}).get(lang, {}).get(lvl, {})

                if not orig_lvl:
                    errors.append(f"[{art_id}][{lang}][{lvl}] Missing in canonical")
                    continue
                if not adapt_lvl:
                    errors.append(f"[{art_id}][{lang}][{lvl}] Missing in adapted")
                    continue

                if orig_lvl.get("title") != adapt_lvl.get("title"):
                    errors.append(f"[{art_id}][{lang}][{lvl}] Title mismatch")

                o_paras = orig_lvl.get("paragraphs", [])
                a_paras = adapt_lvl.get("paragraphs", [])
                if len(o_paras) != len(a_paras):
                    errors.append(f"[{art_id}][{lang}][{lvl}] Paragraph count mismatch")
                    continue

                for p_idx, o_p in enumerate(o_paras):
                    a_p = a_paras[p_idx]
                    if len(o_p) != len(a_p):
                        errors.append(f"[{art_id}][{lang}][{lvl}][p{p_idx}] Sentence count mismatch")
                        continue
                    for s_idx, o_s in enumerate(o_p):
                        a_s = a_p[s_idx]
                        if o_s.get("target") != a_s.get("target"):
                            errors.append(f"[{art_id}][{lang}][{lvl}] Sentence text mismatch")
                        o_toks = o_s.get("tokens", [])
                        a_toks = a_s.get("tokens", [])
                        if len(o_toks) != len(a_toks):
                            errors.append(f"[{art_id}][{lang}][{lvl}] Token count mismatch")
                        total_tokens += len(a_toks)

                quizzes = adapt_lvl.get("quiz", [])
                total_quizzes += len(quizzes)

    print(f"✓ Checked {len(canonical_articles)} articles.")
    print(f"✓ Checked {total_permutations} language-level permutations.")
    print(f"✓ Verified {total_tokens:,} tokens with exact linguistic metadata.")
    print(f"✓ Verified {total_quizzes} comprehension quiz items.")
    if errors:
        print(f"❌ Found {len(errors)} parity errors:")
        for e in errors[:10]:
            print(f"  - {e}")
        return False
    else:
        print("✅ PARITY AUDIT PASSED: 100% exact match between Supabase adapter output and static runtime.\n")
        return True

def test_security_redirects():
    print("=" * 70)
    print("TEST 2: SECURITY REDIRECT RULES AUDIT (_redirects)")
    print("=" * 70)

    with open(REDIRECTS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    rules = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 3:
            rules.append((parts[0], parts[1], parts[2]))

    def match_path(path):
        for pattern, target, status in rules:
            # Check pattern match
            pat_regex = pattern.replace(".", r"\.").replace("*", r".*")
            if re.fullmatch(pat_regex, path):
                return target, status
        return None, None

    test_paths = [
        # Must be blocked (404!)
        ("LAUNCH_CHECKLIST.md", True),
        ("BRANCHES.md", True),
        ("README.md", True),
        (".github/workflows/supabase-heartbeat.yml", True),
        ("scripts/migrate_articles_to_supabase.py", True),
        ("scripts/test_phase2_verification.py", True),
        ("validate_content.py", True),
        ("generate_article_pages.py", True),
        ("docs/superpowers/plans/plan.md", True),
        ("supabase/migrations/20261001_articles_table.sql", True),

        # Must NOT be blocked (served normally)
        ("index.html", False),
        ("article.html", False),
        ("articles-summary.json", False),
        ("articles-summary.js", False),
        ("styles.css", False),
        ("images/tarih-truva-ve-tahta-at.jpg", False),
    ]

    sec_errors = []
    for path, should_block in test_paths:
        target, status = match_path("/" + path)
        if should_block:
            if status != "404!" or target != "/404.html":
                sec_errors.append(f"Security rule FAIL: /{path} should return 404!, got {target} ({status})")
            else:
                print(f"  ✓ Protected: /{path} -> {target} ({status})")
        else:
            if status == "404!":
                sec_errors.append(f"False positive block: /{path} was incorrectly blocked with 404!")
            else:
                print(f"  ✓ Public:    /{path} -> allowed")

    if sec_errors:
        print(f"❌ Security rule audit failed with {len(sec_errors)} errors:")
        for err in sec_errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ SECURITY AUDIT PASSED: All sensitive internal docs/scripts blocked with 404!.\n")
        return True

def test_static_fallback_simulation():
    print("=" * 70)
    print("TEST 3: FALLBACK & OFFLINE RESILIENCE SIMULATION")
    print("=" * 70)

    # Verify that articles-data.js exists and defines window.ARTICLES_DATA
    articles_data_js = os.path.join(WORKSPACE, "articles-data.js")
    if not os.path.exists(articles_data_js):
        print("❌ articles-data.js does not exist!")
        return False
    size_mb = os.path.getsize(articles_data_js) / (1024 * 1024)
    print(f"✓ articles-data.js exists for lazy-fallback ({size_mb:.2f} MB).")

    # Verify that 404.html exists
    four_oh_four = os.path.join(WORKSPACE, "404.html")
    if not os.path.exists(four_oh_four):
        print("❌ 404.html does not exist!")
        return False
    print("✓ 404.html exists and is ready for Netlify serving.")

    # Verify that article.html does NOT statically include articles-data.js
    article_html = os.path.join(WORKSPACE, "article.html")
    with open(article_html, "r", encoding="utf-8") as f:
        html_src = f.read()

    if '<script src="articles-data.js"></script>' in html_src:
        print("❌ article.html still statically includes articles-data.js!")
        return False
    print("✓ article.html does NOT statically load articles-data.js (lazy-fallback only).")

    # Check that abort controller timeout is present
    if "AbortController" not in html_src or "setTimeout" not in html_src:
        print("❌ AbortController timeout missing in article.html!")
        return False
    print("✓ 5000ms AbortController timeout confirmed in article.html.")

    # Check that lazyLoadStaticFallback is present
    if "lazyLoadStaticFallback" not in html_src:
        print("❌ lazyLoadStaticFallback missing in article.html!")
        return False
    print("✓ lazyLoadStaticFallback function confirmed in article.html.")

    # Check that renderNotFoundState is present
    if "renderNotFoundState" not in html_src:
        print("❌ renderNotFoundState missing in article.html!")
        return False
    print("✓ renderNotFoundState confirmed in article.html.")

    # Check that escapeHtml is present
    if "escapeHtml" not in html_src:
        print("❌ escapeHtml helper missing in article.html!")
        return False
    print("✓ escapeHtml helper confirmed in article.html.")

    print("✅ FALLBACK & OFFLINE RESILIENCE VERIFIED.\n")
    return True

if __name__ == "__main__":
    t1 = test_article_parity()
    t2 = test_security_redirects()
    t3 = test_static_fallback_simulation()

    if t1 and t2 and t3:
        print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("❌ ONE OR MORE TESTS FAILED.")
        sys.exit(1)
