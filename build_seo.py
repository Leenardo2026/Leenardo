#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Leenardo SEO & Static Pre-rendering Generator
------------------------------------------------
Generates:
1. 100 unique crawlable article pages (20 articles x 5 languages)
   Path: /{lang}/stories/{id}/{slug}/index.html
2. ID-based fallback alias pages for 100% link permanence
   Path: /{lang}/stories/{id}/index.html
3. Search engine robots.txt with sitemap directive
4. XML Sitemap with multilingual hreflang annotations
5. Netlify _redirects configuration for 301 permanent redirects
"""

import os
import re
import json
import html
import unicodedata
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_JSON = BASE_DIR / "articles.json"
ARTICLE_TEMPLATE_PATH = BASE_DIR / "article.html"
SITEMAP_XML = BASE_DIR / "sitemap.xml"
ROBOTS_TXT = BASE_DIR / "robots.txt"
NETLIFY_REDIRECTS = BASE_DIR / "_redirects"

DOMAIN = "https://leenardo.com"

LANG_META = {
    "tr": {"name": "Türkçe", "locale": "tr_TR", "default_support": "en", "level_desc": "Türkçe seviyelendirilmiş okuma parçası"},
    "en": {"name": "English", "locale": "en_US", "default_support": "tr", "level_desc": "Graded English reader article"},
    "es": {"name": "Español", "locale": "es_ES", "default_support": "en", "level_desc": "Artículo de lectura graduada en español"},
    "de": {"name": "Deutsch", "locale": "de_DE", "default_support": "en", "level_desc": "Abgestufter Lesetext auf Deutsch"},
    "fr": {"name": "Français", "locale": "fr_FR", "default_support": "en", "level_desc": "Article de lecture graduée en français"}
}

SUPPORTED_LANGUAGES = ["tr", "en", "es", "de", "fr"]
SUPPORTED_LEVELS = ["A1", "A2", "B1", "B2", "C1"]

TRACKING_SNIPPET = """  <!-- Google Analytics 4 (GA4) -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-L5G7ZG5437"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', 'G-L5G7ZG5437');
  </script>

  <!-- Microsoft Clarity -->
  <script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "CLARITY_PROJECT_ID");
  </script>"""

def slugify(text: str) -> str:
    """
    Produce clean, URL-safe slugs for multilingual strings
    handling Turkish, German, Spanish, French diacritics.
    """
    if not text:
        return "story"
    s = text.replace("İ", "i").replace("I", "i").replace("ı", "i")
    s = s.replace("ş", "s").replace("Ş", "s")
    s = s.replace("ğ", "g").replace("Ğ", "g")
    s = s.replace("ç", "c").replace("Ç", "c")
    s = s.replace("ö", "o").replace("Ö", "o")
    s = s.replace("ü", "u").replace("Ü", "u")
    s = s.replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "story"

def escape_attr(text: str) -> str:
    return html.escape(str(text or ""), quote=True)

def build_prerendered_body_paragraphs(paragraphs, support_lang, support_level_data):
    """
    Pre-render semantic HTML paragraphs so search engine bots can read
    the full article text without executing JavaScript.
    """
    html_parts = []
    for p_idx, para in enumerate(paragraphs):
        p_html = ['<p class="article-paragraph">']
        for s_idx, sent_obj in enumerate(para):
            sent_text = sent_obj.get("target", "")
            sent_id = f"sent-{p_idx}-{s_idx}"
            p_html.append(f'<span class="sentence-span" id="{sent_id}">')
            
            tokens = re.split(r'(\s+|[.,!?:;«»"“”()]+)', sent_text)
            for token in tokens:
                if not token:
                    continue
                if re.match(r'^\s+$', token) or re.match(r'^[.,!?:;«»"“”()]+$', token):
                    p_html.append(html.escape(token))
                else:
                    escaped_word = html.escape(token)
                    p_html.append(f'<span class="word-span">{escaped_word}</span>')
            
            p_html.append('</span>')
        p_html.append('</p>')
        html_parts.append("".join(p_html))
    return "\n".join(html_parts)

def build_prerendered_vocab(vocab_list, support_lang):
    """
    Pre-render vocabulary items for SEO and crawler visibility.
    """
    if not vocab_list:
        return ""
    cards = []
    for item in vocab_list:
        word = escape_attr(item.get("word", ""))
        level = escape_attr(item.get("level", "A1"))
        pos = escape_attr(item.get("pos", ""))
        translations = item.get("translations", {})
        trans = escape_attr(translations.get(support_lang, translations.get("en", translations.get("tr", ""))))
        
        card = (
            f'          <div class="vocab-card" data-word="{word}" data-level="{level}">\n'
            f'            <div class="vocab-card-header">\n'
            f'              <span class="vocab-card-word">{word}</span>\n'
            f'              <span class="vocab-card-level">{level}</span>\n'
            f'            </div>\n'
            f'            <div class="vocab-card-body">\n'
            f'              <div class="vocab-card-pos">{pos}</div>\n'
            f'              <div class="vocab-card-trans">{trans}</div>\n'
            f'            </div>\n'
            f'          </div>'
        )
        cards.append(card)
    return "\n".join(cards)

def build_prerendered_qa(qa_list, support_lang):
    """
    Pre-render comprehension Q&A items.
    """
    if not qa_list:
        return ""
    cards = []
    for q_idx, item in enumerate(qa_list, start=1):
        q_text = escape_attr(item.get("question", ""))
        ans_text = escape_attr(item.get("answer", ""))
        card = (
            f'          <div class="qa-item">\n'
            f'            <div class="qa-question"><strong>S{q_idx}.</strong> {q_text}</div>\n'
            f'            <div class="qa-answer">{ans_text}</div>\n'
            f'          </div>'
        )
        cards.append(card)
    return "\n".join(cards)

def generate_seo():
    print("=" * 65)
    print("💎 LEENARDO SEO & STATIC HTML PRE-RENDERING GENERATOR")
    print("=" * 65)

    if not ARTICLES_JSON.exists():
        print(f"❌ Error: {ARTICLES_JSON} does not exist.")
        return False

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    with open(ARTICLE_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # Pre-calculate slug maps for all articles
    slug_map = {}
    for art in articles:
        art_id = art["id"]
        slug_map[art_id] = {}
        for lang in SUPPORTED_LANGUAGES:
            title = art.get("titleTranslations", {}).get(lang) or art.get("topic", "")
            slug_map[art_id][lang] = slugify(title)

    today_str = datetime.now().strftime("%Y-%m-%d")
    sitemap_urls = []
    redirect_lines = [
        "# Leenardo Netlify 301 Permanent Redirects",
        "# Auto-generated by build_seo.py - Do not edit directly",
        ""
    ]

    total_pages_generated = 0

    # 1. Process each article in each language
    for art in articles:
        art_id = art["id"]
        img_rel = (art.get("visual") and art["visual"].get("imageUrl")) or ""
        img_url = f"{DOMAIN}/{img_rel.lstrip('/')}" if img_rel else f"{DOMAIN}/images/kultur-turk-kahvesi-ve-fincan.jpg"
        read_time = art.get("readTime", "4 min")

        for lang in SUPPORTED_LANGUAGES:
            lang_slug = slug_map[art_id][lang]
            canonical_path = f"/{lang}/stories/{art_id}/{lang_slug}/"
            canonical_url = f"{DOMAIN}{canonical_path}"

            support_lang = LANG_META[lang]["default_support"]
            
            target_a1 = art.get("languages", {}).get(lang, {}).get("A1", {})
            support_a1 = art.get("languages", {}).get(support_lang, {}).get("A1", {})
            
            title = target_a1.get("title") or art.get("titleTranslations", {}).get(lang) or art.get("topic", "")
            support_title = support_a1.get("title") or art.get("titleTranslations", {}).get(support_lang) or ""
            
            # Meta description
            desc = target_a1.get("grammarDesc") or f"{title} — Graded reading practice for language learners at CEFR A1-C1 levels on Leenardo."
            if isinstance(desc, dict):
                desc = desc.get(lang, desc.get("en", desc.get("tr", "")))
            desc_clean = re.sub(r'\s+', ' ', str(desc)).strip()
            if len(desc_clean) > 160:
                desc_clean = desc_clean[:157] + "..."

            category_name = (art.get("categoryTranslations", {}).get(lang)) or art.get("category", "Kültür")

            # Hreflang alternates
            hreflang_tags = []
            for alt_lang in SUPPORTED_LANGUAGES:
                alt_slug = slug_map[art_id][alt_lang]
                alt_url = f"{DOMAIN}/{alt_lang}/stories/{art_id}/{alt_slug}/"
                hreflang_tags.append(f'  <link rel="alternate" hreflang="{alt_lang}" href="{alt_url}">')
            en_slug = slug_map[art_id]["en"]
            hreflang_tags.append(f'  <link rel="alternate" hreflang="x-default" href="{DOMAIN}/en/stories/{art_id}/{en_slug}/">')
            hreflang_html = "\n".join(hreflang_tags)

            # JSON-LD Structured Data
            json_ld = {
                "@context": "https://schema.org",
                "@type": "Article",
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": canonical_url
                },
                "headline": title,
                "description": desc_clean,
                "image": img_url,
                "inLanguage": lang,
                "timeRequired": f"PT{read_time.split()[0]}M" if read_time and read_time[0].isdigit() else "PT4M",
                "educationalLevel": "CEFR A1-C1",
                "publisher": {
                    "@type": "Organization",
                    "name": "Leenardo",
                    "url": DOMAIN,
                    "logo": {
                        "@type": "ImageObject",
                        "url": f"{DOMAIN}/images/kultur-turk-kahvesi-ve-fincan.jpg"
                    }
                },
                "author": {
                    "@type": "Organization",
                    "name": "Leenardo Editorial Team"
                },
                "datePublished": "2026-09-01",
                "dateModified": today_str
            }
            json_ld_script = f'<script type="application/ld+json">\n{json.dumps(json_ld, ensure_ascii=False, indent=2)}\n</script>'

            # Pre-rendered HTML sections
            prerendered_body = build_prerendered_body_paragraphs(target_a1.get("paragraphs", []), support_lang, support_a1)
            prerendered_vocab = build_prerendered_vocab(target_a1.get("vocab", []), support_lang)
            prerendered_qa = build_prerendered_qa(target_a1.get("qa", []), support_lang)

            # Construct bespoke head
            seo_head = (
                f'  <meta charset="UTF-8">\n'
                f'  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
                f'  <title>{escape_attr(title)} — Leenardo | {LANG_META[lang]["name"]}</title>\n'
                f'  <meta name="description" content="{escape_attr(desc_clean)}">\n'
                f'  <link rel="canonical" href="{canonical_url}">\n'
                f'  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">\n'
                f'  <base href="/">\n\n'
                f'  <!-- OpenGraph Social Metadata -->\n'
                f'  <meta property="og:type" content="article">\n'
                f'  <meta property="og:site_name" content="Leenardo">\n'
                f'  <meta property="og:title" content="{escape_attr(title)} — Leenardo">\n'
                f'  <meta property="og:description" content="{escape_attr(desc_clean)}">\n'
                f'  <meta property="og:url" content="{canonical_url}">\n'
                f'  <meta property="og:image" content="{img_url}">\n'
                f'  <meta property="og:locale" content="{LANG_META[lang]["locale"]}">\n\n'
                f'  <!-- Twitter Card Metadata -->\n'
                f'  <meta name="twitter:card" content="summary_large_image">\n'
                f'  <meta name="twitter:title" content="{escape_attr(title)} — Leenardo">\n'
                f'  <meta name="twitter:description" content="{escape_attr(desc_clean)}">\n'
                f'  <meta name="twitter:image" content="{img_url}">\n\n'
                f'  <!-- Multilingual Hreflang SEO -->\n'
                f'{hreflang_html}\n\n'
                f'  <!-- Schema.org Article Structured Data -->\n'
                f'{json_ld_script}\n\n'
                f'{TRACKING_SNIPPET}'
            )

            # Inject into article.html template
            page_html = template
            page_html = re.sub(r'<html[^>]*>', f'<html lang="{lang}">', page_html, count=1)
            
            page_html = re.sub(
                r'<head>.*?(<link rel="preconnect")',
                f'<head>\n{seo_head}\n  \\1',
                page_html,
                count=1,
                flags=re.DOTALL
            )

            # Absolute asset paths
            page_html = page_html.replace('href="auth.css"', 'href="/auth.css"')
            page_html = page_html.replace('src="articles-data.js"', 'src="/articles-data.js"')
            page_html = page_html.replace('src="supabase-client.js"', 'src="/supabase-client.js"')
            page_html = page_html.replace('src="auth-ui.js"', 'src="/auth-ui.js"')

            # Pre-fill Initial HTML fields
            page_html = page_html.replace('<span class="article-category-tag" id="article-category-badge">Category</span>',
                                          f'<span class="article-category-tag" id="article-category-badge">{escape_attr(category_name)}</span>')
            page_html = page_html.replace('<span class="article-read-time" id="article-read-time">⏱️ 4 min read</span>',
                                          f'<span class="article-read-time" id="article-read-time">⏱️ {escape_attr(read_time)} • A1</span>')
            page_html = page_html.replace('<h1 class="article-main-title" id="article-main-title">Article Headline</h1>',
                                          f'<h1 class="article-main-title" id="article-main-title">{escape_attr(title)}</h1>')
            page_html = page_html.replace('<div class="article-support-title" id="article-support-title">Translated Headline</div>',
                                          f'<div class="article-support-title" id="article-support-title">{escape_attr(support_title)}</div>')
            
            # Pre-fill Featured Image
            if img_rel:
                img_box_html = (
                    f'<div class="featured-image-box" id="featured-img-box" style="display:block;">\n'
                    f'      <img id="article-featured-img" class="featured-image" src="/{img_rel.lstrip("/")}" alt="{escape_attr(title)}">\n'
                    f'      <div class="featured-caption" id="article-img-caption">{escape_attr(title)}</div>\n'
                    f'    </div>'
                )
                page_html = re.sub(r'<div class="featured-image-box"[^>]*>.*?</div>\s*</div>', img_box_html, page_html, count=1, flags=re.DOTALL)

            # Pre-fill article body container
            if prerendered_body:
                page_html = page_html.replace(
                    '<div class="article-body" id="article-body-content">\n        <!-- Paragraphs injected dynamically -->\n      </div>',
                    f'<div class="article-body" id="article-body-content">\n{prerendered_body}\n      </div>'
                )

            # Pre-fill vocabulary grid
            if prerendered_vocab:
                page_html = page_html.replace(
                    '<div class="vocab-grid" id="vocab-list-container">\n            <!-- Vocab pills injected dynamically -->\n          </div>',
                    f'<div class="vocab-grid" id="vocab-list-container">\n{prerendered_vocab}\n          </div>'
                )

            # Pre-fill comprehension Q&A
            if prerendered_qa:
                page_html = page_html.replace(
                    '<div class="qa-list" id="qa-list-container">\n            <!-- Questions injected dynamically -->\n          </div>',
                    f'<div class="qa-list" id="qa-list-container">\n{prerendered_qa}\n          </div>'
                )

            # Pre-select target and support language in header select
            page_html = re.sub(
                r'(<select id="target-lang-select"[^>]*>.*?<option value="' + lang + r'")',
                r'\1 selected',
                page_html,
                count=1,
                flags=re.DOTALL
            )

            # Inject initial hydration state snippet before closing script
            hydration_js = (
                f'\n    // Pre-rendered SEO context for immediate client hydration\n'
                f'    window.LEENARDO_SSR = {{\n'
                f'      articleId: {json.dumps(art_id)},\n'
                f'      targetLang: {json.dumps(lang)},\n'
                f'      supportLang: {json.dumps(support_lang)},\n'
                f'      level: "A1",\n'
                f'      canonicalSlug: {json.dumps(lang_slug)}\n'
                f'    }};\n'
            )
            page_html = page_html.replace(
                'const SUPPORTED_LANGUAGES =',
                f'{hydration_js}\n    const SUPPORTED_LANGUAGES ='
            )

            # Write out to directory /{lang}/stories/{id}/{slug}/index.html
            target_dir = BASE_DIR / lang / "stories" / art_id / lang_slug
            target_dir.mkdir(parents=True, exist_ok=True)
            output_file = target_dir / "index.html"
            with open(output_file, "w", encoding="utf-8") as out:
                out.write(page_html)

            # Also write alias/shortcut index.html at /{lang}/stories/{id}/index.html
            alias_dir = BASE_DIR / lang / "stories" / art_id
            alias_dir.mkdir(parents=True, exist_ok=True)
            alias_file = alias_dir / "index.html"
            alias_html = (
                f'<!DOCTYPE html>\n'
                f'<html lang="{lang}">\n'
                f'<head>\n'
                f'  <meta charset="UTF-8">\n'
                f'  <title>{escape_attr(title)} — Leenardo</title>\n'
                f'  <link rel="canonical" href="{canonical_url}">\n'
                f'  <meta http-equiv="refresh" content="0; url={canonical_path}">\n'
                f'  <script>window.location.replace({json.dumps(canonical_path)});</script>\n'
                f'</head>\n'
                f'<body>\n'
                f'  <p>Redirecting to <a href="{canonical_path}">{escape_attr(title)}</a>...</p>\n'
                f'</body>\n'
                f'</html>'
            )
            with open(alias_file, "w", encoding="utf-8") as out_alias:
                out_alias.write(alias_html)

            # Add redirect rule for Netlify
            redirect_lines.append(f"/{lang}/stories/{art_id}  {canonical_path}  301")
            redirect_lines.append(f"/{lang}/stories/{art_id}/  {canonical_path}  301")

            # Collect for sitemap
            sitemap_urls.append({
                "loc": canonical_url,
                "lastmod": today_str,
                "changefreq": "weekly",
                "priority": "0.8",
                "hreflang": [
                    {"lang": l, "href": f"{DOMAIN}/{l}/stories/{art_id}/{slug_map[art_id][l]}/"}
                    for l in SUPPORTED_LANGUAGES
                ]
            })

            total_pages_generated += 1

    print(f"✓ Generated {total_pages_generated} static crawlable HTML pages across 5 languages.")

    # 2. Build sitemap.xml
    sitemap_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
        '  <url>',
        f'    <loc>{DOMAIN}/</loc>',
        f'    <lastmod>{today_str}</lastmod>',
        '    <changefreq>daily</changefreq>',
        '    <priority>1.0</priority>',
    ]
    for l in SUPPORTED_LANGUAGES:
        sitemap_lines.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{DOMAIN}/?target={l}"/>')
    sitemap_lines.append('  </url>')

    for entry in sitemap_urls:
        sitemap_lines.append('  <url>')
        sitemap_lines.append(f'    <loc>{entry["loc"]}</loc>')
        sitemap_lines.append(f'    <lastmod>{entry["lastmod"]}</lastmod>')
        sitemap_lines.append(f'    <changefreq>{entry["changefreq"]}</changefreq>')
        sitemap_lines.append(f'    <priority>{entry["priority"]}</priority>')
        for hl in entry["hreflang"]:
            sitemap_lines.append(f'    <xhtml:link rel="alternate" hreflang="{hl["lang"]}" href="{hl["href"]}"/>')
        en_href = next(hl["href"] for hl in entry["hreflang"] if hl["lang"] == "en")
        sitemap_lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en_href}"/>')
        sitemap_lines.append('  </url>')

    sitemap_lines.append('</urlset>')
    sitemap_content = "\n".join(sitemap_lines)
    with open(SITEMAP_XML, "w", encoding="utf-8") as f:
        f.write(sitemap_content)
    print(f"✓ Generated sitemap.xml with {len(sitemap_urls) + 1} URLs ({SITEMAP_XML.stat().st_size:,} bytes).")

    # 3. Build robots.txt
    robots_content = f"""# robots.txt for Leenardo Graded Multilingual Reader
User-agent: *
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""
    with open(ROBOTS_TXT, "w", encoding="utf-8") as f:
        f.write(robots_content)
    print(f"✓ Generated robots.txt pointing to {DOMAIN}/sitemap.xml.")

    # 4. Write Netlify _redirects
    redirect_lines.extend([
        "",
        "# Legacy query string redirection fallback",
        "# Handled gracefully by client-side router in article.html as well",
        "/article.html  /  302",
        "",
        "# Note: Intentionally NO catch-all '/* /index.html 200' to prevent Soft 404s",
        "# Non-existent URLs will cleanly serve /404.html with genuine HTTP 404 status."
    ])
    with open(NETLIFY_REDIRECTS, "w", encoding="utf-8") as f:
        f.write("\n".join(redirect_lines) + "\n")
    print("✓ Generated Netlify _redirects configuration.")

    print(f"\n🎉 All SEO assets generated successfully! (Total {total_pages_generated} pages + sitemap + robots + redirects)")
    return True

if __name__ == "__main__":
    generate_seo()
