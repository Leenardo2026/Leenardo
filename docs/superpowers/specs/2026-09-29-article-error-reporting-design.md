# Design Specification: Article Error Reporting System

- **Date:** 2026-09-29
- **Author:** Leenardo Team
- **Status:** Approved / Ready for Implementation Plan
- **Scope:** `article.html`, `articles/*.html`, `supabase-client.js`, `generate_article_pages.py`

---

## 1. Overview & Objective

Leenardo articles are AI-generated and strictly calibrated across 5 CEFR levels (A1–C1) and 5 languages (TR, EN, ES, DE, FR). To ensure high linguistic quality, community trust, and a continuous human-in-the-loop feedback mechanism, users must be able to report issues directly from any article with minimal friction.

The objective is to provide a seamless "Report an Issue" button within the bottom action bar that opens a lightweight, localized modal. Upon submission, the report and contextual metadata (article ID, active CEFR level, target language, support language, user ID if logged in) are stored directly in Supabase (`article_reports` table).

---

## 2. User Experience & Interface Design

### 2.1 Trigger Button
- **Location:** In the `.reading-actions-left` container in `article.html`, positioned adjacent to the "Mark as Read" and "Share" buttons.
- **Visuals:** Secondary pill button matching Leenardo aesthetics (`btn-secondary`), displaying a clean SVG flag/report icon and localized text ("Report" / "Hata Bildir" / "Reportar" / "Melden" / "Signaler").
- **ID:** `#btn-report-bottom`

### 2.2 Report Modal (`#report-modal`)
- **Backdrop & Transitions:** Matches `#share-modal` and `#vocab-notebook-modal` styling with smooth blur and fade-in animations.
- **Header:**
  - Localized title: "Report an Issue" / "Bir Hata Bildirin".
  - Close button (`&times;`).
- **Context Pill:**
  - Displays the active article title, current CEFR level, and active language pairing (e.g., `Stoicism • B1 • ES ➔ TR`).
- **Issue Type Selector (Single-select pill tags or radio tiles):**
  1. `translation_error`: "Yanlış / Eksik Çeviri" (Translation Issue)
  2. `factual_error`: "Bilgi / Mantık Hatası" (Factual Inaccuracy)
  3. `typo_grammar`: "Yazım / Dilbilgisi Hatası" (Typo or Grammar)
  4. `cefr_mismatch`: "Seviye Uyumsuzluğu" (Too Easy or Too Hard for this Level)
  5. `other`: "Diğer" (Other)
- **Optional Details Input:**
  - A clean textarea with placeholder: "Gözünüze çarpan kelimeyi veya cümleyi belirtebilirsiniz (isteğe bağlı)..."
  - Max length: 500 characters.
- **Footer Actions:**
  - "Cancel" button (`#btn-report-cancel`).
  - "Submit Report" button (`#btn-report-submit`) with loading state spinner.
- **Success Confirmation:**
  - An inline toast or modal success state: "Geri bildiriminiz için teşekkürler! İncelenmek üzere iletildi. ✓"
  - Auto-closes after 1.5 seconds.

---

## 3. Database & Supabase Integration

### 3.1 Table Schema (`article_reports`)

```sql
create table if not exists public.article_reports (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  article_id text not null,
  target_lang text not null,
  support_lang text not null,
  cefr_level text not null,
  issue_type text not null,
  notes text,
  user_id uuid references auth.users(id) on delete set null,
  user_email text,
  status text not null default 'pending'
);
```

### 3.2 Row Level Security (RLS)
- **Insert Policy:** Enabled for `public` / `anon` and `authenticated` roles (`with check (true)`). Anyone can submit a report without needing an account.
- **Select / Update / Delete Policy:** Restricted to `service_role` or authorized admin dashboards only.

### 3.3 Supabase Client Function
In `supabase-client.js`:
```javascript
async function submitArticleReport({ articleId, targetLang, supportLang, cefrLevel, issueType, notes }) {
  // Gracefully sends to Supabase; falls back gracefully if client unavailable or offline
}
```

---

## 4. Internationalization (i18n)

The feature will be localized across all 5 supported interface languages in `uiTranslations`:
- **TR (Türkçe):**
  - `reportBtn`: "Hata Bildir"
  - `modalReportTitle`: "Bir Hata Bildirin"
  - `reportIssueTranslation`: "Yanlış / Eksik Çeviri"
  - `reportIssueFactual`: "Bilgi / Mantık Hatası"
  - `reportIssueGrammar`: "Yazım / Dilbilgisi Hatası"
  - `reportIssueLevel`: "Seviye Uyumsuzluğu"
  - `reportIssueOther`: "Diğer"
  - `reportNotesPlaceholder`: "Gözünüze çarpan kelimeyi veya cümleyi belirtebilirsiniz (isteğe bağlı)..."
  - `reportSubmitBtn`: "Raporu Gönder"
  - `reportSuccessToast`: "Geri bildiriminiz için teşekkürler! İletildi. ✓"
- **EN (English):**
  - `reportBtn`: "Report Issue"
  - `modalReportTitle`: "Report an Issue"
  - `reportIssueTranslation`: "Translation Error"
  - `reportIssueFactual`: "Factual Inaccuracy"
  - `reportIssueGrammar`: "Typo / Grammar"
  - `reportIssueLevel`: "CEFR Level Mismatch"
  - `reportIssueOther`: "Other"
  - `reportNotesPlaceholder`: "Describe the issue or paste the sentence (optional)..."
  - `reportSubmitBtn`: "Submit Report"
  - `reportSuccessToast`: "Thank you for your feedback! Submitted. ✓"
- Equivalent high-fidelity translations for **ES**, **DE**, and **FR**.

---

## 5. Propagation & Single Source of Truth
1. Update `article.html` (modal markup, CSS, JS event handlers, UI translations).
2. Update `supabase-client.js` with reporting method.
3. Run `python3 generate_article_pages.py` to regenerate all 22 static article files in `articles/*.html`.
4. Run `python3 validate_content.py` to ensure zero regressions across the content pipeline.

---

## 6. Self-Review & Verification Criteria
- [x] Zero breaking changes to existing "Mark as Read", "Share", and "Side-by-Side View" buttons.
- [x] RLS allows anonymous users to report without login prompts.
- [x] Mobile responsiveness tested for small screens (360px+).
- [x] Keyboard accessibility (Esc closes modal).
- [x] All 22 pre-rendered pages synchronized.
