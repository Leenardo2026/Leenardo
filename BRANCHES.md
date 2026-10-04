# Branch Registry & Tracking

This file tracks active and historical development branches across the Leenardo repository to keep track of work in progress, assignees, and branch purposes.

---

## Active Branches

| Branch | Owner / Collaborators | Start Date | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| `chore/supabase-heartbeat` | Sencan Yüksel | 2026-10-01 | Merged into main | Keep Supabase free-tier project from pausing via scheduled GitHub Actions curl ping to the articles endpoint. |
| `feature/supabase-article-architecture` | Sencan Yüksel & Antigravity | 2026-10-01 | Merged into main | Migrate articles from static HTML/JSON files to dynamic Supabase database storage with clean URLs and SEO rendering so publishing new stories requires zero Netlify redeploys. |
| `fix/saved-words-delete-and-tabs` | Sencan Yüksel & Antigravity | 2026-10-02 | Merged into main (2 Oct 2026) | Fix saved-words delete sync bug (confirm deletion in Supabase before UI removal) and fix notebook modal tabs overlapping/nested layout. |
| `chore/agent-rules` | Sencan Yüksel & Antigravity | 2026-10-02 | Merged into main | Add project-level agent rules (GEMINI.md), ignore scratch/ directory, and block security-sensitive files in _redirects. |
| `feat/phase3-edge-multilingual-urls` | Sencan Yüksel & Antigravity | 2026-10-02 | Merged into main (3 Oct 2026) | Phase 3: Edge-rendered multilingual article routes (/{lang}/articles/{slug}), Netlify Edge Function with Deno, metadata engine, client-side reader hydration, SEO tags, saved-words fixes, and account-required saving. |
| `feat/phase4-supabase-homepage-admin` | Sencan Yüksel | 2026-10-05 | Merged into main (5 Oct 2026) | Phase 4: Homepage reads articles from Supabase REST API with 5s timeout, field mapping, and resilient fallback to static JSON / window summary. |

---

## Reference & Archived Branches

| Branch | Base / Merged Into | Purpose / Scope |
| :--- | :--- | :--- |
| `main` | Production | Live production branch hosting the static deployment. |
| `feat/phase3-edge-multilingual-urls` | Merged into `main` (3 Oct 2026) | Multilingual clean URLs, edge rendering, dynamic sitemap, SEO tags, saved-words fixes, and account-required saving. |
| `fix/saved-words-delete-and-tabs` | Merged into `main` (2 Oct 2026) | Fix saved-words delete sync bug and notebook modal tabs overlapping layout across dynamic article.html and 23 static article pages. |
| `chore/supabase-heartbeat` | Merged into `main` | Supabase keep-alive cron ping workflow & pre-launch checklist. |
| `feature/media-and-homepage-optimization` | Merged into `main` | Web-optimized image compression (~120KB), lightweight `articles-summary.js` homepage payload, and screenshot cleanup. |
| `feature/multilingual-token-gloss-and-lab` | Merged into `main` | Deep contextual AI glosses for Spanish, Turkish, and German verb fallthrough tokens. |
| `feature/cefr-calibration-and-disclaimers` | Merged into `main` | CEFR progression calibrations and automated linguistic validator pipeline. |
| `v1.0-live-baseline` | Tag / Baseline | Pre-migration static baseline for rollback safety. |
