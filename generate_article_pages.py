#!/usr/bin/env python3
"""
Static Page Generator for Leenardo Articles.
Generates physical /articles/{id}.html files for each story in articles.json.
This ensures:
1. Zero-config compatibility with static CDNs, Netlify, and local development servers.
2. Full SEO and social media rich link cards (WhatsApp, Twitter/X, Facebook, Telegram)
   with dedicated pre-rendered Open Graph / Twitter meta tags per story.
"""

import json
import os
import re
import sys

BASE_URL = "https://leenardo.com"
DEFAULT_IMG = "https://leenardo.com/logo-1024.png"

def escape_attr(text):
    if not text:
        return ""
    return (text.replace("&", "&amp;")
                .replace('"', "&quot;")
                .replace("<", "&lt;")
                .replace(">", "&gt;"))

def generate_pages(articles_json="articles.json", template_html="article.html", output_dir="articles"):
    if not os.path.exists(articles_json):
        print(f"Error: {articles_json} not found.")
        sys.exit(1)
    if not os.path.exists(template_html):
        print(f"Error: {template_html} not found.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    with open(articles_json, "r", encoding="utf-8") as f:
        articles = json.load(f)

    with open(template_html, "r", encoding="utf-8") as f:
        template = f.read()

    generated_count = 0

    for art in articles:
        art_id = art.get("id")
        if not art_id or art.get("hidden"):
            continue

        # Extract primary title
        title = art.get("topic") or ""
        tr_data = (art.get("languages") or {}).get("tr", {})
        if "A1" in tr_data and "title" in tr_data["A1"]:
            title = tr_data["A1"]["title"]
        elif "titleTranslations" in art and "tr" in art["titleTranslations"]:
            title = art["titleTranslations"]["tr"]
        elif "titleTranslations" in art and "en" in art["titleTranslations"]:
            title = art["titleTranslations"]["en"]

        # Extract teaser / description
        teaser = ""
        if "teaserTranslations" in art:
            teaser = art["teaserTranslations"].get("tr") or art["teaserTranslations"].get("en") or ""
        if not teaser and "teaser" in art:
            if isinstance(art["teaser"], dict):
                teaser = art["teaser"].get("tr") or art["teaser"].get("en") or ""
            else:
                teaser = str(art["teaser"])
        if not teaser:
            teaser = f"{title}. Graded multilingual story with sentence-by-sentence translations and interactive vocabulary tools on Leenardo."

        # Extract visual image
        img_url = (art.get("visual") or {}).get("imageUrl") or art.get("featuredImage") or ""
        if img_url:
            if img_url.startswith("http://") or img_url.startswith("https://"):
                full_img = img_url
            elif img_url.startswith("/"):
                full_img = f"{BASE_URL}{img_url}"
            else:
                full_img = f"{BASE_URL}/{img_url}"
        else:
            full_img = DEFAULT_IMG

        canonical_url = f"{BASE_URL}/articles/{art_id}.html"

        # Customize head tags
        page_content = template

        # Replace Title
        page_title = f"{escape_attr(title)} — Leenardo"
        page_content = re.sub(
            r"<title>.*?</title>",
            f"<title>{page_title}</title>",
            page_content,
            count=1,
            flags=re.IGNORECASE
        )

        # Replace Meta Description
        safe_desc = escape_attr(teaser.strip())
        page_content = re.sub(
            r'<meta\s+name="description"\s+content=".*?"\s*>',
            f'<meta name="description" content="{safe_desc}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )

        # Replace Canonical
        page_content = re.sub(
            r'<link\s+rel="canonical"\s+href=".*?"\s*>',
            f'<link rel="canonical" href="{canonical_url}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )

        # Replace OpenGraph
        safe_title = escape_attr(f"{title} | Leenardo")
        page_content = re.sub(
            r'<meta\s+property="og:title"\s+content=".*?"\s*>',
            f'<meta property="og:title" content="{safe_title}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )
        page_content = re.sub(
            r'<meta\s+property="og:description"\s+content=".*?"\s*>',
            f'<meta property="og:description" content="{safe_desc}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )
        page_content = re.sub(
            r'<meta\s+property="og:image"\s+content=".*?"\s*>',
            f'<meta property="og:image" content="{escape_attr(full_img)}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )
        page_content = re.sub(
            r'<meta\s+property="og:url"\s+content=".*?"\s*>',
            f'<meta property="og:url" content="{canonical_url}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )

        # Replace Twitter
        page_content = re.sub(
            r'<meta\s+name="twitter:title"\s+content=".*?"\s*>',
            f'<meta name="twitter:title" content="{safe_title}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )
        page_content = re.sub(
            r'<meta\s+name="twitter:description"\s+content=".*?"\s*>',
            f'<meta name="twitter:description" content="{safe_desc}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )
        page_content = re.sub(
            r'<meta\s+name="twitter:image"\s+content=".*?"\s*>',
            f'<meta name="twitter:image" content="{escape_attr(full_img)}">',
            page_content,
            count=1,
            flags=re.IGNORECASE
        )

        out_file = os.path.join(output_dir, f"{art_id}.html")
        with open(out_file, "w", encoding="utf-8") as out:
            out.write(page_content)

        generated_count += 1

    print(f"✓ Successfully generated {generated_count} distinct article pages in {output_dir}/")

if __name__ == "__main__":
    generate_pages()
