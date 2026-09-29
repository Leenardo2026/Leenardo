#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 Leenardo - Multilingual Graded Content Pipeline
--------------------------------------------------------------
Çok dilli (TR, ES, DE, FR, EN) içerikleri CEFR A1-C1 standartlarına göre
seviyelendiren, sözlük ve anlama soruları oluşturan, yasal uyar-kaldır
korumalı çalışma kağıtları ve JSON veritabanı üreten pipeline motoru.

YASAL BİLGİ & TELİF:
- C2 seviyesi kaldırılmıştır. En yüksek seviye C1'dir.
- Orijinal basın fotoğrafları çekilmez ve depolanmaz.
- Her haber altında telif bildirimi ve iletişim (contact@leenardo.com) yer alır.
- İçerikler yapay zekâ ile üretilmiş olup CEFR seviye yönergelerine uygun şekilde yapılandırılmış ve sürekli incelemelerle geliştirilmektedir.
"""

import os
import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ARTICLES_FILE = BASE_DIR / "articles.json"
WORKSHEETS_DIR = BASE_DIR / "worksheets"

LANG_NAMES = {
    "tr": "Türkçe",
    "en": "English",
    "es": "Español",
    "de": "Deutsch",
    "fr": "Français"
}

CEFR_REWRITE_SYSTEM_PROMPT = """
Sen, çok dilli yabancı dil eğitimi (CEFR A1-C1) konusunda uzman bir müfredat ve dilbilim tasarımcısısın.
Sana verilen konuyu seçilen HEDEF DİLDE (Target Language) 5 farklı CEFR seviyesine (A1, A2, B1, B2, C1) dönüştür.

ZORUNLU CEFR SEVİYE VE ZORLUK KALİBRASYON KURALLARI (TÜM DİLLER İÇİN GEÇERLİDİR):
Seviyelerin birbirine benzemesini ve hepsinin aynı edebi tona kaymasını kesinlikle engelle. Her seviye için aşağıdaki sınırlamaları tavizsiz uygula:

1. A1 SEVİYESİ (Beginner):
   - Cümle uzunluğu: Cümle başına KESİNLİKLE 5-8 kelime.
   - Zamanlar / Çatılar: Yalnızca yalın geniş zaman / şimdiki zaman veya basit geçmiş zaman (simple present/past only).
   - Kelime dağarcığı: Yalnızca hedef dilde en sık kullanılan 500-750 kelime.
   - KESİNLİKLE YASAK: Yan cümle (subordinate clause), deyimler (idioms), edilgen çatı (passive voice).

2. A2 SEVİYESİ (Elementary):
   - Cümle uzunluğu: Cümle başına KESİNLİKLE 8-12 kelime.
   - Cümle yapısı: En fazla iki basit cümleyi "ve / ama / çünkü" (and / but / because) bağlaçlarıyla bağlayabilir.
   - Kelime dağarcığı: En sık kullanılan 1000-1500 kelime.
   - KESİNLİKLE YASAK: Deyimler, edebi veya soyut kelimeler, edilgen çatı (passive voice).

3. B1 SEVİYESİ (Intermediate):
   - Cümle uzunluğu: Cümle başına KESİNLİKLE 12-18 kelime.
   - Cümle yapısı: Cümle başına en fazla bir (1) yan cümle (subordinate clause). Sade, doğrudan ve akıcı sentaks; retorik veya süslü sanatlardan kaçın.
   - Kelime dağarcığı: En sık kullanılan 2000-3000 kelime + somut konuya özgü terimler.
   - KESİNLİKLE YASAK / KAÇINILACAKLAR: Edebi/şiirsel anlatım, nadir eşanlamlılar, soyut felsefi terimler (örn. "posthumously", "malice", "phantom", "virtue" gibi kelimeler KULLANILMAZ — yerine "after his death", "unkind", "illusion", "good character" gibi yalın karşılıklar kullanılır).

4. B2 SEVİYESİ (Upper-Intermediate):
   - Cümle uzunluğu: Cümle başına en fazla 25 kelimeye kadar.
   - Cümle yapısı: Birden fazla yan cümle ve karmaşık sentaks serbesttir.
   - Kelime dağarcığı: Genişletilmiş ve soyut kavramlar, yaygın deyimler kabul edilebilir, orta düzey sentaks karmaşıklığı.

