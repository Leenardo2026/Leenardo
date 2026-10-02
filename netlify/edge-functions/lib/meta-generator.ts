// ==============================================================================
// Leenardo Central Metadata & SEO Generator
// Phase 3: Edge-rendered multilingual article routes (/{lang}/articles/{slug})
// ==============================================================================

export const SUPPORTED_LANGUAGES = ["tr", "en", "es", "de", "fr"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

export const SUPPORTED_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
export type SupportedLevel = (typeof SUPPORTED_LEVELS)[number];

export const LOCALE_MAP: Record<SupportedLanguage, string> = {
  tr: "tr_TR",
  en: "en_US",
  es: "es_ES",
  de: "de_DE",
  fr: "fr_FR",
};

export const DEFAULT_BASE_URL = "https://leenardo.com";
export const DEFAULT_IMAGE = "https://leenardo.com/logo-1024.png";
export const X_DEFAULT_LANG: SupportedLanguage = "en";

export interface ArticleMetaData {
  title: string;
  description: string;
  canonicalUrl: string;
  ogUrl: string;
  imageUrl: string;
  locale: string;
  hreflangs: Array<{ lang: string; url: string }>;
  targetLang: SupportedLanguage;
  level: SupportedLevel;
}

export function escapeHtml(str: string): string {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Builds all canonical, hreflang, Open Graph, and Twitter metadata
 * for an article under a specific target language and level.
 */
export function generateArticleMeta(params: {
  article: any;
  lang: SupportedLanguage;
  level: SupportedLevel;
  slug: string;
  baseUrl?: string;
}): ArticleMetaData {
  const { article, lang, level, slug, baseUrl = DEFAULT_BASE_URL } = params;

  // 1. Resolve localized title
  const targetLevelData = article.languages?.[lang]?.[level];
  const localizedTitle =
    targetLevelData?.title ||
    article.title_translations?.[lang] ||
    article.titleTranslations?.[lang] ||
    (lang === "tr" ? article.title_tr || article.titleTr : "") ||
    (lang === "en" ? article.title_en || article.titleEn : "") ||
    article.topic ||
    "Leenardo Story";

  const fullTitle = `${localizedTitle} | Leenardo`;

  // 2. Resolve localized teaser / meta description
  let teaser =
    article.teaser_translations?.[lang] ||
    article.teaserTranslations?.[lang] ||
    "";
  if (!teaser && article.teaser) {
    if (typeof article.teaser === "object") {
      teaser = article.teaser[lang] || article.teaser.en || article.teaser.tr || "";
    } else {
      teaser = String(article.teaser);
    }
  }
  if (!teaser) {
    teaser = `${localizedTitle}. Graded multilingual story with sentence-by-sentence translations and interactive vocabulary tools on Leenardo.`;
  }

  // 3. Resolve visual image URL
  let imgUrl =
    article.visual?.imageUrl ||
    article.visual?.image_url ||
    article.featuredImage ||
    "";
  let fullImageUrl = DEFAULT_IMAGE;
  if (imgUrl) {
    if (imgUrl.startsWith("http://") || imgUrl.startsWith("https://")) {
      fullImageUrl = imgUrl;
    } else if (imgUrl.startsWith("/")) {
      fullImageUrl = `${baseUrl}${imgUrl}`;
    } else {
      fullImageUrl = `${baseUrl}/${imgUrl}`;
    }
  }

  // 4. Canonical URL is strictly clean without query parameters
  const canonicalUrl = `${baseUrl}/${lang}/articles/${slug}`;

  // 5. Build hreflang matrix across all 5 languages + x-default (points to /en/articles/:slug)
  const hreflangs: Array<{ lang: string; url: string }> = SUPPORTED_LANGUAGES.map((l) => ({
    lang: l,
    url: `${baseUrl}/${l}/articles/${slug}`,
  }));
  hreflangs.push({
    lang: "x-default",
    url: `${baseUrl}/${X_DEFAULT_LANG}/articles/${slug}`,
  });

  return {
    title: fullTitle,
    description: teaser.trim(),
    canonicalUrl,
    ogUrl: canonicalUrl,
    imageUrl: fullImageUrl,
    locale: LOCALE_MAP[lang] || "en_US",
    hreflangs,
    targetLang: lang,
    level,
  };
}

/**
 * Injects pre-rendered SEO, canonical, and social meta tags into HTML.
 */
export function injectMetaIntoHtml(html: string, meta: ArticleMetaData): string {
  const safeTitle = escapeHtml(meta.title);
  const safeDesc = escapeHtml(meta.description);
  const safeImg = escapeHtml(meta.imageUrl);
  const safeCanonical = escapeHtml(meta.canonicalUrl);

  // 1. Update <title>
  let output = html.replace(
    /<title>[\s\S]*?<\/title>/i,
    `<title>${safeTitle}</title>`
  );

  // 2. Update html lang attribute
  output = output.replace(
    /<html([^>]*)lang="[^"]*"/i,
    `<html$1lang="${meta.targetLang}"`
  );

  // 3. Update meta description
  output = output.replace(
    /<meta\s+name="description"\s+content="[^"]*"\s*\/?>/i,
    `<meta name="description" content="${safeDesc}">`
  );

  // 4. Update canonical link
  output = output.replace(
    /<link\s+rel="canonical"\s+href="[^"]*"\s*\/?>/i,
    `<link rel="canonical" href="${safeCanonical}">`
  );

  // 5. Update Open Graph tags
  output = output.replace(
    /<meta\s+property="og:title"\s+content="[^"]*"\s*\/?>/i,
    `<meta property="og:title" content="${safeTitle}">`
  );
  output = output.replace(
    /<meta\s+property="og:description"\s+content="[^"]*"\s*\/?>/i,
    `<meta property="og:description" content="${safeDesc}">`
  );
  output = output.replace(
    /<meta\s+property="og:image"\s+content="[^"]*"\s*\/?>/i,
    `<meta property="og:image" content="${safeImg}">`
  );
  output = output.replace(
    /<meta\s+property="og:url"\s+content="[^"]*"\s*\/?>/i,
    `<meta property="og:url" content="${safeCanonical}">`
  );

  // 6. Update Twitter Card tags
  output = output.replace(
    /<meta\s+name="twitter:title"\s+content="[^"]*"\s*\/?>/i,
    `<meta name="twitter:title" content="${safeTitle}">`
  );
  output = output.replace(
    /<meta\s+name="twitter:description"\s+content="[^"]*"\s*\/?>/i,
    `<meta name="twitter:description" content="${safeDesc}">`
  );
  output = output.replace(
    /<meta\s+name="twitter:image"\s+content="[^"]*"\s*\/?>/i,
    `<meta name="twitter:image" content="${safeImg}">`
  );

  // 7. Inject hreflang tags directly after canonical link
  const hreflangTags = meta.hreflangs
    .map(
      (h) => `  <link rel="alternate" hreflang="${h.lang}" href="${escapeHtml(h.url)}">`
    )
    .join("\n");

  // Remove any preexisting alternate hreflangs
  output = output.replace(/\s*<link\s+rel="alternate"\s+hreflang="[^"]*"\s+href="[^"]*"\s*\/?>/gi, "");

  output = output.replace(
    /<link\s+rel="canonical"\s+href="[^"]*"\s*\/?>/i,
    `<link rel="canonical" href="${safeCanonical}">\n${hreflangTags}`
  );

  return output;
}
