#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Token-Gloss Generator for English (Leenardo).
Generates context-aware token glosses across all articles and CEFR levels.
Addresses phrasal verbs, homographs, contractions, verb tenses, and plural/possessives.
"""

import json
import re
import os
import sys

# Phrasal verbs detection mapping: multi-word key -> (lemma, pos, tr_meaning, note)
PHRASAL_VERBS = {
    "give way to": ("give way to", "Phrasal Verb", "yerini bırakmak / boyun eğmek", "gave way to (\"yerini modern yöntemlere bıraktı\")"),
    "gave way to": ("give way to", "Phrasal Verb", "yerini bıraktı", "gave way to (\"yerini bıraktı\")"),
    "give way": ("give way", "Phrasal Verb", "yol vermek / yerini bırakmak", "give way (\"yerini bırakmak\")"),
    "gave way": ("give way", "Phrasal Verb", "yerini bıraktı", "gave way (\"yerini bıraktı\")"),
    "carry out": ("carry out", "Phrasal Verb", "yürütmek / uygulamak / gerçekleştirmek", "carry out (\"yürütmek\")"),
    "carried out": ("carry out", "Phrasal Verb", "yürütülen / uygulanan / gerçekleştirilen", "carried out (\"yürütülen / uygulanan\")"),
    "carrying out": ("carry out", "Phrasal Verb", "yürüten / uygulayan", "carrying out (\"uygulayarak\")"),
    "rely on": ("rely on", "Phrasal Verb", "güvenmek / dayanmak / muhtaç olmak", "rely on (\"dayanmak / güvenmek\")"),
    "relies on": ("rely on", "Phrasal Verb", "dayanır / güvenir / muhtaçtır", "relies on (\"doğal fermantasyona dayanır\")"),
    "relied on": ("rely on", "Phrasal Verb", "dayandı / güvendi", "relied on (\"dayandı\")"),
    "depend on": ("depend on", "Phrasal Verb", "bağlı olmak", "depend on (\"bağlı olmak\")"),
    "depends on": ("depend on", "Phrasal Verb", "bağlıdır", "depends on (\"bağlıdır\")"),
    "depended on": ("depend on", "Phrasal Verb", "bağlıydı", "depended on (\"bağlıydı\")"),
    "focus on": ("focus on", "Phrasal Verb", "odaklanmak", "focus on (\"kendi seçimlerine odaklanır\")"),
    "focuses on": ("focus on", "Phrasal Verb", "odaklanır", "focuses on (\"odaklanır\")"),
    "focused on": ("focus on", "Phrasal Verb", "odaklandı", "focused on (\"odaklandı\")"),
    "turn into": ("turn into", "Phrasal Verb", "dönüşmek / dönüştürmek", "turn into (\"dönüşmek\")"),
    "turns into": ("turn into", "Phrasal Verb", "dönüşür", "turns into (\"dönüşür\")"),
    "turned into": ("turn into", "Phrasal Verb", "dönüştü / dönüştürdü", "turned into (\"büyük bir harekete dönüştü\")"),
    "set up": ("set up", "Phrasal Verb", "kurmak / düzenlemek", "set up (\"kurmak\")"),
    "sets up": ("set up", "Phrasal Verb", "kurar", "sets up (\"kurar\")"),
    "break down": ("break down", "Phrasal Verb", "parçalamak / yıkmak / bozulmak", "break down (\"parçalamak\")"),
    "broke down": ("break down", "Phrasal Verb", "parçaladı / yıktı", "broke down (\"yıktı\")"),
    "lead to": ("lead to", "Phrasal Verb", "yol açmak / neden olmak", "lead to (\"yol açmak\")"),
    "leads to": ("lead to", "Phrasal Verb", "yol açar", "leads to (\"yol açar\")"),
    "led to": ("lead to", "Phrasal Verb", "yol açtı", "led to (\"yol açtı\")"),
    "point out": ("point out", "Phrasal Verb", "işaret etmek / belirtmek", "point out (\"belirtmek\")"),
    "pointed out": ("point out", "Phrasal Verb", "işaret etti / belirtti", "pointed out (\"belirtti\")"),
    "wipe out": ("wipe out", "Phrasal Verb", "yok etmek / silip süpürmek", "wipe out (\"yok etmek\")"),
    "wiped out": ("wipe out", "Phrasal Verb", "yok etti", "wiped out (\"yok etti\")"),
    "stand out": ("stand out", "Phrasal Verb", "öne çıkmak / göze çarpmak", "stand out (\"öne çıkmak\")"),
    "stands out": ("stand out", "Phrasal Verb", "öne çıkar", "stands out (\"öne çıkar\")"),
    "stood out": ("stand out", "Phrasal Verb", "öne çıktı", "stood out (\"öne çıktı\")"),
    "bring about": ("bring about", "Phrasal Verb", "meydana getirmek / yol açmak", "bring about (\"yol açmak\")"),
    "brought about": ("bring about", "Phrasal Verb", "meydana getirdi", "brought about (\"meydana getirdi\")"),
    "pass away": ("pass away", "Phrasal Verb", "vefat etmek / göçüp gitmek", "pass away (\"vefat etmek\")"),
    "passed away": ("pass away", "Phrasal Verb", "vefat etti", "passed away (\"vefat etti\")"),
    "take off": ("take off", "Phrasal Verb", "havalanmak / çıkarmak", "take off (\"çıkarmak\")"),
    "took off": ("take off", "Phrasal Verb", "havalandı / çıkardı", "took off (\"çıkardı\")"),
    "in terms of": ("in terms of", "Prepositional Phrase", "bakımından / açısından", "in terms of (\"açısından\")"),
    "as well as": ("as well as", "Conjunction", "yanı sıra / hem de", "as well as (\"yanı sıra\")"),
    "such as": ("such as", "Preposition", "örneğin / gibi", "such as (\"gibi\")"),
    "due to": ("due to", "Preposition", "nedeniyle / -den dolayı", "due to (\"nedeniyle\")"),
    "because of": ("because of", "Preposition", "yüzünden / nedeniyle", "because of (\"yüzünden\")"),
    "instead of": ("instead of", "Preposition", "yerine", "instead of (\"yerine\")"),
    "in front of": ("in front of", "Preposition", "önünde", "in front of (\"önünde\")"),
    "according to": ("according to", "Preposition", "göre", "according to (\"göre\")"),
    "thanks to": ("thanks to", "Preposition", "sayesinde", "thanks to (\"sayesinde\")"),
}

# Contractions mapping
CONTRACTIONS = {
    "don't": ("do not", "Auxiliary + Negation", "yapmamak / etmemek (geniş zaman olumsuz)"),
    "doesn't": ("does not", "Auxiliary + Negation", "yapmaz / etmez (3. tekil şahıs olumsuz)"),
    "didn't": ("did not", "Auxiliary + Negation", "yapmadı / etmedi (geçmiş zaman olumsuz)"),
    "can't": ("cannot", "Modal + Negation", "yapamaz / edemez (yetersizlik)"),
    "couldn't": ("could not", "Modal + Negation", "yapamadı / edemedi"),
    "won't": ("will not", "Auxiliary + Negation", "yapmayacak / etmeyecek"),
    "wouldn't": ("would not", "Modal + Negation", "yapmazdı / etmezdi"),
    "isn't": ("is not", "Copula + Negation", "değildir"),
    "aren't": ("are not", "Copula + Negation", "değillerdir / değilsiniz"),
    "wasn't": ("was not", "Copula + Negation", "değildi"),
    "weren't": ("were not", "Copula + Negation", "değillerdi / değildiniz"),
    "haven't": ("have not", "Auxiliary + Negation", "yapmadı / sahip değil"),
    "hasn't": ("has not", "Auxiliary + Negation", "yapmadı / sahip değil"),
    "hadn't": ("had not", "Auxiliary + Negation", "yapmamıştı"),
    "it's": ("it is", "Pronoun + Copula", "bu ...dır / o ...dır"),
    "that's": ("that is", "Pronoun + Copula", "işte bu / şu ...dır"),
    "there's": ("there is", "Existential + Copula", "vardır"),
    "what's": ("what is", "Pronoun + Copula", "nedir"),
    "they're": ("they are", "Pronoun + Copula", "onlar ...dır"),
    "we're": ("we are", "Pronoun + Copula", "biz ...-ız"),
    "you're": ("you are", "Pronoun + Copula", "sen ...sın / siz ...sınız"),
    "i'm": ("I am", "Pronoun + Copula", "ben ...-ım"),
    "i've": ("I have", "Pronoun + Auxiliary", "ben ...-dım"),
    "we've": ("we have", "Pronoun + Auxiliary", "biz ...-dık"),
    "they've": ("they have", "Pronoun + Auxiliary", "onlar ...-dılar"),
    "you've": ("you have", "Pronoun + Auxiliary", "sen ...-dın"),
    "he's": ("he is", "Pronoun + Copula", "o ...dır"),
    "she's": ("she is", "Pronoun + Copula", "o ...dır"),
}

# Common English Function Words
EN_FUNCTION_WORDS = {
    "the": ("the", "Belirteç (Definite Article)", "o / bilinen (belirli artikel)", "the"),
    "a": ("a", "Belirteç (Indefinite Article)", "bir", "a"),
    "an": ("an", "Belirteç (Indefinite Article)", "bir", "an"),
    "and": ("and", "Bağlaç", "ve", "and"),
    "or": ("or", "Bağlaç", "veya / ya da", "or"),
    "but": ("but", "Bağlaç", "ama / fakat", "but"),
    "yet": ("yet", "Bağlaç / Zarf", "oysa / henüz / yine de", "yet"),
    "so": ("so", "Bağlaç / Zarf", "bu yüzden / öyle", "so"),
    "for": ("for", "Edat / Bağlaç", "için / çünkü", "for"),
    "nor": ("nor", "Bağlaç", "ne de", "nor"),
    "in": ("in", "Edat", "içinde / -de, -da", "in"),
    "on": ("on", "Edat", "üzerinde / -de, -da", "on"),
    "at": ("at", "Edat", "-de, -da", "at"),
    "by": ("by", "Edat", "tarafından / ile / yanında", "by"),
    "from": ("from", "Edat", "-den, -dan", "from"),
    "to": ("to", "Edat / Mastar Eki", "-e, -a / için / mastar eki", "to"),
    "with": ("with", "Edat", "ile / birlikte", "with"),
    "without": ("without", "Edat", "-sız, -siz / olmadan", "without"),
    "about": ("about", "Edat / Zarf", "hakkında / yaklaşık", "about"),
    "over": ("over", "Edat", "üzerinde / boyunca", "over"),
    "under": ("under", "Edat", "altında", "under"),
    "through": ("through", "Edat", "boyunca / aracılığıyla", "through"),
    "between": ("between", "Edat", "arasında (iki şey)", "between"),
    "among": ("among", "Edat", "arasında (çok şey)", "among"),
    "after": ("after", "Edat / Bağlaç", "sonra", "after"),
    "before": ("before", "Edat / Bağlaç", "önce", "before"),
    "during": ("during", "Edat", "sırasında / boyunca", "during"),
    "while": ("while", "Bağlaç", "iken / oysa", "while"),
    "since": ("since", "Edat / Bağlaç", "-den beri / çünkü", "since"),
    "until": ("until", "Edat / Bağlaç", "-e kadar", "until"),
    "as": ("as", "Edat / Bağlaç", "olarak / gibi / iken", "as"),
    "than": ("than", "Edat", "-den, -dan (karşılaştırma)", "than"),
    "this": ("this", "İşaret Sıfatı / Zamiri", "bu", "this"),
    "that": ("that", "İşaret Sıfatı / Bağlaç", "şu / o / ki", "that"),
    "these": ("these", "İşaret Sıfatı / Zamiri", "bunlar", "these"),
    "those": ("those", "İşaret Sıfatı / Zamiri", "şunlar / onlar", "those"),
    "all": ("all", "Belirteç / Zamir", "tüm / bütün / hepsi", "all"),
    "each": ("each", "Belirteç / Zamir", "her bir / her", "each"),
    "every": ("every", "Belirteç", "her", "every"),
    "some": ("some", "Belirteç / Zamir", "bazı / biraz", "some"),
    "any": ("any", "Belirteç / Zamir", "herhangi bir / hiç", "any"),
    "no": ("no", "Belirteç", "hiç / yok", "no"),
    "not": ("not", "Zarf", "değil", "not"),
    "only": ("only", "Zarf / Sıfat", "sadece / tek", "only"),
    "very": ("very", "Derecelendirme Zarfı", "çok", "very"),
    "most": ("most", "Derecelendirme Zarfı / Sıfat", "en çok / çoğu", "most"),
    "more": ("more", "Derecelendirme Zarfı / Sıfat", "daha / daha fazla", "more"),
    "less": ("less", "Derecelendirme Zarfı", "daha az", "less"),
    "least": ("least", "Derecelendirme Zarfı", "en az", "least"),
    "also": ("also", "Zarf", "ayrıca / da, de", "also"),
    "even": ("even", "Zarf", "hatta / bile", "even"),
    "still": ("still", "Zarf", "hâlâ / yine de", "still"),
    "already": ("already", "Zarf", "zaten / çoktan", "already"),
    "often": ("often", "Sıklık Zarfı", "sık sık / genellikle", "often"),
    "always": ("always", "Sıklık Zarfı", "her zaman / daima", "always"),
    "never": ("never", "Sıklık Zarfı", "asla / hiçbir zaman", "never"),
    "sometimes": ("sometimes", "Sıklık Zarfı", "bazen / ara sıra", "sometimes"),
    "usually": ("usually", "Sıklık Zarfı", "genellikle", "usually"),
    "is": ("be", "Fiil (Geniş Zaman 3. Tekil)", "dır, dir / dir", "is"),
    "are": ("be", "Fiil (Geniş Zaman Çoğul)", "dırlar / dirler", "are"),
    "was": ("be", "Fiil (Geçmiş Zaman Tekil)", "idi / oldu", "was"),
    "were": ("be", "Fiil (Geçmiş Zaman Çoğul)", "idiler / oldular", "were"),
    "be": ("be", "Fiil (Yalın/Mastar)", "olmak", "be"),
    "been": ("be", "Fiil (Ortaç/Participle)", "olmuş", "been"),
    "being": ("be", "Fiil (Şimdiki Zaman Ortacı)", "olma / olarak", "being"),
    "has": ("have", "Fiil / Yardımcı Fiil", "sahiptir / vardır", "has"),
    "have": ("have", "Fiil / Yardımcı Fiil", "sahip olmak", "have"),
    "had": ("have", "Fiil / Yardımcı Fiil (Geçmiş)", "sahipti / olmuştu", "had"),
    "do": ("do", "Fiil / Yardımcı Fiil", "yapmak", "do"),
    "does": ("do", "Fiil (3. Tekil)", "yapar", "does"),
    "did": ("do", "Fiil (Geçmiş Zaman)", "yaptı", "did"),
    "can": ("can", "Modal Fiil", "-ebilmek (yeterlilik)", "can"),
    "could": ("could", "Modal Fiil (Geçmiş)", "-ebilirdi / -ebildi", "could"),
    "may": ("may", "Modal Fiil", "-ebilir (olasılık / izin)", "may"),
    "might": ("might", "Modal Fiil", "-ebilirdi (düşük olasılık)", "might"),
    "must": ("must", "Modal Fiil", "-meli, -malı (zorunluluk)", "must"),
    "should": ("should", "Modal Fiil", "-meli, -malı (tavsiye)", "should"),
    "will": ("will", "Gelecek Zaman Yardımcı Fiil", "-ecek, -acak", "will"),
    "would": ("would", "Modal Fiil", "-erdi / -ecekti", "would"),
    "it": ("it", "Zamir", "o / bu", "it"),
    "its": ("it", "İyelik Sıfatı", "onun / bunun", "its"),
    "itself": ("it", "Dönüşlülük Zamiri", "kendisi", "itself"),
    "he": ("he", "Kişi Zamiri", "o (erkek)", "he"),
    "him": ("he", "Nesne Zamiri", "ona / onu", "him"),
    "his": ("he", "İyelik Sıfatı / Zamiri", "onun", "his"),
    "himself": ("he", "Dönüşlülük Zamiri", "kendisi", "himself"),
    "she": ("she", "Kişi Zamiri", "o (kadın)", "she"),
    "her": ("she", "Nesne / İyelik Zamiri", "ona / onu / onun", "her"),
    "herself": ("she", "Dönüşlülük Zamiri", "kendisi", "herself"),
    "they": ("they", "Kişi Zamiri (Çoğul)", "onlar", "they"),
    "them": ("they", "Nesne Zamiri", "onlara / onları", "them"),
    "their": ("they", "İyelik Sıfatı", "onların", "their"),
    "theirs": ("they", "İyelik Zamiri", "onlarınki", "theirs"),
    "themselves": ("they", "Dönüşlülük Zamiri", "kendileri", "themselves"),
    "we": ("we", "Kişi Zamiri", "biz", "we"),
    "us": ("we", "Nesne Zamiri", "bize / bizi", "us"),
    "our": ("we", "İyelik Sıfatı", "bizim", "our"),
    "ours": ("we", "İyelik Zamiri", "bizimki", "ours"),
    "ourselves": ("we", "Dönüşlülük Zamiri", "kendimiz", "ourselves"),
    "you": ("you", "Kişi Zamiri", "sen / siz", "you"),
    "your": ("you", "İyelik Sıfatı", "senin / sizin", "your"),
    "yours": ("you", "İyelik Zamiri", "seninki / sizinki", "yours"),
    "yourself": ("you", "Dönüşlülük Zamiri", "kendin", "yourself"),
    "yourselves": ("you", "Dönüşlülük Zamiri", "kendiniz", "yourselves"),
    "i": ("I", "Kişi Zamiri", "ben", "I"),
    "me": ("I", "Nesne Zamiri", "bana / beni", "me"),
    "my": ("I", "İyelik Sıfatı", "benim", "my"),
    "mine": ("I", "İyelik Zamiri", "benimki", "mine"),
    "myself": ("I", "Dönüşlülük Zamiri", "kendim", "myself"),
}

# English Base Lexicon (Common content words across the 23 stories)
EN_CONTENT_LEXICON = {
    # Nouns
    "art": ("art", "Noun", "sanat"),
    "artist": ("artist", "Noun", "sanatçı"),
    "artists": ("artist", "Noun (Plural)", "sanatçılar"),
    "painting": ("painting", "Noun", "resim / tablo"),
    "paintings": ("painting", "Noun (Plural)", "resimler / tablolar"),
    "painter": ("painter", "Noun", "ressam"),
    "poet": ("poet", "Noun", "şair"),
    "poetry": ("poetry", "Noun", "şiir"),
    "poem": ("poem", "Noun", "şiir"),
    "poems": ("poem", "Noun (Plural)", "şiirler"),
    "literature": ("literature", "Noun", "edebiyat"),
    "history": ("history", "Noun", "tarih"),
    "culture": ("culture", "Noun", "kültür"),
    "tradition": ("tradition", "Noun", "gelenek"),
    "traditions": ("tradition", "Noun (Plural)", "gelenekler"),
    "heritage": ("heritage", "Noun", "miras"),
    "voyage": ("voyage", "Noun", "sefer / yolculuk"),
    "voyages": ("voyage", "Noun (Plural)", "seferler / yolculuklar"),
    "journey": ("journey", "Noun", "yolculuk"),
    "sea": ("sea", "Noun", "deniz"),
    "city": ("city", "Noun", "şehir / kent"),
    "cities": ("city", "Noun (Plural)", "şehirler"),
    "nature": ("nature", "Noun", "doğa"),
    "boat": ("boat", "Noun", "tekne"),
    "boats": ("boat", "Noun (Plural)", "tekneler"),
    "horse": ("horse", "Noun", "at"),
    "war": ("war", "Noun", "savaş"),
    "wall": ("wall", "Noun", "sur / duvar"),
    "walls": ("wall", "Noun (Plural)", "surlar / duvarlar"),
    "soldier": ("soldier", "Noun", "asker"),
    "soldiers": ("soldier", "Noun (Plural)", "askerler"),
    "army": ("army", "Noun", "ordu"),
    "dream": ("dream", "Noun", "rüya / düş"),
    "dreams": ("dream", "Noun (Plural)", "rüyalar"),
    "sleep": ("sleep", "Noun / Verb", "uyku / uyumak"),
    "brain": ("brain", "Noun", "beyin"),
    "memory": ("memory", "Noun", "bellek / hafıza"),
    "memories": ("memory", "Noun (Plural)", "anılar / hatıralar"),
    "tree": ("tree", "Noun", "ağaç"),
    "trees": ("tree", "Noun (Plural)", "ağaçlar"),
    "forest": ("forest", "Noun", "orman"),
    "tea": ("tea", "Noun", "çay"),
    "coffee": ("coffee", "Noun", "kahve"),
    "cup": ("cup", "Noun", "fincan"),
    "glass": ("glass", "Noun", "bardak / cam"),
    "shadow": ("shadow", "Noun", "gölge"),
    "shadows": ("shadow", "Noun (Plural)", "gölgeler"),
    "puppet": ("puppet", "Noun", "kukla / tasvir"),
    "puppets": ("puppet", "Noun (Plural)", "kuklalar / tasvirler"),
    "music": ("music", "Noun", "müzik"),
    "sound": ("sound", "Noun", "ses"),
    "sounds": ("sound", "Noun (Plural)", "sesler"),
    "instrument": ("instrument", "Noun", "enstrüman / çalgı"),
    "instruments": ("instrument", "Noun (Plural)", "enstrümanlar"),
    "yogurt": ("yogurt", "Noun", "yoğurt"),
    "milk": ("milk", "Noun", "süt"),
    "scent": ("scent", "Noun", "koku / rayiha"),
    "smell": ("smell", "Noun / Verb", "koku / koklamak"),
    "stone": ("stone", "Noun", "taş"),
    "stones": ("stone", "Noun (Plural)", "taşlar"),
    "cave": ("cave", "Noun", "mağara"),
    "caves": ("cave", "Noun (Plural)", "mağaralar"),
    "bee": ("bee", "Noun", "arı"),
    "bees": ("bee", "Noun (Plural)", "arılar"),
    "honey": ("honey", "Noun", "bal"),
    "olive": ("olive", "Noun", "zeytin"),
    "oil": ("oil", "Noun", "yağ"),
    "gold": ("gold", "Noun / Adjective", "altın"),
    "sweater": ("sweater", "Noun", "kazak"),
    "decision": ("decision", "Noun", "karar"),
    "decisions": ("decision", "Noun (Plural)", "kararlar"),
    "choice": ("choice", "Noun", "seçim"),
    "choices": ("choice", "Noun (Plural)", "seçimler"),
    "fatigue": ("fatigue", "Noun", "yorgunluk"),
    "temple": ("temple", "Noun", "tapınak / mabet"),
    "monument": ("monument", "Noun", "anıt"),
    "pillar": ("pillar", "Noun", "sütun / dikilitaş"),
    "pillars": ("pillar", "Noun (Plural)", "sütunlar"),
    "hunter": ("hunter", "Noun", "avcı"),
    "hunters": ("hunter", "Noun (Plural)", "avcılar"),
    "people": ("people", "Noun (Plural)", "insanlar / halk"),
    "human": ("human", "Noun / Adjective", "insan"),
    "humans": ("human", "Noun (Plural)", "insanlar"),
    "life": ("life", "Noun", "hayat / yaşam"),
    "lives": ("life", "Noun (Plural)", "hayatlar / yaşamlar"),
    "time": ("time", "Noun", "zaman / vakit"),
    "times": ("time", "Noun (Plural)", "zamanlar / defalar"),
    "world": ("world", "Noun", "dünya"),
    "century": ("century", "Noun", "yüzyıl"),
    "centuries": ("century", "Noun (Plural)", "yüzyıllar"),
    "year": ("year", "Noun", "yıl / sene"),
    "years": ("year", "Noun (Plural)", "yıllar"),
    "day": ("day", "Noun", "gün"),
    "days": ("day", "Noun (Plural)", "günler"),
    "night": ("night", "Noun", "gece"),
    "place": ("place", "Noun / Verb", "yer / koymak"),
    "places": ("place", "Noun (Plural)", "yerler"),
    "process": ("process", "Noun", "süreç"),
    "method": ("method", "Noun", "yöntem"),
    "methods": ("method", "Noun (Plural)", "yöntemler"),
    "way": ("way", "Noun", "yol / tarz"),
    "ways": ("way", "Noun (Plural)", "yollar"),

    # Adjectives
    "ancient": ("ancient", "Adjective", "antik / kadim"),
    "old": ("old", "Adjective", "eski / yaşlı"),
    "new": ("new", "Adjective", "yeni"),
    "modern": ("modern", "Adjective", "modern / çağdaş"),
    "traditional": ("traditional", "Adjective", "geleneksel"),
    "famous": ("famous", "Adjective", "ünlü / meşhur"),
    "great": ("great", "Adjective", "büyük / harika"),
    "small": ("small", "Adjective", "küçük"),
    "large": ("large", "Adjective", "büyük / geniş"),
    "wooden": ("wooden", "Adjective", "ahşap / tahta"),
    "blue": ("blue", "Adjective", "mavi"),
    "bright": ("bright", "Adjective", "parlak / canlı"),
    "colorful": ("colorful", "Adjective", "renkli"),
    "quiet": ("quiet", "Adjective", "sessiz / sakin"),
    "deep": ("deep", "Adjective", "derin"),
    "profound": ("profound", "Adjective", "derin / köklü"),
    "simple": ("simple", "Adjective", "basit / sade"),
    "complex": ("complex", "Adjective", "karmaşık"),
    "natural": ("natural", "Adjective", "doğal"),
    "important": ("important", "Adjective", "önemli"),
    "special": ("special", "Adjective", "özel"),
    "general": ("general", "Adjective", "genel"),
    "rich": ("rich", "Adjective", "zengin"),
    "poor": ("poor", "Adjective", "fakir / zavallı"),
    "long": ("long", "Adjective", "uzun"),
    "short": ("short", "Adjective", "kısa"),
    "high": ("high", "Adjective", "yüksek"),
    "strong": ("strong", "Adjective", "güçlü"),
    "weak": ("weak", "Adjective", "zayıf"),
    "fresh": ("fresh", "Adjective", "taze"),
    "warm": ("warm", "Adjective", "ılık / sıcak"),
    "cold": ("cold", "Adjective", "soğuk"),
    "first": ("first", "Ordinal / Adjective", "ilk / birinci"),
    "last": ("last", "Adjective", "son / sonuncu"),
    "second": ("second", "Ordinal / Adjective", "ikinci"),
    "twentieth": ("twentieth", "Ordinal", "yirminci"),

    # Verbs
    "love": ("love", "Verb", "sevmek"),
    "loved": ("love", "Verb (Past)", "sevdi"),
    "like": ("like", "Verb / Preposition", "beğenmek / sevmek / gibi"),
    "liked": ("like", "Verb (Past)", "beğendi / sevdi"),
    "live": ("live", "Verb / Adjective", "yaşamak / canlı"),
    "lived": ("live", "Verb (Past)", "yaşadı"),
    "living": ("live", "Verb (Participle)", "yaşayan / canlı"),
    "make": ("make", "Verb", "yapmak / oluşturmak"),
    "made": ("make", "Verb (Past)", "yaptı / oluşturdu"),
    "making": ("make", "Verb (Participle)", "yaparak / yapma"),
    "do": ("do", "Verb", "yapmak / etmek"),
    "did": ("do", "Verb (Past)", "yaptı / etti"),
    "doing": ("do", "Verb (Participle)", "yaparak"),
    "see": ("see", "Verb", "görmek"),
    "saw": ("see", "Verb (Past)", "gördü"),
    "seen": ("see", "Verb (Participle)", "görülmüş"),
    "seeing": ("see", "Verb (Participle)", "görerek"),
    "look": ("look", "Verb", "bakmak / görünmek"),
    "looked": ("look", "Verb (Past)", "baktı / göründü"),
    "looking": ("look", "Verb (Participle)", "bakarak"),
    "know": ("know", "Verb", "bilmek / tanımak"),
    "knew": ("know", "Verb (Past)", "biliyordu / bildi"),
    "known": ("know", "Verb (Participle)", "bilinen / tanınan"),
    "find": ("find", "Verb", "bulmak"),
    "found": ("find", "Verb (Past)", "buldu"),
    "finding": ("find", "Verb (Participle)", "bularak / bulma"),
    "give": ("give", "Verb", "vermek"),
    "gave": ("give", "Verb (Past)", "verdi"),
    "given": ("give", "Verb (Participle)", "verilen / verilmiş"),
    "giving": ("give", "Verb (Participle)", "vererek"),
    "take": ("take", "Verb", "almak / götürmek"),
    "took": ("take", "Verb (Past)", "aldı / götürdü"),
    "taken": ("take", "Verb (Participle)", "alınmış"),
    "taking": ("take", "Verb (Participle)", "alarak"),
    "become": ("become", "Verb", "haline gelmek / olmak"),
    "became": ("become", "Verb (Past)", "haline geldi / oldu"),
    "becoming": ("become", "Verb (Participle)", "dönüşerek"),
    "create": ("create", "Verb", "yaratmak / oluşturmak"),
    "created": ("create", "Verb (Past)", "yarattı / oluşturdu"),
    "creating": ("create", "Verb (Participle)", "yaratarak"),
    "develop": ("develop", "Verb", "geliştirmek"),
    "developed": ("develop", "Verb (Past)", "geliştirdi"),
    "developing": ("develop", "Verb (Participle)", "geliştirerek / gelişen"),
    "build": ("build", "Verb", "inşa etmek / kurmak"),
    "built": ("build", "Verb (Past)", "inşa etti / kurdu"),
    "building": ("build", "Verb (Participle) / Noun", "inşa ederek / bina"),
    "show": ("show", "Verb", "göstermek"),
    "showed": ("show", "Verb (Past)", "gösterdi"),
    "shown": ("show", "Verb (Participle)", "gösterilen"),
    "showing": ("show", "Verb (Participle)", "göstererek"),
    "stand": ("stand", "Verb", "durmak / dikilmek"),
    "stood": ("stand", "Verb (Past)", "durdu / dikildi"),
    "standing": ("stand", "Verb (Participle)", "duran"),
    "sail": ("sail", "Verb / Noun", "denize açılmak / yelken"),
    "sailed": ("sail", "Verb (Past)", "denize açıldı / yelken açtı"),
    "sailing": ("sail", "Verb (Participle)", "yelken açarak"),
    "visit": ("visit", "Verb", "ziyaret etmek"),
    "visited": ("visit", "Verb (Past)", "ziyaret etti"),
    "visiting": ("visit", "Verb (Participle)", "ziyaret ederek"),
    "explore": ("explore", "Verb", "keşfetmek"),
    "explored": ("explore", "Verb (Past)", "keşfetti"),
    "exploring": ("explore", "Verb (Participle)", "keşfederek"),
    "transform": ("transform", "Verb", "dönüştürmek"),
    "transformed": ("transform", "Verb (Past)", "dönüştürdü"),
    "transforming": ("transform", "Verb (Participle)", "dönüştürerek"),
    "begin": ("begin", "Verb", "başlamak"),
    "began": ("begin", "Verb (Past)", "başladı"),
    "begun": ("begin", "Verb (Participle)", "başlamış"),
    "beginning": ("begin", "Verb (Participle) / Noun", "başlayarak / başlangıç"),
    "start": ("start", "Verb", "başlamak"),
    "started": ("start", "Verb (Past)", "başladı"),
    "starting": ("start", "Verb (Participle)", "başlayarak"),
    "help": ("help", "Verb / Noun", "yardım etmek / yardım"),
    "helped": ("help", "Verb (Past)", "yardım etti"),
    "helping": ("help", "Verb (Participle)", "yardım ederek"),
}


def analyze_english_token(token, sentence_en="", sentence_tr="", curated_vocab=None):
    clean = re.sub(r"[^\w'-]", "", token, flags=re.UNICODE).strip()
    if not clean:
        return None

    raw_lower = clean.lower()

    # 1. Check Curated Vocab from current level / database
    if curated_vocab and raw_lower in curated_vocab:
        v = curated_vocab[raw_lower]
        tr_trans = v.get("translations", {}).get("tr") or v.get("target") or clean
        return {
            "token": clean,
            "lemma": v.get("target") or clean,
            "pos": "Key Word (Lesson Vocab)",
            "gloss": {"tr": tr_trans, "en": clean},
            "note": f"\"{clean}\" — {tr_trans}"
        }

    # 2. Check Phrasal Verbs in Sentence Context
    if sentence_en:
        s_en_low = sentence_en.lower()
        for pv, (pv_lemma, pv_pos, pv_tr, pv_note) in PHRASAL_VERBS.items():
            pv_words = pv.split()
            if raw_lower in pv_words and pv in s_en_low:
                return {
                    "token": clean,
                    "lemma": pv_lemma,
                    "pos": f"{pv_pos} (Öbeksi Fiil)",
                    "gloss": {"tr": pv_tr, "en": clean},
                    "note": pv_note
                }

    # 3. Check Homographs with Context Disambiguation
    if raw_lower == "read":
        # Disambiguate read: past (/red/) vs present (/ri:d/)
        is_past = bool(re.search(r"\b(yesterday|in\s+\d{4}|had|have|has|was|were)\b", sentence_en, re.I))
        if is_past:
            return {
                "token": clean,
                "lemma": "read",
                "pos": "Verb (Past / /red/)",
                "gloss": {"tr": "okudu (geçmiş zaman)", "en": "read"},
                "note": "read (/red/) — geçmiş zaman telaffuzu"
            }
        else:
            return {
                "token": clean,
                "lemma": "read",
                "pos": "Verb (Present / /ri:d/)",
                "gloss": {"tr": "okur / okumak", "en": "read"},
                "note": "read (/ri:d/) — geniş zaman telaffuzu"
            }
    elif raw_lower == "lead":
        is_metal = bool(re.search(r"\b(metal|pipe|poison|heavy)\b", sentence_en, re.I))
        if is_metal:
            return {
                "token": clean,
                "lemma": "lead",
                "pos": "Noun (/led/)",
                "gloss": {"tr": "kurşun (maden)", "en": "lead"}
            }
        else:
            return {
                "token": clean,
                "lemma": "lead",
                "pos": "Verb (/li:d/)",
                "gloss": {"tr": "öncülük etmek / yol açmak", "en": "lead"}
            }
    elif raw_lower == "close":
        is_verb = bool(re.search(r"\b(to\s+close|will\s+close|close\s+the)\b", sentence_en, re.I))
        if is_verb:
            return {
                "token": clean,
                "lemma": "close",
                "pos": "Verb (/kloʊz/)",
                "gloss": {"tr": "kapatmak", "en": "close"}
            }
        else:
            return {
                "token": clean,
                "lemma": "close",
                "pos": "Adjective (/kloʊs/)",
                "gloss": {"tr": "yakın / samimi", "en": "close"}
            }

    # 4. Check Contractions
    if raw_lower in CONTRACTIONS:
        exp, pos, tr_meaning = CONTRACTIONS[raw_lower]
        return {
            "token": clean,
            "lemma": exp,
            "pos": pos,
            "gloss": {"tr": tr_meaning, "en": exp},
            "note": f"{clean} = {exp} (kısaltma)"
        }

    # 5. Check Function Words
    if raw_lower in EN_FUNCTION_WORDS:
        lemma, pos, tr_meaning, en_val = EN_FUNCTION_WORDS[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_meaning, "en": clean}
        }

    # 6. Check Content Lexicon
    if raw_lower in EN_CONTENT_LEXICON:
        lemma, pos, tr_meaning = EN_CONTENT_LEXICON[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_meaning, "en": clean}
        }

    # 7. Check Possessive 's
    if raw_lower.endswith("'s") or raw_lower.endswith("’s"):
        base = clean[:-2]
        return {
            "token": clean,
            "lemma": base,
            "pos": "Noun (Possessive)",
            "gloss": {"tr": f"{base}'nin / {base}'in", "en": clean},
            "note": f"{clean} (iyelik eki: 's)"
        }

    # 8. Check Regular -ed Past Tense
    if raw_lower.endswith("ed") and len(raw_lower) > 4:
        # e.g. explored -> explore, painted -> paint
        cand_stem = raw_lower[:-2] if not raw_lower.endswith("ied") else raw_lower[:-3] + "y"
        cand_stem_e = raw_lower[:-1]  # e.g. created -> create
        for cand in (cand_stem_e, cand_stem):
            if cand in EN_CONTENT_LEXICON:
                lemma, _, tr = EN_CONTENT_LEXICON[cand]
                return {
                    "token": clean,
                    "lemma": lemma,
                    "pos": "Verb (Past Tense -ed)",
                    "gloss": {"tr": f"{tr} (geçmiş zaman)", "en": clean},
                    "note": f"{clean} (past tense of {lemma})"
                }

    # 9. Check Regular -ing Participle / Gerund
    if raw_lower.endswith("ing") and len(raw_lower) > 5:
        cand_stem = raw_lower[:-3]
        cand_stem_e = raw_lower[:-3] + "e"
        for cand in (cand_stem_e, cand_stem):
            if cand in EN_CONTENT_LEXICON:
                lemma, _, tr = EN_CONTENT_LEXICON[cand]
                return {
                    "token": clean,
                    "lemma": lemma,
                    "pos": "Verb (Participle / Gerund -ing)",
                    "gloss": {"tr": f"{tr} (şimdiki/zarf-fiil)", "en": clean},
                    "note": f"{clean} (-ing form of {lemma})"
                }

    # 10. Check Regular Plural -s / -es
    if raw_lower.endswith("s") and len(raw_lower) > 3 and not raw_lower.endswith("ss"):
        cand_stem = raw_lower[:-1]
        if raw_lower.endswith("es"):
            cand_stem_es = raw_lower[:-2]
        else:
            cand_stem_es = ""
        for cand in (cand_stem, cand_stem_es):
            if cand and cand in EN_CONTENT_LEXICON:
                lemma, pos, tr = EN_CONTENT_LEXICON[cand]
                return {
                    "token": clean,
                    "lemma": lemma,
                    "pos": f"{pos} (Plural -s)",
                    "gloss": {"tr": f"{tr} (çoğul)", "en": clean}
                }

    # 11. Proper Noun Heuristic (Capitalized not at start of sentence)
    is_cap = clean[0].isupper() and clean[0] != clean[0].lower()
    return {
        "token": clean,
        "lemma": clean.lower(),
        "pos": "Proper Noun" if is_cap else "Word",
        "gloss": {"tr": clean, "en": clean}
    }


def tokenize_target(target):
    raw_tokens = re.split(r"(\s+|[.,!?:;«»\"“”()]+)", target)
    clean_words = []
    for tok in raw_tokens:
        if re.match(r"^\s+$", tok) or re.match(r"^[.,!?:;«»\"“”()]+$", tok):
            continue
        if len(tok) > 0:
            c = re.sub(r"[^\w'-]", "", tok, flags=re.UNICODE).strip()
            if c:
                clean_words.append((tok, c))
    return clean_words


def process_english_articles(articles_path="articles.json"):
    print(f"Reading {articles_path} for English token-gloss generation...")
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # Collect English global vocab
    global_vocab = {}
    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("en", {}).items():
            for v in lvl_data.get("vocab", []):
                tgt = v.get("target", "").strip().lower()
                if tgt:
                    global_vocab[tgt] = v

    print(f"Loaded {len(global_vocab)} English curated vocab items.")

    total_sents = 0
    total_tokens_generated = 0

    for art_idx, art in enumerate(articles):
        art_id = art["id"]
        en_data = art.get("languages", {}).get("en", {})

        for lvl in ["A1", "A2", "B1", "B2", "C1"]:
            lvl_data = en_data.get(lvl, {})
            art_vocab = {**global_vocab}
            for v in lvl_data.get("vocab", []):
                tgt = v.get("target", "").strip().lower()
                if tgt:
                    art_vocab[tgt] = v

            for pi, p in enumerate(lvl_data.get("paragraphs", [])):
                for si, s in enumerate(p):
                    total_sents += 1
                    target_sent = s.get("target", "")
                    tr_trans = s.get("translations", {}).get("tr", "")

                    token_pairs = tokenize_target(target_sent)
                    tokens_list = []

                    for raw_tok, clean_tok in token_pairs:
                        gloss_obj = analyze_english_token(
                            clean_tok,
                            sentence_en=target_sent,
                            sentence_tr=tr_trans,
                            curated_vocab=art_vocab
                        )
                        if gloss_obj:
                            tokens_list.append(gloss_obj)

                    s["tokens"] = tokens_list
                    total_tokens_generated += len(tokens_list)

    print(f"\nCompleted English Generation!")
    print(f"Total English Sentences Processed: {total_sents}")
    print(f"Total English Tokens with Contextual Gloss: {total_tokens_generated}")

    print(f"\nWriting back to {articles_path}...")
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ Successfully updated articles.json with English token-gloss data.")


if __name__ == "__main__":
    process_english_articles()
