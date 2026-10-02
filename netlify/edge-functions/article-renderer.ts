// ==============================================================================
// Leenardo Netlify Edge Function: Article Renderer
// Route: /:lang/articles/:slug
// Features: PostgREST slim fetch, server-rendered level/C1 content,
//           canonical & hreflang injection, Netlify Edge CDN caching
// ==============================================================================

import type { Context } from "@netlify/edge-functions";
import {
  SUPPORTED_LANGUAGES,
  SUPPORTED_LEVELS,
  SupportedLanguage,
  SupportedLevel,
  generateArticleMeta,
  injectMetaIntoHtml,
  escapeHtml,
} from "./lib/meta-generator.ts";

const DEFAULT_SUPABASE_URL = "https://vkddnvpqnccstcjnqfyq.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY =
  "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-";

export default async function handler(request: Request, context: Context) {
  const url = new URL(request.url);

  // Diagnostic Entry Log
  console.log(`[Edge] Incoming request: ${request.method} ${url.pathname}${url.search}`);

  // 1. Validate route params (:lang and :slug)
  const pathParts = url.pathname.replace(/^\/|\/$/g, "").split("/");
  if (pathParts.length !== 3 || pathParts[1] !== "articles") {
    console.error(`[Edge] Invalid route structure for path: ${url.pathname}`);
    return context.next();
  }

  const rawLang = pathParts[0].toLowerCase();
  const rawSlug = pathParts[2];

  if (!SUPPORTED_LANGUAGES.includes(rawLang as SupportedLanguage)) {
    console.error(`[Edge] Unsupported target language: "${rawLang}"`);
    return new Response("Language not supported", {
      status: 404,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }
  const targetLang = rawLang as SupportedLanguage;

  if (!rawSlug || rawSlug.trim() === "") {
    console.error("[Edge] Missing or empty article slug in request URL");
    return new Response("Article not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }
  const slug = decodeURIComponent(rawSlug.trim());

  // 2. Resolve level parameter (?level=A1..C1, defaults to C1)
  const queryLevel = (url.searchParams.get("level") || "").toUpperCase();
  const activeLevel: SupportedLevel = SUPPORTED_LEVELS.includes(
    queryLevel as SupportedLevel
  )
    ? (queryLevel as SupportedLevel)
    : "C1";

  // Resolve support language parameter (?support=en..tr)
  const querySupport = (url.searchParams.get("support") || "").toLowerCase();
  const supportLang: SupportedLanguage = SUPPORTED_LANGUAGES.includes(
    querySupport as SupportedLanguage
  )
    ? (querySupport as SupportedLanguage)
    : targetLang === "tr"
    ? "en"
    : "tr";

  // 3. Supabase Configuration
  const supabaseUrl =
    Deno.env.get("SUPABASE_URL") || DEFAULT_SUPABASE_URL;
  const supabaseAnonKey =
    Deno.env.get("SUPABASE_ANON_KEY") || DEFAULT_SUPABASE_ANON_KEY;

  // 4. Fetch article data from Supabase REST API (with 3-second timeout)
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3000);

  let article: any = null;
  try {
    // PostgREST slim fetch projecting metadata and target language block
    const selectQuery = [
      "id",
      "topic",
      "category",
      "category_translations",
      "title_tr",
      "title_en",
      "title_translations",
      "teaser",
      "teaser_translations",
      "visual",
      "read_time",
      `languages->${targetLang}`,
      "status",
      "hidden",
    ].join(",");

    const endpoint = `${supabaseUrl}/rest/v1/articles?id=eq.${encodeURIComponent(
      slug
    )}&status=eq.published&hidden=eq.false&select=${selectQuery}`;

    // Publishable keys are sent strictly in "apikey" header (no Bearer token)
    const resp = await fetch(endpoint, {
      signal: controller.signal,
      headers: {
        apikey: supabaseAnonKey,
        Accept: "application/json",
      },
    });

    clearTimeout(timeoutId);

    if (resp.ok) {
      const data = await resp.json();
      if (Array.isArray(data) && data.length > 0) {
        article = data[0];
      } else {
        console.error(`[Edge] Supabase query returned 0 rows for slug "${slug}"`);
      }
    } else {
      console.error(`[Edge] Supabase REST error for slug "${slug}": status ${resp.status}`);
    }
  } catch (fetchErr) {
    clearTimeout(timeoutId);
    console.error(`[Edge] Supabase fetch exception for slug "${slug}":`, fetchErr);
  }

  // Fallback: If slim query returned empty or structure was unexpected, try standard select
  if (!article) {
    try {
      const fallbackEndpoint = `${supabaseUrl}/rest/v1/articles?id=eq.${encodeURIComponent(
        slug
      )}&status=eq.published&hidden=eq.false&select=*`;
      const fallbackResp = await fetch(fallbackEndpoint, {
        headers: {
          apikey: supabaseAnonKey,
          Accept: "application/json",
        },
      });
      if (fallbackResp.ok) {
        const fullData = await fallbackResp.json();
        if (Array.isArray(fullData) && fullData.length > 0) {
          article = fullData[0];
        }
      } else {
        console.error(`[Edge] Supabase fallback query failed: status ${fallbackResp.status}`);
      }
    } catch (fbErr) {
      console.error("[Edge] Supabase fallback fetch exception:", fbErr);
    }
  }

  // 5. Handle Article Not Found (404)
  if (!article) {
    console.error(`[Edge] Story not found in database: "${slug}"`);
    return new Response("Article not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  // Normalize languages dictionary if PostgREST returned languages->targetLang key
  const targetLangBlock =
    article[`languages->${targetLang}`] ||
    article.languages?.[targetLang] ||
    {};
  if (!article.languages) {
    article.languages = {};
  }
  article.languages[targetLang] = targetLangBlock;

  const levelData = targetLangBlock[activeLevel] || targetLangBlock.A1 || {};
  const activeTitle =
    levelData.title ||
    article.title_translations?.[targetLang] ||
    article.topic ||
    "Leenardo Story";

  // Support language title (for sub-headline)
  const supportLangBlock = article.languages?.[supportLang] || {};
  const supportLevelData = supportLangBlock[activeLevel] || {};
  const supportTitle =
    supportLang !== targetLang
      ? supportLevelData.title ||
        article.title_translations?.[supportLang] ||
        ""
      : "";

  // 6. Fetch base template (article.html) via internal pipeline (context.next())
  let html = "";
  try {
    const templateResp = await context.next();
    if (templateResp && templateResp.ok) {
      html = await templateResp.text();
    } else {
      console.error(`[Edge] context.next() template load returned non-200: ${templateResp?.status}`);
    }
  } catch (tplErr) {
    console.error("[Edge] context.next() template load threw exception:", tplErr);
  }

  // Fallback: If context.next() returned empty or non-200, try same-origin fetch
  if (!html || html.trim() === "") {
    try {
      const originUrl = new URL("/article.html", request.url);
      const directResp = await fetch(originUrl, {
        headers: {
          "Accept": "text/html",
        },
      });
      if (directResp.ok) {
        html = await directResp.text();
      } else {
        console.error(`[Edge] Direct template fetch failed: status ${directResp.status}`);
      }
    } catch (directErr) {
      console.error("[Edge] Direct template fetch exception:", directErr);
    }
  }

  // Strict Guard: Never return 200 with missing or empty template
  if (!html || html.trim() === "") {
    console.error(`[Edge] Fatal: Failed to load article.html template for slug "${slug}"`);
    return new Response("Template error: unable to load page layout", {
      status: 500,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  // 7. Inject localized SEO Metadata & Hreflang Tags
  const metaData = generateArticleMeta({
    article,
    lang: targetLang,
    level: activeLevel,
    slug,
    baseUrl: url.origin,
  });
  html = injectMetaIntoHtml(html, metaData);

  // 8. Inject Server-Rendered Content into editorial HTML placeholders
  // A. Article Headline
  html = html.replace(
    /<h1 class="article-main-title"[^>]*>[\s\S]*?<\/h1>/i,
    `<h1 class="article-main-title" id="article-main-title">${escapeHtml(
      activeTitle
    )}</h1>`
  );

  // B. Article Subtitle / Translation
  html = html.replace(
    /<div class="article-support-title"[^>]*>[\s\S]*?<\/div>/i,
    `<div class="article-support-title" id="article-support-title">${escapeHtml(
      supportTitle
    )}</div>`
  );

  // C. Category Badge
  const catLabel =
    article.category_translations?.[supportLang] ||
    article.category_translations?.en ||
    article.category ||
    "Story";
  html = html.replace(
    /<span class="article-category-tag"[^>]*>[\s\S]*?<\/span>/i,
    `<span class="article-category-tag" id="article-category-badge">${escapeHtml(
      catLabel
    )}</span>`
  );

  // D. Server-render Body Paragraphs for Level
  const paragraphs = levelData.paragraphs || [];
  let renderedParagraphsHtml = "";
  if (Array.isArray(paragraphs) && paragraphs.length > 0) {
    renderedParagraphsHtml = paragraphs
      .map((para: any[], pIdx: number) => {
        if (!Array.isArray(para)) return "";
        const sentencesHtml = para
          .map((sent: any, sIdx: number) => {
            const targetText = sent.target || "";
            const transText =
              sent.translations?.[supportLang] ||
              sent.translations?.en ||
              sent.translations?.tr ||
              "";
            return `<span class="sentence-bubble" data-sentence-index="${pIdx}-${sIdx}" data-translation="${escapeHtml(
              transText
            )}">${escapeHtml(targetText)} </span>`;
          })
          .join("");
        return `<p class="story-paragraph">${sentencesHtml}</p>`;
      })
      .join("\n");
  }

  if (renderedParagraphsHtml) {
    html = html.replace(
      /<div class="article-body-content" id="article-body">[\s\S]*?<\/div>/i,
      `<div class="article-body-content" id="article-body">${renderedParagraphsHtml}</div>`
    );
  }

  // 9. Embed initial article payload for client hydration
  const initialPayloadJson = JSON.stringify(article).replace(/</g, "\\u003c");
  const hydrationScript = `
  <script id="initial-article-data" type="application/json">
    ${initialPayloadJson}
  </script>
  <script>
    window.__INITIAL_ARTICLE__ = JSON.parse(document.getElementById("initial-article-data").textContent);
    window.__INITIAL_TARGET_LANG__ = "${targetLang}";
    window.__INITIAL_ACTIVE_LEVEL__ = "${activeLevel}";
    window.__INITIAL_SUPPORT_LANG__ = "${supportLang}";
  </script>
  `;

  html = html.replace("</body>", `${hydrationScript}\n</body>`);

  // Final Guard: Verify rendered content integrity
  if (!html || html.trim() === "" || !html.includes("article-main-title")) {
    console.error(`[Edge] Fatal: Rendered HTML is corrupted or incomplete for slug "${slug}"`);
    return new Response("Rendering error: incomplete output", {
      status: 500,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  // 10. Return Response with Netlify CDN Layer 1 Edge Caching Headers
  return new Response(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Netlify-CDN-Cache-Control":
        "public, s-maxage=3600, stale-while-revalidate=86400",
      "Netlify-Cache-Tag": `article-${slug},lang-${targetLang}`,
      "Cache-Control": "public, max-age=0, must-revalidate",
    },
  });
}
