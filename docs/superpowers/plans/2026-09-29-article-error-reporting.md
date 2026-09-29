# Article Error Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a frictionless, multilingual "Report an Issue" feature on all Leenardo articles that captures user reports with automatic article/CEFR/language context and sends them directly to Supabase.

**Architecture:** A secondary action button (`#btn-report-bottom`) in the reading action bar triggers an accessible modal (`#report-modal`). The modal lets users select an issue type via pills and add optional notes. On submit, `supabase-client.js` asynchronously inserts the payload into the `article_reports` table, providing immediate visual feedback without interrupting the reading experience.

**Tech Stack:** Vanilla JavaScript (ES6+), HTML5, CSS3 with Leenardo custom CSS variables, Supabase JS SDK (PostgreSQL + RLS).

## Global Constraints
- Target branch: work on `feature/article-error-reporting` (do not commit directly to `main` until reviewed).
- 100% responsive: must display properly on mobile (360px) and desktop.
- 5 Languages: all UI copy in the modal and button must be localized across TR, EN, ES, DE, FR.
- Single Source of Truth: update `article.html` then compile all static files in `articles/*.html` via `generate_article_pages.py`.

---

### Task 1: Supabase Schema & Client API

**Files:**
- Create: `supabase/migrations/20260929_article_reports.sql`
- Modify: `supabase-client.js`

**Interfaces:**
- Produces: `window.LeenardoReports = { submitArticleReport(payload) }`
  - Input: `{ articleId: string, targetLang: string, supportLang: string, cefrLevel: string, issueType: string, notes: string }`
  - Returns: `{ success: boolean, data?: object, error?: string }`

- [ ] **Step 1: Create SQL migration file for `article_reports`**
  Write table schema with columns: `id`, `created_at`, `article_id`, `target_lang`, `support_lang`, `cefr_level`, `issue_type`, `notes`, `user_id`, `user_email`, `status`. Include public insert RLS policy.
- [ ] **Step 2: Add `submitArticleReport` method to `supabase-client.js`**
  Implement safe insertion to Supabase `article_reports`. Handle anonymous reporting gracefully with error catching.
- [ ] **Step 3: Verify client method exists and behaves gracefully in local environment**

---

### Task 2: UI Markup & Styling in `article.html`

**Files:**
- Modify: `article.html` (CSS styles and HTML body)

**Interfaces:**
- Consumes: Leenardo CSS design tokens (`--bg-surface`, `--ink-navy`, `--brand-coral`, `--brand-purple-light`, `--divider-hairline`)
- Produces:
  - Button `#btn-report-bottom` in `.reading-actions-left`
  - Modal `#report-modal` with pill selection and textarea

- [ ] **Step 1: Add "Hata Bildir" button in `.reading-actions-left`**
  Place button with flag SVG icon next to `#btn-share-bottom`.
- [ ] **Step 2: Add `#report-modal` HTML structure**
  Add modal container with backdrop, header, context badge (`#report-context-badge`), issue pill buttons (`#report-issue-options`), textarea (`#report-notes`), and action buttons ("Cancel", "Submit").
- [ ] **Step 3: Add CSS styling for modal and pills**
  Style `.modal-report-box`, `.report-pills`, `.report-pill.active`, `.report-textarea`, `.report-context-pill`. Ensure smooth animations matching Leenardo modals.

---

### Task 3: JavaScript Logic & Multilingual Localization

**Files:**
- Modify: `article.html` (JavaScript script block)

**Interfaces:**
- Consumes: `window.LeenardoReports.submitArticleReport`, active global state (`currentArticleId`, `targetLang`, `supportLang`, `currentLevel`)
- Produces: `openReportModal()`, `closeReportModal()`, `selectReportIssue(type)`, `submitReportAction()`

- [ ] **Step 1: Add localization keys to `uiTranslations`**
  Add keys for `tr`, `en`, `es`, `de`, `fr` for:
  - `reportBtn`
  - `modalReportTitle`
  - `reportContextLabel`
  - `reportIssueTranslation`
  - `reportIssueFactual`
  - `reportIssueGrammar`
  - `reportIssueLevel`
  - `reportIssueOther`
  - `reportNotesPlaceholder`
  - `reportCancelBtn`
  - `reportSubmitBtn`
  - `reportSending`
  - `reportSuccessToast`
  - `reportErrorToast`
- [ ] **Step 2: Implement modal open/close & state management**
  Show current article title, level, and language in the context badge when opening. Reset form fields on close. Add `Escape` key close handling.
- [ ] **Step 3: Implement submit action with validation & loading indicator**
  Ensure at least one issue pill is selected. Call `submitArticleReport`. Display success toast and auto-close modal.

---

### Task 4: Static Site Generation & Synchronization

**Files:**
- Modify: `articles/*.html` (via script)
- Execute: `python3 generate_article_pages.py`
- Execute: `python3 validate_content.py`

- [ ] **Step 1: Run `generate_article_pages.py`**
  Verify all 22 static HTML pages in `articles/` receive the updated modal and button markup.
- [ ] **Step 2: Run `validate_content.py`**
  Verify zero regressions in content validation pipeline.

---

### Task 5: Verification & Branch Commit

**Files:**
- Git branch: `feature/article-error-reporting`

- [ ] **Step 1: Check interactive behavior in browser**
  Verify modal open, pill selection, typing notes, closing via button/backdrop/Escape, and language switching.
- [ ] **Step 2: Commit changes to `feature/article-error-reporting`**
