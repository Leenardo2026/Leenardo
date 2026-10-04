#!/usr/bin/env node
/**
 * scripts/upload_drafts.mjs
 * 
 * Uploads draft articles to Supabase as the draft writer user.
 * Node 24+, zero external dependencies (built-in fetch only).
 * 
 * Usage:
 *   node --env-file=.env scripts/upload_drafts.mjs <file.json> [--confirm]
 * 
 * RLS Requirements:
 *   - Inserts must have status='draft'
 *   - Uses user access token from Supabase Auth
 *   - Uses Prefer: return=minimal header to prevent PostgREST SELECT
 */

import fs from "node:fs";
import path from "node:path";

// Supabase configuration matching supabase-client.js
const SUPABASE_URL = process.env.SUPABASE_URL || "https://vkddnvpqnccstcjnqfyq.supabase.co";
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY || "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-";

/**
 * Extracts a lightweight summary for homepage / preview feeds.
 * Matches python migrate_articles_to_supabase.py build_article_summary.
 */
function buildArticleSummary(art) {
  const sumLangs = {};
  if (art && art.languages && typeof art.languages === "object") {
    for (const [lang, levels] of Object.entries(art.languages)) {
      sumLangs[lang] = {};
      if (levels && typeof levels === "object") {
        for (const [lvl, data] of Object.entries(levels)) {
          const lvlItem = {
            title: data?.title || "",
            grammarDesc: data?.grammarDesc || ""
          };
          const paras = data?.paragraphs || [];
          if (Array.isArray(paras) && paras.length > 0 && Array.isArray(paras[0])) {
            lvlItem.paragraphs = [
              paras[0]
                .filter(s => s && typeof s === "object")
                .map(s => ({ target: s.target || "" }))
            ];
          }
          sumLangs[lang][lvl] = lvlItem;
        }
      }
    }
  }
  return sumLangs;
}

/**
 * Prepares the Supabase articles table row payload.
 * Ensures status is strictly 'draft' for RLS policy compliance.
 */
function prepareDraftRow(art) {
  const titleTranslations = { ...(art.titleTranslations || {}) };
  const titleTr = art.titleTr || titleTranslations.tr || "";
  const titleEn = art.titleEn || titleTranslations.en || "";

  if (titleTr && !titleTranslations.tr) titleTranslations.tr = titleTr;
  if (titleEn && !titleTranslations.en) titleTranslations.en = titleEn;

  // Fallback title translations from languages structure if missing
  if (art.languages && typeof art.languages === "object") {
    for (const [lang, levels] of Object.entries(art.languages)) {
      if (!titleTranslations[lang] && levels && typeof levels === "object") {
        const firstLevel = Object.values(levels)[0];
        if (firstLevel?.title) {
          titleTranslations[lang] = firstLevel.title;
        }
      }
    }
  }

  return {
    id: art.id,
    topic: art.topic || "",
    category: art.category || "",
    category_translations: art.categoryTranslations || {},
    title_tr: titleTr,
    title_en: titleEn,
    title_translations: titleTranslations,
    teaser: art.teaser || null,
    teaser_translations: art.teaserTranslations || {},
    visual: art.visual || {},
    read_time: art.readTime || "3 min read",
    languages: art.languages || {},
    summary: buildArticleSummary(art),
    status: "draft", // Strictly 'draft' to satisfy draft writer RLS policy
    hidden: Boolean(art.hidden)
  };
}

const REQUIRED_LANGUAGES = ["tr", "en", "es", "de", "fr"];
const REQUIRED_LEVELS = ["A1", "A2", "B1", "B2", "C1"];
const TURKISH_CHARS_REGEX = /[ğĞşŞıİ]/;

/**
 * Extracts distinct Turkish-specific characters found in a string.
 */
function matchTurkishChars(str) {
  if (!str || typeof str !== "string") return "";
  const found = str.match(/[ğĞşŞıİ]/g);
  return found ? [...new Set(found)].join("") : "";
}

