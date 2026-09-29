# Design Specification: Multilingual Safe Compound & Noun Phrase Engine

- **Date:** 2026-09-29
- **Author:** Leenardo Team
- **Status:** Approved / Ready for Implementation Plan
- **Scope:** `article.html`, `articles/*.html`, `generate_article_pages.py`

---

## 1. Objective & Philosophy

Enable effortless, context-aware click-to-translate for **multi-word compound phrases and noun collocations** across all 5 languages (TR, EN, ES, DE, FR), while **strictly preventing false positives** (unrelated words like subject-verb, verb-object, or clause boundaries must never be incorrectly bound together).

Example legitimate pairs:
- **TR:** *taze fasulye*, *elma suyu*, *portakal suyu*, *zeytin ağacı*, *çay bardağı*, *yeraltı şehri*, *altın tozu*
- **EN:** *green beans*, *apple juice*, *orange juice*, *olive tree*, *tea glass*, *underground city*
- **ES:** *judías verdes*, *zumo de manzana*, *zumo de naranja*, *árbol de olivo*, *ciudad subterránea*
- **FR:** *haricots verts*, *jus de pomme*, *jus d'orange*, *arbre à olives*, *cité souterraine*
- **DE:** *grüne Bohnen*, *Apfelsaft*, *Orangensaft*, *unterirdische Stadt*

---

## 2. Three-Tier False-Positive Prevention Architecture

To guarantee that arbitrary adjacent words are **never** erroneously joined, the detection engine applies three strict validation gates:

### Gate 1: Safe Head Noun & Structural Patterns (By Language)

1. **Turkish (TR):**
   - **Safe Belirtisiz İsim Tamlaması Heads:**
     - *Liquids/Foods:* `suyu`, `çayı`, `kahvesi`, `sütü`, `yağı`, `çorbası`, `reçeli`, `salatası`, `yemeği`
     - *Botany/Nature:* `ağacı`, `yaprağı`, `dalı`, `çiçeği`, `tohumu`, `kökü`, `meyvesi`, `kabuğu`, `bahçesi`, `ormanı`, `dağı`, `vadisi`, `gölü`, `denizi`, `kıyısı`, `toprağı`
     - *Vessels/Craft:* `bardağı`, `fincanı`, `kaşığı`, `tabağı`, `kasesi`, `şişesi`, `kutusu`, `tozu`, `teli`, `sandığı`
     - *Structures/Civic:* `şehri`, `sarayı`, `kalesi`, `kapısı`, `sokağı`, `meydanı`, `odası`, `evi`, `merkezi`
     - *Cultural/Eras:* `çağı`, `dönemi`, `yüzyılı`, `geleneği`, `ozanı`, `sanatı`, `akımı`
   - **Safe Adjective Modifiers:**
     - High-frequency culinary & descriptive adjectives: `taze`, `kuru`, `sıcak`, `soğuk`, `yeşil`, `mavi`, `kara`, `ak`, `büyük`, `küçük`, `eski`, `yeni`, `ince`, `tatlı`, `acı`.
   - **Terminal Suffix Tolerance:** Suffixes appended to the head noun (e.g. *elma suyu-na*, *çam ağacı-nda*, *taze fasulye-yi*) are recognized via Turkish stemmer.

2. **Spanish (ES):**
   - Pattern: `[Noun] + "de" / "del" + [Noun]` (e.g. *zumo de manzana*, *aceite de oliva*, *árbol de higo*).
   - Pattern: `[Noun] + [Descriptive Adj]` (e.g. *judías verdes*, *café turco*, *ciudad subterránea*).
   - Non-nouns (verbs, pronouns, adverbs) are rejected.

3. **French (FR):**
   - Pattern: `[Noun] + "de" / "d'" / "à" + [Noun]` (e.g. *jus de pomme*, *jus d'orange*, *huile d'olive*, *cuillère à café*).
   - Pattern: `[Noun] + [Descriptive Adj]` (e.g. *haricots verts*, *ville souterraine*).

4. **English (EN):**
   - Pattern: `[Safe Modifier] + [Noun]` (e.g. *fresh beans*, *green beans*, *apple juice*, *olive oil*, *tea glass*).
   - Plural `-s/-es` tolerance on head.

5. **German (DE):**
   - Adjective declension stripping (`-e, -en, -er, -es, -em`) + Noun (e.g. *grüne(n) Bohnen*, *unterirdische(n) Stadt*).
   - Single-word compounds (*Apfelsaft*, *Orangensaft*) are annotated with component breakdowns.

### Gate 2: Stopwords & Punctuation Boundary Filter
- Conjunctions (*ve, ama, fakat, pero, y, et, mais, and, but, oder, und*), pronouns, demonstratives, and auxiliary verbs are **strictly excluded** from forming phrase spans.
- Any sentence punctuation (commas, semicolons, quotes, dashes, colons) instantly breaks phrase candidacy.

### Gate 3: Dynamic Vocab Harvester (`harvestVocabPhrases`)
- At runtime, every multi-word term present in the article's `languages[lang][level].vocab` list is automatically registered as a high-confidence phrase unit with pre-translated definitions.

---

## 3. Runtime User Interaction & Visual State

1. **Hover / Interaction:** Clicking on *any* token of an active phrase:
   - Evaluates `detectContextualUnit(cleanWords, clickedIdx, targetLang)`.
   - Locates `[startIdx ... endIdx]`.
   - Highlights the complete multi-word span simultaneously via `.active-word`.
2. **Popover Display:**
   - **Title:** The full phrase (e.g. *elma suyu* or *zumo de manzana*).
   - **Type / Badge:** "İsim / Sıfat Tamlaması" / "Noun Phrase" / "Sintagma Nominal".
   - **Translation:** Full phrase translation from the phrase registry or dynamically constructed via component alignment.
   - **Components:** Breakdown of parts (e.g. *elma (isim) + suyu (tamlanan isim)*).
   - **Save to Vocabulary:** Saves the full compound phrase to the reader's vocabulary notebook.

---

## 4. Implementation Steps
1. Implement `detectContextualUnit` enhancements with safe head noun sets and multi-language rules in `article.html`.
2. Add `harvestVocabPhrases` to register all multi-word vocabulary items dynamically from current article level data.
3. Expand `MULTILINGUAL_PHRASE_REGISTRY` with common culinary, nature, and cultural compounds.
4. Regenerate all 23 static pages via `python3 generate_article_pages.py`.
5. Run `python3 validate_content.py` to ensure pipeline consistency.
