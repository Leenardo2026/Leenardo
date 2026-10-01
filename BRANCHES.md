# Branch Registry & Tracking

This file tracks active and historical development branches across the Leenardo repository to keep track of work in progress, assignees, and branch purposes.

---

## Active Branches

| Branch | Owner / Collaborators | Start Date | Status | Description |
| :--- | :--- | :--- | :--- | :--- |
| `feature/supabase-article-architecture` | Sencan Yüksel & Antigravity | 2026-10-01 | Phase 2 (Dynamic Reader) | Migrate articles from static HTML/JSON files to dynamic Supabase database storage with clean URLs and SEO rendering so publishing new stories requires zero Netlify redeploys. |

---

## Reference & Archived Branches

| Branch | Base / Merged Into | Purpose / Scope |
| :--- | :--- | :--- |
| `main` | Production | Live production branch hosting the static deployment. |
| `feature/media-and-homepage-optimization` | Merged into `main` | Web-optimized image compression (~120KB), lightweight `articles-summary.js` homepage payload, and screenshot cleanup. |
| `feature/multilingual-token-gloss-and-lab` | Merged into `main` | Deep contextual AI glosses for Spanish, Turkish, and German verb fallthrough tokens. |
| `feature/cefr-calibration-and-disclaimers` | Merged into `main` | CEFR progression calibrations and automated linguistic validator pipeline. |
| `v1.0-live-baseline` | Tag / Baseline | Pre-migration static baseline for rollback safety. |