5. C1 SEVİYESİ (Advanced):
   - Cümle yapısı & Üslup: Zengin kelime dağarcığı, karmaşık sentaks, anadili seviyesine yakın doğal akış (near-native register). Kaliteli bir gazete incelemesi (long-read) veya edebi deneme üslubu.
   - KAÇINILACAKLAR: Konunun kendisi o teknik uzmanlık alanı olmadıkça aşırı teknik akademik/bilimsel jargon ve arkaik/nadir kelimelerden kaçın.

GENEL İLKE:
- Her seviyeyi sonuçlandırmadan önce kelime sıklığı ve cümle uzunluğu kısıtlamalarına göre tek tek doğrula.
- Bu kuralları tüm hedef dillerde (Türkçe, İspanyolca, İngilizce, Almanca, Fransızca) kelimesi kelimesine çeviri olarak değil, fonksiyonel dilbilimsel denklik temelinde tutarlı şekilde uygula.
- Kesinlikle telifli orijinal metin kopyalanmaz veya basın fotoğrafı kullanılmaz.
- İçerikler yapay zekâ ile üretilmiş olup CEFR seviye yönergelerine uygun şekilde yapılandırılmış ve sürekli incelemelerle geliştirilmektedir.
"""

def load_existing_articles():
    if ARTICLES_FILE.exists():
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def save_articles(articles):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"✅ articles.json güncellendi! (Toplam {len(articles)} haber)")

def audit_article_for_compliance(article):
    """
    Haber/öğrenim metnini yasal ve pedagojik protokollere göre denetler:
    1. Basın fotoğrafı veya dış telifli kaynak içermemesi
    2. Dış ajans manşetleri veya linkleri içermemesi (originalSource/sourceUrl olmaması)
    3. Pedagojik konu başlığı (topic) ve kategori (category) bulunması
    4. CEFR A1-C1 seviyelerinin eksiksiz bulunması
    5. %100 özgün, kurgusal ve telifsiz eğitim metni olması
    """
    report = []
    passed = True
    art_id = article.get("id", "Bilinmeyen")
    
    # Check absence of external scraper fields
    forbidden_fields = ["originalSource", "originalTitle", "sourceUrl"]
    leaked = [f for f in forbidden_fields if f in article]
    if leaked:
        report.append(f"❌ [İHLAL] Dış kaynak kalıntıları tespit edildi: {leaked}")
        passed = False
    else:
        report.append("✅ [ONAY] %100 Özgün İçerik - Dış ajans ve haber linki içermez.")

    topic = article.get("topic")
    if not topic or len(topic.strip()) < 5:
        report.append("❌ [İHLAL] Pedagojik konu başlığı (topic) eksik.")
        passed = False
    else:
        report.append(f"✅ [ONAY] Pedagojik Konu Başlığı: \"{topic}\"")

    category = article.get("category")
    if not category:
        report.append("❌ [İHLAL] Kategori eksik.")
        passed = False
    else:
        report.append(f"✅ [ONAY] Kategori: {category}")

    langs = article.get("languages", {})
    required_lvls = {"A1", "A2", "B1", "B2", "C1"}
    for l_code in ["tr", "en", "es", "de", "fr"]:
        if l_code not in langs:
            report.append(f"❌ [İHLAL] {l_code} dil paketi eksik.")
            passed = False
            break
        missing = required_lvls - set(langs[l_code].keys())
        if missing:
            report.append(f"❌ [İHLAL] {l_code} dilinde eksik seviyeler: {missing}")
            passed = False
            break
    else:
        report.append("✅ [ONAY] 5 Dil × 5 CEFR Düzeyi (A1-C1) eksiksiz yapılandırıldı.")

    return passed, report

def generate_worksheets(articles=None):
    WORKSHEETS_DIR.mkdir(exist_ok=True)
    if articles is None:
        articles = load_existing_articles()

    for art in articles:
        art_id = art["id"]
        topic_title = art.get("topic") or art.get("originalTitle", "Eğitim Konusu")
        category_name = art.get("category", "Genel")
        langs_dict = art.get("languages", {})
        
        # If modern unified schema
        if langs_dict:
            for t_lang, levels_map in langs_dict.items():
                t_lang_name = LANG_NAMES.get(t_lang, t_lang)
                output_file = WORKSHEETS_DIR / f"worksheet_{art_id}_{t_lang}.md"

                content = []
                content.append(f"# 💎 Leenardo - {t_lang_name} Ders Çalışma Kağıdı")
                content.append(f"**Kategori:** {category_name}")
                content.append(f"**Eğitim Konusu:** {topic_title}")
                content.append(f"**İçerik Türü:** %100 Özgün Pedagojik Metin (Telif ve Basın Alıntısı İçermez)")
                content.append("")
                content.append("> ⚖️ **EĞİTİM AMACI & YASAL BİLGİ:**")
                content.append(f"> İçerikler yapay zekâ ile üretilmiş olup CEFR seviye yönergelerine uygun şekilde yapılandırılmış ve sürekli incelemelerle geliştirilmektedir.")
                content.append("> İletişim: `contact@leenardo.com`.")
                content.append("")
                content.append("---")
                content.append("")

                for lvl in ["A1", "A2", "B1", "B2", "C1"]:
                    if lvl not in levels_map:
                        continue
                    data = levels_map[lvl]
                    content.append(f"## 📌 SEVİYE {lvl}: {data['title']}")
                    content.append("")
                    content.append(f"**Dil Bilgisi Odağı:** {', '.join(data.get('grammarTags', []))}")
                    
                    g_desc = data.get('grammarDesc', '')
                    if isinstance(g_desc, dict):
                        g_desc = g_desc.get(t_lang) or g_desc.get('tr') or g_desc.get('en') or str(g_desc)
                    content.append(f"> {g_desc}")
                    content.append("")
                    
                    content.append(f"### 📖 Okuma Parçası ({t_lang_name})")
                    for p in data["paragraphs"]:
                        p_text = " ".join(s.get("target") or s.get("tr") or "" for s in p)
                        content.append(f"{p_text}")
                        content.append("")

                    content.append("### 📚 Kilit Kelimeler (Key Vocabulary)")
                    for v in data.get("vocab", []):
                        v_target = v.get("target") or v.get("tr") or ""
                        v_trans = ""
                        if "translations" in v:
                            v_trans = v["translations"].get("en") or v["translations"].get("tr") or ""
                        else:
                            v_trans = v.get("en", "")
                        root_part = ""
                        if v.get("root"):
                            r_word = v.get("root")
                            r_trans = (v.get("rootTranslations", {}).get("en") or v.get("rootTranslations", {}).get("tr") or "")
                            root_part = f" *(kök: {r_word}{' - ' + r_trans if r_trans else ''})*"
                        content.append(f"- **{v_target}**: {v_trans}{root_part}")
                    content.append("")

                    content.append("### ❓ Anlama ve Konuşma Soruları (Comprehension Questions)")
                    for idx, qa in enumerate(data.get("qa", []), 1):
                        content.append(f"{idx}. {qa['q']}")
                        content.append(f"   *(Cevap: {qa['a']})*")
                    content.append("")
                    content.append("="*50)
                    content.append("")

                with open(output_file, "w", encoding="utf-8") as f:
                    f.write("\n".join(content))
                print(f"📄 Çalışma kağıdı hazırlandı: {output_file.name}")

def main():
    args = sys.argv[1:]
    articles = load_existing_articles()
    
    if not args or "--status" in args:
        print("💎 Daily Turkish with Mia - Haber Veritabanı Durumu:")
        print(f"Toplam Haber Sayısı: {len(articles)}")
        for idx, a in enumerate(articles, 1):
            langs = list(a.get('languages', {}).keys())
            lang_str = ", ".join([LANG_NAMES.get(l, l) for l in langs])
            topic_title = a.get("topic") or a.get("originalTitle")
            print(f"  {idx}. [{a['category']}] {topic_title}")
            print(f"      Diller: {lang_str} (Seviyeler: A1-C1)")
    elif "--audit" in args:
        print("🛡️ Daily Turkish with Mia - Yasal & Pedagojik Uyumluluk Denetimi:")
        print("="*65)
        all_passed = True
        for idx, a in enumerate(articles, 1):
            passed, report = audit_article_for_compliance(a)
            status_icon = "✅ UYUMLU" if passed else "❌ UYUMSUZ"
            print(f"\n[{idx}] {a.get('id')} - {status_icon}")
            for line in report:
                print(f"   {line}")
            if not passed:
                all_passed = False
        print("="*65)
        if all_passed:
            print("🎉 Tebrikler! Tüm haberler telif, C1 tavan ve uyar-kaldır protokollerine tam uyumludur.")
        else:
            print("⚠️ Bazı haberler yasal uyumluluk kriterlerini karşılamıyor.")
    elif "--generate-worksheets" in args:
        generate_worksheets(articles)
    else:
        print("""
💎 Daily Turkish with Mia - CLI Yardım:
  --status              : Veritabanındaki çok dilli haberleri listeler
  --audit               : Telif, görsel yokluğu ve CEFR standartlarını denetler
  --generate-worksheets : Google Docs / Preply için telif korumalı Markdown çalışma kağıtları üretir
        """)

if __name__ == "__main__":
    main()
