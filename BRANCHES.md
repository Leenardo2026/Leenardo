# Branch Registry & Tracking

This file tracks active and historical development branches across the Leenardo repository following the **short-lived branch model**: focused feature/fix branches are branched from `main`, verified, merged, and promptly retired.

---

## Active Branches

| Branch | Owner / Collaborators | Start Date | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| `fix/seo-url-params` | Sencan Yüksel & Antigravity | 2026-10-08 | In Progress | SEO fix package A: remove ?level=/?support=/?target= from generated URLs, default level C1 everywhere, fix level preference loading priority, return 503 on upstream Supabase errors/timeouts, add homepage and lastmod to sitemap, validate categories on draft upload, and update agent docs. |

---

## Reference & Archived Branches

| Branch | Base / Merged Into | Purpose / Scope |
| :--- | :--- | :--- |
| `main` | Production | Live production branch hosting the static deployment. |
| `fix/cleanup-exposed-files` | Merged into `main` (7 Oct 2026) | Block exposed internal files, remove legacy static articles. |
| `feat/phase4-supabase-homepage-admin` | Merged into `main` (5 Oct 2026) | Phase 4: Homepage reads articles from Supabase REST API with 5s timeout, field mapping, and resilient fallback to static JSON / window summary. |
| `feat/phase3-edge-multilingual-urls` | Merged into `main` (3 Oct 2026) | Phase 3: Multilingual clean URLs, edge rendering, dynamic sitemap, SEO tags, saved-words fixes, and account-required saving. |
| `chore/agent-rules` | Merged into `main` (2 Oct 2026) | Add project-level agent rules (GEMINI.md), ignore scratch/ directory, and block security-sensitive files in _redirects. |
| `fix/saved-words-delete-and-tabs` | Merged into `main` (2 Oct 2026) | Fix saved-words delete sync bug and notebook modal tabs overlapping layout across dynamic article.html and 23 static article pages. |
| `feature/supabase-article-architecture` | Merged into `main` (1 Oct 2026) | Migrate articles from static HTML/JSON files to dynamic Supabase database storage with clean URLs and SEO rendering so publishing new stories requires zero Netlify redeploys. |
| `chore/supabase-heartbeat` | Merged into `main` (1 Oct 2026) | Supabase keep-alive cron ping workflow & pre-launch checklist. |
| `feature/media-and-homepage-optimization` | Merged into `main` | Web-optimized image compression (~120KB), lightweight `articles-summary.js` homepage payload, and screenshot cleanup. |
| `feature/multilingual-token-gloss-and-lab` | Merged into `main` | Deep contextual AI glosses for Spanish, Turkish, and German verb fallthrough tokens. |
| `feature/cefr-calibration-and-disclaimers` | Merged into `main` | CEFR progression calibrations and automated linguistic validator pipeline. |
| `v1.0-live-baseline` | Tag / Baseline | Pre-migration static baseline for rollback safety. |
