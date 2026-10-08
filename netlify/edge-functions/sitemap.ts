// ==============================================================================
// Leenardo Netlify Edge Function: Dynamic Sitemap Generator
// Route: /sitemap.xml
// Features: Queries Supabase for published article IDs, renders 115 localized
//           article URLs (23 articles × 5 languages) with hreflang alternates
//           and x-default (/en/), cached for 1 hour on Netlify Edge CDN.
// ==============================================================================

import type { Context } from "@netlify/edge-functions";

const DEFAULT_SUPABASE_URL = "https://vkddnvpqnccstcjnqfyq.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY =
  "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-";

const BASE_URL = "https://leenardo.com";
const SUPPORTED_LANGUAGES = ["tr", "en", "es", "de", "fr"] as const;
type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];
const X_DEFAULT_LANG: SupportedLanguage = "en";

export interface ArticleRecord {
  id: string;
  updated_at?: string;
}

export function formatW3CDate(dateStr?: string): string | null {
  if (!dateStr) return null;
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    return d.toISOString();
  } catch {
    return null;
  }
}

export function buildSitemapXml(articles: ArticleRecord[]): string {
  const xmlHeader = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n';
  const xmlFooter = "</urlset>\n";

  const urlBlocks: string[] = [];

  // Find latest updated_at among articles for homepage lastmod
  let latestUpdated: string | null = null;
  for (const art of articles) {
    if (art.updated_at) {
      const formatted = formatW3CDate(art.updated_at);
      if (formatted && (!latestUpdated || formatted > latestUpdated)) {
        latestUpdated = formatted;
      }
    }
  }

  // 1. Homepage URL
  const homeLastmod = latestUpdated ? `\n    <lastmod>${latestUpdated}</lastmod>` : "";
  urlBlocks.push(`  <url>\n    <loc>${BASE_URL}/</loc>${homeLastmod}\n  </url>`);

  // 2. Localized article URLs with alternate hreflang tags and lastmod
  for (const art of articles) {
    if (!art.id) continue;
    const slug = encodeURIComponent(art.id.trim());
    const lastmodTag = formatW3CDate(art.updated_at);
    const lastmodLine = lastmodTag ? `\n    <lastmod>${lastmodTag}</lastmod>` : "";

    for (const lang of SUPPORTED_LANGUAGES) {
      const loc = `${BASE_URL}/${lang}/articles/${slug}`;
      const alternateTags = SUPPORTED_LANGUAGES.map(
        (altLang) =>
          `    <xhtml:link rel="alternate" hreflang="${altLang}" href="${BASE_URL}/${altLang}/articles/${slug}" />`
      ).join("\n");
      const xDefaultTag = `    <xhtml:link rel="alternate" hreflang="x-default" href="${BASE_URL}/${X_DEFAULT_LANG}/articles/${slug}" />`;

      urlBlocks.push(
        `  <url>\n    <loc>${loc}</loc>${lastmodLine}\n${alternateTags}\n${xDefaultTag}\n  </url>`
      );
    }
  }

  return xmlHeader + urlBlocks.join("\n") + "\n" + xmlFooter;
}

export default async function handler(request: Request, _context: Context) {
  console.log(`[Edge Sitemap] Incoming request: ${request.method} ${request.url}`);

  const supabaseUrl =
    Deno.env.get("SUPABASE_URL") || DEFAULT_SUPABASE_URL;
  const supabaseAnonKey =
    Deno.env.get("SUPABASE_ANON_KEY") || DEFAULT_SUPABASE_ANON_KEY;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  let articles: ArticleRecord[] = [];

  try {
    // PostgREST query: fetch only published, non-hidden article IDs and updated_at
    const endpoint = `${supabaseUrl}/rest/v1/articles?status=eq.published&hidden=eq.false&select=id,updated_at&order=id.asc`;

    const resp = await fetch(endpoint, {
      signal: controller.signal,
      headers: {
        apikey: supabaseAnonKey,
        Accept: "application/json",
      },
    });

    clearTimeout(timeoutId);

    if (!resp.ok) {
      console.error(`[Edge Sitemap] Supabase REST error: HTTP ${resp.status}`);
      return new Response("Error fetching articles from database", {
        status: 502,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-store",
        },
      });
    }

    const data = await resp.json();
    if (!Array.isArray(data)) {
      console.error("[Edge Sitemap] Supabase response is not an array:", data);
      return new Response("Invalid data format received from database", {
        status: 502,
        headers: {
          "Content-Type": "text/plain; charset=utf-8",
          "Cache-Control": "no-store",
        },
      });
    }

    articles = data;
  } catch (err) {
    clearTimeout(timeoutId);
    console.error("[Edge Sitemap] Supabase fetch exception:", err);
    return new Response("Service unavailable while retrieving sitemap", {
      status: 503,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  const sitemapXml = buildSitemapXml(articles);

  // Return XML with Netlify Edge CDN caching: 1 hour edge cache, revalidate
  return new Response(sitemapXml, {
    status: 200,
    headers: {
      "Content-Type": "application/xml; charset=utf-8",
      "Netlify-CDN-Cache-Control":
        "public, s-maxage=3600, stale-while-revalidate=86400",
      "Netlify-Cache-Tag": "sitemap",
      "Cache-Control": "public, max-age=0, must-revalidate",
    },
  });
}