/**
 * Validates article list adhering to strict content and schema rules:
 *   a) All 5 languages (tr, en, es, de, fr) x 5 levels (A1, A2, B1, B2, C1) present; title and paragraphs non-empty
 *   b) IDs unique within the file
 *   c) Turkish letters (ğ, ş, ı, İ) inside quiz of en/es/de/fr
 *   d) Comprehension questions without translations / invalid text
 */
function validateArticles(articles) {
  const errors = [];
  const seenIds = new Map();

  for (let idx = 0; idx < articles.length; idx++) {
    const art = articles[idx];
    const prefix = `Article #${idx + 1}${art?.id ? ` (${art.id})` : ""}`;

    if (!art || typeof art !== "object") {
      errors.push(`${prefix}: Must be an object.`);
      continue;
    }

    // Required top-level fields
    if (!art.id || typeof art.id !== "string" || !art.id.trim()) {
      errors.push(`${prefix} id: Missing or invalid 'id'.`);
    } else {
      // b) IDs unique within the file
      if (seenIds.has(art.id)) {
        errors.push(`${art.id} id: Duplicate article ID found in input file (first defined at article #${seenIds.get(art.id) + 1}).`);
      } else {
        seenIds.set(art.id, idx);
      }
    }

    if (!art.category || typeof art.category !== "string" || !art.category.trim()) {
      errors.push(`${prefix} category: Missing or invalid 'category'.`);
    }
    if (!art.topic || typeof art.topic !== "string" || !art.topic.trim()) {
      errors.push(`${prefix} topic: Missing or invalid 'topic'.`);
    }

    const artId = art.id || `article_${idx + 1}`;
    const langs = art.languages;
    if (!langs || typeof langs !== "object") {
      errors.push(`${artId} languages: Missing or invalid 'languages' dictionary.`);
      continue;
    }

    // a) All 5 languages x 5 levels present, title and paragraphs non-empty
    for (const lang of REQUIRED_LANGUAGES) {
      if (!langs[lang] || typeof langs[lang] !== "object") {
        errors.push(`${artId} [${lang}]: missing required language.`);
        continue;
      }

      for (const lvl of REQUIRED_LEVELS) {
        const lvlData = langs[lang][lvl];
        if (!lvlData || typeof lvlData !== "object") {
          errors.push(`${artId} [${lang}][${lvl}]: missing required level.`);
          continue;
        }

        // a) Title non-empty
        if (!lvlData.title || typeof lvlData.title !== "string" || !lvlData.title.trim()) {
          errors.push(`${artId} [${lang}][${lvl}].title: empty or missing title.`);
        }

        // a) Paragraphs non-empty
        if (!Array.isArray(lvlData.paragraphs) || lvlData.paragraphs.length === 0) {
          errors.push(`${artId} [${lang}][${lvl}].paragraphs: empty or missing paragraphs array.`);
        } else {
          const hasValidSentence = lvlData.paragraphs.some(
            p => Array.isArray(p) && p.length > 0 && p.some(s => s && typeof s === "object" && s.target && s.target.trim())
          );
          if (!hasValidSentence) {
            errors.push(`${artId} [${lang}][${lvl}].paragraphs: no non-empty sentence target text found.`);
          }
        }

        // c) Turkish letters ğ ş ı İ inside quiz of en/es/de/fr
        if (lang !== "tr" && Array.isArray(lvlData.quiz)) {
          lvlData.quiz.forEach((q, qIdx) => {
            if (!q || typeof q !== "object") return;
            if (q.question && TURKISH_CHARS_REGEX.test(q.question)) {
              errors.push(`${artId} [${lang}][${lvl}] quiz[${qIdx}].question: contains Turkish characters (${matchTurkishChars(q.question)}) in non-TR quiz.`);
            }
            if (q.explanation && TURKISH_CHARS_REGEX.test(q.explanation)) {
              errors.push(`${artId} [${lang}][${lvl}] quiz[${qIdx}].explanation: contains Turkish characters (${matchTurkishChars(q.explanation)}) in non-TR quiz.`);
            }
            if (Array.isArray(q.options)) {
              q.options.forEach((opt, optIdx) => {
                if (typeof opt === "string" && TURKISH_CHARS_REGEX.test(opt)) {
                  errors.push(`${artId} [${lang}][${lvl}] quiz[${qIdx}].options[${optIdx}]: contains Turkish characters (${matchTurkishChars(opt)}) in non-TR quiz.`);
                }
              });
            }
          });
        }

        // d) Comprehension questions without translations / invalid text
        if (Array.isArray(lvlData.qa)) {
          lvlData.qa.forEach((qa, qaIdx) => {
            if (!qa || typeof qa !== "object") return;
            const qText = qa.q || qa.question || "";
            const aText = qa.a || qa.answer || "";
            if (!qText.trim()) {
              errors.push(`${artId} [${lang}][${lvl}] qa[${qaIdx}].question: empty or missing question text.`);
            }
            if (!aText.trim()) {
              errors.push(`${artId} [${lang}][${lvl}] qa[${qaIdx}].answer: empty or missing answer text.`);
            }

            // Untranslated Turkish comprehension questions in non-TR:
            if (lang !== "tr") {
              const hasTrChars = TURKISH_CHARS_REGEX.test(qText) || TURKISH_CHARS_REGEX.test(aText);
              if (hasTrChars) {
                const transObj = qa.translations && typeof qa.translations === "object" ? qa.translations[lang] : null;
                const hasTargetTrans = transObj && (transObj.q || transObj.question);
                if (!hasTargetTrans) {
                  errors.push(`${artId} [${lang}][${lvl}] qa[${qaIdx}]: untranslated comprehension question (contains Turkish characters in ${lang} without target translation).`);
                }
              }
            }

            // If translations dictionary is provided, ensure it is non-empty
            if (qa.translations !== undefined) {
              if (!qa.translations || typeof qa.translations !== "object" || Object.keys(qa.translations).length === 0) {
                errors.push(`${artId} [${lang}][${lvl}] qa[${qaIdx}].translations: translations property exists but is empty.`);
              }
            }
          });
        }
      }
    }
  }

  return errors;
}

