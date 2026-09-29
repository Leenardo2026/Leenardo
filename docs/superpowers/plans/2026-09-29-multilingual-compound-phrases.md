# Multilingual Compound & Noun Phrase Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a generic, safe multi-word compound & noun phrase detection engine in `article.html` that automatically detects compounds across all 5 languages (e.g. *taze fasulye*, *elma suyu*, *zumo de naranja*, *green beans*) while strictly preventing false positives.

**Architecture:** A 3-layer architecture:
1. `harvestVocabPhrases(targetData, targetLang)` dynamically harvests multi-word entries from the article's own vocabulary list.
2. `detectContextualUnit(cleanTokens, clickedIdx, lang)` evaluates static phrase registry first, then applies language-specific safe grammatical rules (safe head nouns for TR, `de/del` chains for ES, `de/d'/à` chains for FR, modifier+noun for EN/DE).
3. `handleWordClick` highlights all constituent words in the multi-word span (`spanGroup`) and renders the full phrase in the popover with component breakdown.

**Tech Stack:** Vanilla JavaScript (ES6+), Unicode Regex (`\p{L}`), DOM API, HTML5/CSS3.

## Global Constraints
- Target branch: work on `feature/multilingual-compound-phrases`.
- Zero false positives: Verbs, pronouns, and clause boundaries must never be conjoined.
- Single Source of Truth: update `article.html`, then synchronize all 23 static pages via `generate_article_pages.py` and validate via `validate_content.py`.

---

### Task 1: Safe Grammatical Rules & Language-Specific Stemmers

**Files:**
- Modify: `article.html` (inside `<script>` block around line 5280)

**Interfaces:**
- Produces:
  - `SAFE_HEAD_NOUNS_TR`: Set of valid head nouns in Turkish noun compounds.
  - `SAFE_ADJECTIVES_TR`: Set of common culinary/descriptive adjectives.
  - `stemToken(word, lang)`: Language-aware stemmer/normalizer.
  - `detectRuleBasedCompound(cleanTokens, clickedIdx, lang)`: Returns `{ type: "compound", phrase, startIdx, endIdx, data }` or `null`.

- [ ] **Step 1: Define safe grammatical sets in `article.html`**
  Add `SAFE_HEAD_NOUNS_TR` (liquids, botany, vessels, civic, eras) and `SAFE_ADJECTIVES_TR`. Add connector rules for ES (`de/del`), FR (`de/d'/à`), EN (adjacent nouns/adj).
- [ ] **Step 2: Implement `detectRuleBasedCompound`**
  Checks index bounds, ensures no punctuation/stopwords in-between, checks if adjacent tokens match legitimate patterns (e.g., `[word] + [safe_head_noun]` in TR, or `[noun] + de + [noun]` in ES).
- [ ] **Step 3: Integrate with `detectContextualUnit`**
  If `MULTILINGUAL_PHRASE_REGISTRY` doesn't match, invoke `detectRuleBasedCompound`.

---

### Task 2: Dynamic Vocab Harvester (`harvestVocabPhrases`)

**Files:**
- Modify: `article.html` (inside `renderArticleContent`)

**Interfaces:**
- Produces: `harvestVocabPhrases(targetData, targetLang)`
  - Returns array of dynamic phrase registry items derived from `targetData.vocab` where word count >= 2.
- Integrates with `detectContextualUnit` as the first-priority lookup.

- [ ] **Step 1: Write `harvestVocabPhrases(targetData, targetLang)`**
  Extract multi-word terms from `targetData.vocab`, format them with `stemSequence` and `translations`.
- [ ] **Step 2: Store `currentVocabPhrases` on level change**
  When rendering article content, initialize `currentVocabPhrases = harvestVocabPhrases(targetData, targetLang)`.
- [ ] **Step 3: Check `currentVocabPhrases` inside `detectContextualUnit`**

---

### Task 3: Multi-Word UI Popover & Component Breakdown

**Files:**
- Modify: `article.html` (inside `handleWordClick` around line 5350)

**Interfaces:**
- Consumes: `detectedUnit` with `type: "phrase"` or `type: "compound"`.
- Produces: Highlighted `spanGroup`, popover title with full phrase, grammatical category badge, and component decomposition.

- [ ] **Step 1: Update popover rendering for rule-based compounds**
  If phrase translation is not in registry, construct fallback translation or search in active sentence translation.
- [ ] **Step 2: Add component breakdown label in popover**
  Display `elma (isim) + suyu (tamlanan)` or `fresh (adj) + green beans (noun)`.
- [ ] **Step 3: Ensure "Save Word" saves the complete multi-word phrase**
  Ensure clicking "Save Word" in the popover saves `"taze fasulye"` or `"elma suyu"` rather than just one token.

---

### Task 4: Static Site Generation & Synchronization

**Files:**
- Modify: `articles/*.html`
- Execute: `python3 generate_article_pages.py`
- Execute: `python3 validate_content.py`

- [ ] **Step 1: Run `generate_article_pages.py`**
  Regenerate all 23 static pages with the upgraded compound detection engine.
- [ ] **Step 2: Run `validate_content.py`**
  Verify 100% data integrity and pipeline health.

---

### Task 5: Interactive Verification & Feature Branch Commit

**Files:**
- Git branch: `feature/multilingual-compound-phrases`

- [ ] **Step 1: Test Turkish compounds**
  Verify clicking "taze" or "fasulye" in Aegean Olive Oil article selects both.
  Verify test compound like "zeytin ağacı", "çay bardağı" selects both.
  Verify unrelated words like "eve gitti" do NOT join.
- [ ] **Step 2: Commit feature branch**
