// ==============================================================================
// Leenardo Netlify Edge Function: Legacy Article Redirects
// Routes: /articles/* and /article.html
// Features: Validates article slug against Supabase, strips .html, resolves
//           target language (default "tr"), preserves level and support query
//           params, and returns 1-hop 301 redirects to /{lang}/articles/{slug}.
//           Unknown slugs return 404 (never redirect to invalid URLs).
// ==============================================================================

import type { Context } from "@netlify/edge-functions";

const DEFAULT_SUPABASE_URL = "https://vkddnvpqnccstcjnqfyq.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY =
  "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-";

const SUPPORTED_LANGUAGES = ["tr", "en", "es", "de", "fr"] as const;
type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

const SUPPORTED_LEVELS = ["A1", "A2", "B1", "B2", "C1"] as const;
type SupportedLevel = (typeof SUPPORTED_LEVELS)[number];

export default async function handler(request: Request, context: Context) {
  const url = new URL(request.url);
  const pathname = url.pathname;

  let rawSlug = "";

  // 1. Resolve slug from path or query parameter
  if (pathname === "/article.html") {
    const queryId = url.searchParams.get("id");
    // If no ?id= param is present (e.g. /article.html#notebook or internal rewrites), passthrough
    if (!queryId || queryId.trim() === "") {
      return context.next();
    }
    rawSlug = queryId.trim();
  } else if (pathname.startsWith("/articles/")) {
    const pathPart = pathname.substring("/articles/".length);
    // Strip trailing .html if present
    rawSlug = pathPart.replace(/\.html$/i, "").trim();
  } else {
    return context.next();
  }

  // Reject empty or invalid slug patterns immediately
  if (!rawSlug || rawSlug === "" || rawSlug.includes("/")) {
    return new Response("Article not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  const slug = decodeURIComponent(rawSlug);

  // 2. Validate slug against Supabase published articles
  const supabaseUrl =
    Deno.env.get("SUPABASE_URL") || DEFAULT_SUPABASE_URL;
  const supabaseAnonKey =
    Deno.env.get("SUPABASE_ANON_KEY") || DEFAULT_SUPABASE_ANON_KEY;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 3000);

  let isPublished = false;

  try {
    const endpoint = `${supabaseUrl}/rest/v1/articles?id=eq.${encodeURIComponent(
      slug
    )}&status=eq.published&hidden=eq.false&select=id`;

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
        isPublished = true;
      }
    } else {
      console.error(`[Legacy Redirect] Supabase check error for "${slug}": status ${resp.status}`);
    }
  } catch (err) {
    clearTimeout(timeoutId);
    console.error(`[Legacy Redirect] Supabase fetch exception for "${slug}":`, err);
  }

  // Unknown or unpublished slug -> 404 (never redirect to an invalid URL)
  if (!isPublished) {
    return new Response("Article not found", {
      status: 404,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  // 3. Resolve target language (defaults to "tr")
  const rawTarget = (
    url.searchParams.get("target") ||
    url.searchParams.get("lang") ||
    "tr"
  ).toLowerCase();

  const targetLang: SupportedLanguage = SUPPORTED_LANGUAGES.includes(
    rawTarget as SupportedLanguage
  )
    ? (rawTarget as SupportedLanguage)
    : "tr";

  // 4. Preserve optional level and support query parameters
  const redirectParams = new URLSearchParams();

  const queryLevel = (url.searchParams.get("level") || "").toUpperCase();
  if (SUPPORTED_LEVELS.includes(queryLevel as SupportedLevel)) {
    redirectParams.set("level", queryLevel);
  }

  const querySupport = (url.searchParams.get("support") || "").toLowerCase();
  if (SUPPORTED_LANGUAGES.includes(querySupport as SupportedLanguage)) {
    redirectParams.set("support", querySupport);
  }

  const qs = redirectParams.toString() ? `?${redirectParams.toString()}` : "";
  const destination = `/${targetLang}/articles/${encodeURIComponent(slug)}${qs}`;

  // 5. Strict safety guard: never emit ":" placeholders or "undefined" in Location header
  if (destination.includes(":") || destination.includes("undefined")) {
    console.error(`[Legacy Redirect] Fatal: Refusing to emit invalid Location "${destination}"`);
    return new Response("Internal redirect error", {
      status: 500,
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      },
    });
  }

  // 6. Return 1-hop 301 Permanent Redirect
  return new Response(null, {
    status: 301,
    headers: {
      Location: destination,
      "Cache-Control": "public, max-age=3600, must-revalidate",
      "Netlify-CDN-Cache-Control": "public, s-maxage=86400, must-revalidate",
    },
  });
}