/**
 * Main execution routine.
 */
async function main() {
  const args = process.argv.slice(2);
  const isConfirm = args.includes("--confirm");
  const fileArg = args.find(a => !a.startsWith("--"));

  if (!fileArg) {
    console.error("❌ Error: Missing input file.\n");
    console.log("Usage:");
    console.log("  node --env-file=.env scripts/upload_drafts.mjs <file.json> [--confirm]\n");
    console.log("Options:");
    console.log("  <file.json>    Path to JSON file containing article(s) in articles.json shape");
    console.log("  --confirm      Execute actual upload to Supabase (without this, runs in dry-run mode)");
    process.exit(1);
  }

  const filePath = path.resolve(process.cwd(), fileArg);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ Error: Input file not found at "${filePath}"`);
    process.exit(1);
  }

  let fileContent = "";
  try {
    fileContent = fs.readFileSync(filePath, "utf-8");
  } catch (err) {
    console.error(`❌ Error reading file "${filePath}": ${err.message}`);
    process.exit(1);
  }

  let parsed = null;
  try {
    parsed = JSON.parse(fileContent);
  } catch (err) {
    console.error(`❌ Error: Invalid JSON in "${filePath}": ${err.message}`);
    process.exit(1);
  }

  const rawArticles = Array.isArray(parsed) ? parsed : [parsed];
  if (rawArticles.length === 0) {
    console.error(`❌ Error: File "${filePath}" contains an empty list of articles.`);
    process.exit(1);
  }

  console.log("=================================================================");
  console.log("💎 LEENARDO SUPABASE DRAFT UPLOADER");
  console.log("=================================================================");
  console.log(`Input File:  ${fileArg} (${rawArticles.length} article${rawArticles.length > 1 ? "s" : ""})`);
  console.log(`Endpoint:    ${SUPABASE_URL}`);
  console.log(`Mode:        ${isConfirm ? "LIVE UPLOAD (--confirm)" : "DRY RUN (preview only)"}`);
  console.log("-----------------------------------------------------------------");

  // Validate all articles against content architecture rules
  const allErrors = validateArticles(rawArticles);

  if (allErrors.length > 0) {
    console.error("❌ Validation errors found in input articles:");
    allErrors.forEach(e => console.error(`   - ${e}`));
    console.error("\nUpload aborted. Please fix the input JSON and try again.");
    process.exit(1);
  }

  // Display summary of articles
  rawArticles.forEach((art, idx) => {
    const langs = art.languages ? Object.keys(art.languages) : [];
    const sampleLang = langs[0];
    const levels = sampleLang && art.languages[sampleLang] ? Object.keys(art.languages[sampleLang]) : [];
    console.log(`[${idx + 1}/${rawArticles.length}] ID: ${art.id}`);
    console.log(`      Topic:      ${art.topic}`);
    console.log(`      Category:   ${art.category}`);
    console.log(`      Languages:  ${langs.join(", ")} (Levels: ${levels.join(", ")})`);
  });

  console.log("-----------------------------------------------------------------");

  // If dry-run, stop here
  if (!isConfirm) {
    console.log("✅ Validation successful. All articles passed schema checks.");
    console.log("🔍 DRY RUN MODE: No data was written to Supabase.");
    console.log("\nTo upload these drafts to Supabase, run with the --confirm flag:");
    console.log(`   node --env-file=.env scripts/upload_drafts.mjs ${fileArg} --confirm\n`);
    process.exit(0);
  }

  // Confirm mode: verify credentials
  const email = process.env.DRAFT_WRITER_EMAIL;
  const password = process.env.DRAFT_WRITER_PASSWORD;

  if (!email || !password) {
    console.error("❌ Error: Missing credentials in environment.");
    console.error("   DRAFT_WRITER_EMAIL and DRAFT_WRITER_PASSWORD must be set.");
    console.error("   Ensure your .env file exists and run with: node --env-file=.env ...");
    process.exit(1);
  }

  // Authenticate as draft writer user
  console.log("Authenticating as draft writer...");
  let accessToken = null;
  let userEmail = "";

  try {
    const authRes = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password })
    });

    if (!authRes.ok) {
      const errJson = await authRes.json().catch(() => ({}));
      const msg = errJson.error_description || errJson.message || errJson.error || `HTTP ${authRes.status}`;
      console.error(`❌ Authentication failed: ${msg}`);
      process.exit(1);
    }

    const authData = await authRes.json();
    accessToken = authData.access_token;
    userEmail = authData.user?.email || "authenticated user";

    if (!accessToken) {
      console.error("❌ Authentication failed: No access token in response.");
      process.exit(1);
    }
  } catch (err) {
    console.error(`❌ Authentication request failed: ${err.message}`);
    process.exit(1);
  }

  console.log(`✓ Authenticated successfully as ${userEmail}.`);
  console.log("Uploading draft(s)...");

  let successCount = 0;
  let failCount = 0;

  for (let idx = 0; idx < rawArticles.length; idx++) {
    const art = rawArticles[idx];
    const row = prepareDraftRow(art);
    const label = `[${idx + 1}/${rawArticles.length}] ${row.id}`;

    try {
      // POST to rest/v1/articles with user token and Prefer: return=minimal
      // RLS policy permits INSERT only when auth.uid() matches and status='draft'
      const res = await fetch(`${SUPABASE_URL}/rest/v1/articles`, {
        method: "POST",
        headers: {
          "apikey": SUPABASE_ANON_KEY,
          "Authorization": `Bearer ${accessToken}`,
          "Content-Type": "application/json",
          "Prefer": "return=minimal"
        },
        body: JSON.stringify(row)
      });

      if (res.status === 201 || res.status === 200) {
        console.log(`  ✓ ${label} uploaded successfully.`);
        successCount++;
      } else {
        const errText = await res.text().catch(() => "");
        console.error(`  ❌ ${label} failed: HTTP ${res.status} ${errText}`);
        failCount++;
      }
    } catch (err) {
      console.error(`  ❌ ${label} network error: ${err.message}`);
      failCount++;
    }
  }

  console.log("-----------------------------------------------------------------");
  console.log(`Upload finished: ${successCount} succeeded, ${failCount} failed.`);
  console.log("=================================================================");

  if (failCount > 0) {
    process.exit(1);
  }
}

main().catch(err => {
  console.error("Unhandled exception:", err.message);
  process.exit(1);
});
