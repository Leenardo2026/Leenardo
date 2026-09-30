#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Patch Script for German Fallthrough Verb & Predicate Tokens.
Patches tokens in articles.json that fell through to generic 'Wort' / 'Substantiv'
with identical echo translations (gloss.tr == token).
Does NOT touch tokens that already have high-confidence rule-based matches.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_JSON = BASE_DIR / "articles.json"

try:
    from scripts.german_fallthrough_dict import DE_ADDITIONAL_FALLTHROUGH_MAP
except ImportError:
    try:
        from german_fallthrough_dict import DE_ADDITIONAL_FALLTHROUGH_MAP
    except ImportError:
        DE_ADDITIONAL_FALLTHROUGH_MAP = {}


def patch_german_articles():
    print(f"Reading {ARTICLES_JSON}...")
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    patched_count = 0
    skipped_high_conf = 0

    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("de", {}).items():
            for p in lvl_data.get("paragraphs", []):
                if isinstance(p, list):
                    for s in p:
                        for tok in s.get("tokens", []):
                            raw = tok.get("token", "")
                            clean = re.sub(r"[^\w]", "", raw).lower()
                            if not clean or len(clean) <= 1:
                                continue

                            pos = tok.get("pos", "")
                            g = tok.get("gloss", {})
                            tr = g.get("tr", "")
                            is_echo = (not tr or tr.lower() == raw.lower() or tr.lower() == clean)

                            # STRICT GUARD: Only patch tokens in generic fallthrough set
                            if pos not in ["Wort", "Substantiv", "Eigenname"] and not is_echo:
                                skipped_high_conf += 1
                                continue

                            if clean in DE_ADDITIONAL_FALLTHROUGH_MAP:
                                lemma, new_pos, tr_trans, en_trans, note = DE_ADDITIONAL_FALLTHROUGH_MAP[clean]
                                tok["lemma"] = lemma
                                tok["pos"] = new_pos
                                g["tr"] = tr_trans
                                g["en"] = en_trans
                                tok["gloss"] = g
                                tok["note"] = note
                                patched_count += 1

    print(f"\n✓ Successfully patched {patched_count} German fallthrough tokens!")
    print(f"✓ Preserved {skipped_high_conf} high-confidence rule-based matches without modification.")

    print(f"\nWriting updated database to {ARTICLES_JSON}...")
    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ articles.json successfully saved.")


if __name__ == "__main__":
    patch_german_articles()
