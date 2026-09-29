# 💎 Leenardo — Project Status & Memory Guide

> **Son Güncelleme:** 28 Eylül 2026  
> **Canlı Adres:** [https://leenardo.com](https://leenardo.com)  
> **GitHub Deposu:** [https://github.com/Leenardo2026/Leenardo](https://github.com/Leenardo2026/Leenardo)

---

## 📌 1. Proje Özeti
**Leenardo**, dil öğrenenler için seviyelendirilmiş (A1–C2 CEFR) haber ve makaleler sunan, okurken bilinmeyen kelimelerin kaydedilip pratik yapılabildiği interaktif bir çok dilli öğrenme platformudur.

---

## 🏗️ 2. Canlı Altyapı ve Sistem Mimarisi

* **Domain & DNS:** Porkbun (`leenardo.com` & `www.leenardo.com`).
  * A Kaydı: `75.2.60.5` (Netlify)
  * CNAME: `magenta-phoenix-d78774.netlify.app`
* **Hosting & Dağıtım:** Netlify (Global CDN, ücretsiz otomatik Let's Encrypt SSL sertifikası).
  * GitHub ile sürekli entegrasyon (Continuous Deployment) aktiftir. `main` dalına kod gittiğinde Netlify 5 saniyede canlıyı günceller.
* **Backend & Veritabanı:** Supabase (PostgreSQL + Auth).
  * Project Ref: `vkddnvpqnccstcjnqfyq`
  * Tablo: `public.saved_words` (RLS kurallarıyla korumalı; kullanıcı sadece kendi kelimelerini okuyabilir, ekleyebilir, silebilir).
* **Frontend:** Vanilla HTML5, modern CSS3 (`auth.css`), saf JavaScript (`supabase-client.js`, `auth-ui.js`, `articles-data.js`). Hiçbir hantal framework bağımlılığı yoktur, ışık hızında çalışır.
* **Tasarım Sistemi:** Editorial Magazine Minimalism (Sanzo Wada Renk Paleti: Gündüz için #263 paleti — Krem `#F5F2EC`, Mürekkep Lacivert `#1B3644`, Şeftali Vurgusu `#F2AD78`, Tuğla Kırmızısı `#A93400`, Nötr Gri `#8A8A8A`, 1px saç çizgisi ayraçlar `#E0DDD6`; Gece modu için Sanzo Wada gece paleti — Gece İndigo `#122129`, Yüzey `#192C37`, Kart `#1F3441`, Fildişi/Ekru `#F0ECE1`, Sis Grisi `#889DA8`, Sıcak Şeftali `#F2AD78`, Benitobi Kırmızısı `#C44D23`, Saç çizgisi `#243B48`. `border-radius: 0`, gölgesiz düz editoryal yüzeyler, Fraunces serif ve Inter tipografi).

---

## 🛡️ 3. Altın Çalışma Kurallarımız (Yapay Zekâ ve Ekip İçin)

1. **Kullanıcı Onayı Olmadan Canlıya Asla Gönderme:**
   * Yapılan her değişiklik önce kullanıcının bilgisayarında test edilir.
   * Kullanıcı açıkça *"Beğendim, canlıya gönder"* demediği sürece kod GitHub'a (`git push`) atılmaz.
2. **Büyük Değişikliklerde Güvenlik Dalı (Git Branch) Aç:**
   * Tasarım, kod yapısı veya büyük bir özellik geliştirilirken `main` dalında doğrudan çalışılmaz; yeni bir dal (branch) açılır.
   * İlk çalışan canlı sürüm `v1.0-live-baseline` dalı ve `v1.0-live` etiketiyle kalıcı olarak yedeklenmiştir.
3. **Ekip Çalışması Kuralı:**
   * İki ortak uzaktan çalışırken güne başlarken `git pull` yapılır.
4. **Bu Dosyayı Güncel Tut:**
   * Her büyük özellik veya altyapı değişikliği tamamlandığında bu dosya (`PROJECT_STATUS.md`) güncellenir.
5. **Prompt Dili Kuralı (MANDATORY):**
   * Yapay zekâya, görsel üretim araçlarına ve oturum geçişlerine verilen tüm promptlar her zaman **İngilizce (English)** yazılır.
6. **Ticari Lisans, Telif ve Ücretli API Güvencesi Kuralı (MANDATORY & CRITICAL):**
   * Yapılan her güncellemede, eklenen her kütüphane, görsel, yazı tipi, ses veya API entegrasyonunda ticari lisans ve borçlanma riski mutlaka denetlenir.
   * Asla habersiz ücretli/kotalı üçüncü taraf API (ElevenLabs, OpenAI, Cloud TTS vb.) veya telif hakkı kısıtlı materyal (stok fotoğraf, basından ham metin vb.) sisteme eklenemez.
   * Herhangi bir ticari lisans ihlali veya borçlanma tehlikesi tespit edilirse **İŞLEM DERHAL DURDURULUR** ve kullanıcıya haber verilir.
7. **Çıktı & Yanıt Verimliliği (Concise Outputs):**
   * Açıklamaları öz ve kısa tut; oturum içinde daha önce açıklananları tekrarlama.
   * Tamamlanan ve doğrulanmış değişiklikleri tekrar özetleme/açıklama; kısaca onay bildir.
   * Değişmesi gerekmeyen dosyaları gereksiz yere baştan üretme veya üzerine yazma.
8. **Netlify Dağıtım & Kredi Tasarrufu (Branch-First Development):**
   * Tasarım ve içerik geliştirmeleri her zaman ayrı bir git dalında (`branch`) yapılır; asla doğrudan `main` dalına push edilmez.
   * Sadece kullanıcı toplu değişikliklerden memnun olduğunu açıkça onayladığında `main` dalına merge/push yapılır (Netlify ücretli deploy kredisi tüketimini önlemek için). Küçük veya tekil ince ayarlar için asla otomatik deploy önerilmez/yapılmaz.
9. **Supabase 7 Günlük Uyku (Auto-Pause) Takibi:**
   * Projeye birkaç gün işlem yapılmadığında, ücretsiz Supabase projesinin uykuya (pause) geçmesini önlemek için kullanıcıya dashboard'u kontrol etmesi hatırlatılır.
10. **GitHub Depo Hafifliği & Medya Yönetimi:**
    * Git reposuna doğrudan büyük resim/medya dosyaları commit edilmez; mümkün oldukça Supabase Storage kullanılır.
11. **Risk ve Limit Ön-Bildirimi (Pre-Action Flagging):**
    * Herhangi bir işlem bu limitleri (büyük deploy, büyük dosya commit, uzun inaktivite) aşma riski taşıyorsa otomatik ilerlemeden önce kullanıcıya bayrak kaldırılır.

---

## ✅ 4. Tamamlanan Aşamalar

* [x] `leenardo.com` alan adı satın alındı ve Porkbun DNS yönlendirmesi yapıldı.
* [x] Netlify hosting hesabı kuruldu ve GitHub ile tam otomatik dağıtım bağlandı.
* [x] Supabase projesi oluşturuldu, `saved_words` SQL tablosu ve RLS güvenlik kuralları yazıldı.
* [x] Kullanıcı kimlik doğrulama sistemi (Kayıt ol, Giriş yap, Şifremi unuttum, Çıkış yap) kodlandı ve arayüze entegre edildi.
* [x] Okuma sayfasında kelimeleri buluta (Supabase) kaydetme ve profil kelime defteri senkronizasyonu bağlandı.
* [x] Misafir kullanıcıların giriş yapmadan kaydettiği kelimelerin giriş anında hesaba otomatik aktarılması sağlandı.
* [x] Platformun adı resmi olarak her yerde **"Leenardo"** olarak güncellendi ve canlıya alındı.
* [x] Güvenlik yedekleme dalı (`v1.0-live-baseline`) ve etiketi (`v1.0-live`) oluşturuldu.
* [x] **Arayüz Yenilemesi (Editorial Magazine Minimalism):** `index.html`, `article.html` ve `auth.css` dosyalarında Sanzo Wada #263 paleti, Fraunces serif başlıklar, düz saç çizgisi bölücüler ve sıfır border-radius tasarımı uygulandı; tüm emojiler temizlendi ve işlevsellik (dil, seviye, kelime kaydetme, auth, arama) eksiksiz korundu.
* [x] **Okundu Takibi & Akıllı "Surprise Me":** Makaleleri okundu olarak işaretleme (`Mark as Read`), ana sayfa ve tavsiye kartlarında zarif `✓ Okundu` rozeti gösterimi ve `Surprise Me` butonunun okunmamış hikayeleri önceliklendirmesi sağlandı.
* [x] **Makale Paylaşım Özelliği:** Makale üstü ve altında yer alan editoryal paylaş butonuyla mobilde yerel sistem paylaşımı (`Web Share API`), masaüstünde ise tek tıkla panoya kopyalama ve anlık toast bildirimi eklendi.
* [x] **Sanzo Wada Gece Modu (Dark Mode):** Sanzo Wada geleneksel renk paletlerinden ilham alan (Kuro-Aizome gece indigosu, fildişi ekru tipografi, yumuşak şeftali vurgusu) editoryal gece modu eklendi. FOUC önleyici satır içi komut dosyası, `localStorage` ve sistem tema tercihi (`prefers-color-scheme`) algılama, 5 dilde (TR/EN/ES/DE/FR) yerelleştirilmiş zarif tipografik buton tasarımı sağlandı.
* [x] **Bağlamsal Token-Gloss Mimarisi (Contextual Token-Gloss Architecture — 5 Dilin Tamamı Tamamlandı):**
  * Tıklanan kelimelerde izole canlı API çağrısı yerine, cümlenin dilbilgisel bağlamını koruyan önceden üretilmiş morfolojik token-gloss sistemi (`sentObj.tokens`) kuruldu.
  * `article.html` popover motoru güncellendi: Önce `sentObj.tokens` bağlamsal sözlüğü taranır; bulunamazsa arka planda `[Gloss Miss]` uyarısı vererek mevcut canlı Google Translate motoruna güvenle düşer (`fallback`).
  * Ayrı olan ders kelime listesi (`levelData.vocab` / flashcard) tamamen bağımsız ve izole tutuldu.
  * **5 Dilin Tamamı Üretildi (3.120 Cümle, 44.604 Kelime):**
    * **Türkçe (TR):** 624 cümle, 7.862 token (eklemeli morfoloji, sıfat-fiiller, ek-fiiller).
    * **İngilizce (EN):** 624 cümle, 9.296 token (öbeksi fiiller / phrasal verbs, homograflar, kısaltmalar).
    * **İspanyolca (ES):** 624 cümle, 9.611 token (bitişik klitik zamirler, gerundio/infinitivo ekleri, dar/del daralmaları).
    * **Almanca (DE):** 624 cümle, 8.319 token (ayrılabilen fiiller / trennbare Verben, birleşik isimler / Komposita).
    * **Fransızca (FR):** 624 cümle, 9.516 token (elizyon / kesme işareti ayrıştırmaları, kaynaşmış edatlar au/du/des).
  * **Tek Doğruluk Kaynağı & Doğrulama:** `articles-data.js` (8.8 MB) senkronize edildi, `validate_content.py` 575 permütasyonun tamamını 0 hata ile doğruladı.
  * **Yayın Kapısı Kuralı:** Kullanıcı açık onay vermeden asla `git push` veya yayına alma yapılmaz!

---

## 🎯 5. Sırada Bekleyen Geliştirme Başlıkları

1. **Canlıya Alma Onayı (Deployment Gate):**
   * Yapılan 5 dilli token-gloss mimarisinin yerel test sonuçlarının kullanıcıya sunulması ve onay alındıktan sonra `main` dalına commit/push yapılması.
2. **Kelime Pekiştirme & Quiz Modülü:**
   * Kaydedilen kelimelerle aralıklı tekrar (spaced repetition / flashcard) ve çoktan seçmeli anlama testleri.
3. **Otomasyon & Günlük İçerik Üretimi:**
   * `news_pipeline.py` betiği üzerinden her gün farklı dillerde ve CEFR seviyelerinde otomatik güncel içerik eklenmesi.
