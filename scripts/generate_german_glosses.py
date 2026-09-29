#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Token-Gloss Generator for German (Leenardo).
Generates context-aware token glosses across all articles and CEFR levels.
Handles separable verbs (trennbare Verben across clauses), composite nouns (Komposita),
prepositional contractions (im, am, zum, zur, beim, vom, ins), and case inflections.
"""

import json
import re
import os
import sys

# Separable Verb mappings: (conjugated_verb, prefix) -> (full_infinitive, pos, tr_meaning, en_meaning)
SEPARABLE_VERB_PAIRS = {
    ("ließen", "zurück"): ("zurücklassen", "Trennbares Verb", "geride bırakmak", "to leave behind"),
    ("lässt", "zurück"): ("zurücklassen", "Trennbares Verb", "geride bırakır", "leaves behind"),
    ("lassen", "zurück"): ("zurücklassen", "Trennbares Verb", "geride bırakmak", "to leave behind"),
    ("stellen", "dar"): ("darstellen", "Trennbares Verb", "temsil etmek / teşkil etmek", "to represent / constitute"),
    ("stellt", "dar"): ("darstellen", "Trennbares Verb", "temsil eder / teşkil eder", "represents / constitutes"),
    ("stellten", "dar"): ("darstellen", "Trennbares Verb", "temsil etti / teşkil etti", "represented / constituted"),
    ("schlief", "ein"): ("einschlafen", "Trennbares Verb", "uyuyakalmak / uykuya dalmak", "to fall asleep"),
    ("schläft", "ein"): ("einschlafen", "Trennbares Verb", "uyuyakalır", "falls asleep"),
    ("ahmt", "nach"): ("nachahmen", "Trennbares Verb", "taklit etmek", "to imitate / mimic"),
    ("ahmte", "nach"): ("nachahmen", "Trennbares Verb", "taklit etti", "imitated / mimicked"),
    ("ahmen", "nach"): ("nachahmen", "Trennbares Verb", "taklit ederler", "imitate / mimic"),
    ("bauten", "auf"): ("aufbauen", "Trennbares Verb", "inşa etmek / dikmek", "to build up / erect"),
    ("baut", "auf"): ("aufbauen", "Trennbares Verb", "inşa eder", "builds up / erects"),
    ("bauen", "auf"): ("aufbauen", "Trennbares Verb", "inşa ederler", "build up / erect"),
    ("drückte", "aus"): ("ausdrücken", "Trennbares Verb", "ifade etmek / dışa vurmak", "to express"),
    ("drückt", "aus"): ("ausdrücken", "Trennbares Verb", "ifade eder", "expresses"),
    ("drücken", "aus"): ("ausdrücken", "Trennbares Verb", "ifade ederler", "express"),
    ("kühlt", "ab"): ("abkühlen", "Trennbares Verb", "soğumak", "to cool down"),
    ("kühlte", "ab"): ("abkühlen", "Trennbares Verb", "soğudu", "cooled down"),
    ("setzte", "auf"): ("aufsetzen", "Trennbares Verb", "ateşe koymak / ocağa koymak", "to put on (kettle/stove)"),
    ("tauchen", "ein"): ("eintauchen", "Trennbares Verb", "dalmak / içine girmek", "to immerse / dive in"),
    ("taucht", "ein"): ("eintauchen", "Trennbares Verb", "dalar", "immerses / dives in"),
    ("leitet", "ein"): ("einleiten", "Trennbares Verb", "başlatmak / öncülük etmek", "to initiate / usher in"),
    ("leitete", "ein"): ("einleiten", "Trennbares Verb", "başlattı", "initiated / ushered in"),
    ("weicht", "ab"): ("abweichen", "Trennbares Verb", "farklılaşmak / sapmak", "to deviate / diverge from"),
    ("wich", "ab"): ("abweichen", "Trennbares Verb", "farklılaştı / saptı", "deviated / diverged from"),
    ("hauchte", "ein"): ("einhauchen", "Trennbares Verb", "üflemek / aşılamak", "to breathe into / instill"),
    ("weckt", "auf"): ("aufwecken", "Trennbares Verb", "uyandırmak / canlandırmak", "to wake up / evoke"),
    ("breiten", "aus"): ("ausbreiten", "Trennbares Verb", "yayılmak / serilmek", "to spread out / unfold"),
    ("breitet", "aus"): ("ausbreiten", "Trennbares Verb", "yayılır", "spreads out"),
    ("nimmt", "auf"): ("aufnehmen", "Trennbares Verb", "içine çekmek / emmek / kaydetmek", "to absorb / take in"),
    ("nahmen", "auf"): ("aufnehmen", "Trennbares Verb", "emdi / kaydetti", "absorbed / took in"),
    ("höhlten", "aus"): ("aushöhlen", "Trennbares Verb", "oymak / boşaltmak", "to hollow out / excavate"),
    ("schotteten", "ab"): ("abschotten", "Trennbares Verb", "yalıtmak / kapatmak / tecrit etmek", "to seal off / isolate"),
    ("hängen", "ab"): ("abhängen", "Trennbares Verb", "bağlı olmak", "to depend on"),
    ("hängt", "ab"): ("abhängen", "Trennbares Verb", "bağlıdır", "depends on"),
    ("bräche", "ein"): ("einbrechen", "Trennbares Verb", "çökmek / düşmek", "to collapse / plummet"),
    ("lehnten", "ab"): ("ablehnen", "Trennbares Verb", "reddetmek", "to reject / decline"),
    ("lehnt", "ab"): ("ablehnen", "Trennbares Verb", "reddeder", "rejects"),
    ("kamen", "vor"): ("vorkommen", "Trennbares Verb", "yer almak / geçmek / bulunmak", "to appear / occur"),
    ("kommt", "vor"): ("vorkommen", "Trennbares Verb", "yer alır / geçer", "appears / occurs"),
    ("baut", "an"): ("anbauen", "Trennbares Verb", "yetiştirmek / ekmek", "to cultivate / grow"),
    ("bauen", "an"): ("anbauen", "Trennbares Verb", "yetiştirirler", "cultivate / grow"),
    ("dämmt", "ein"): ("eindämmen", "Trennbares Verb", "frenlemek / sınırlamak", "to curb / contain"),
    ("bürdet", "auf"): ("aufbürden", "Trennbares Verb", "yüklemek / bindirmek", "to burden / impose on"),
    ("hielten", "ab"): ("abhalten", "Trennbares Verb", "düzenlemek / icra etmek", "to hold (ceremony) / conduct"),
    ("bereitet", "vor"): ("vorbereiten", "Trennbares Verb", "hazırlamak", "to prepare"),
    ("bereiteten", "vor"): ("vorbereiten", "Trennbares Verb", "hazırladı", "prepared"),
    ("ruhen", "aus"): ("ausruhen", "Trennbares Verb", "dinlenmek", "to rest"),
    ("ruht", "aus"): ("ausruhen", "Trennbares Verb", "dinlenir", "rests"),
}

# Prepositional Contractions in German
DE_CONTRACTIONS = {
    "im": ("in dem", "Präposition + Artikel (Dativ)", "in / içinde", "in the"),
    "am": ("an dem", "Präposition + Artikel (Dativ)", "üzerinde / -de, -da", "at the / on the"),
    "zum": ("zu dem", "Präposition + Artikel (Dativ)", "-e, -a (yönelme)", "to the"),
    "zur": ("zu der", "Präposition + Artikel (Dativ Fem)", "-e, -a (yönelme)", "to the"),
    "beim": ("bei dem", "Präposition + Artikel (Dativ)", "sırasında / yanında / -de", "during / at the"),
    "vom": ("von dem", "Präposition + Artikel (Dativ)", "-den, -dan", "from the / of the"),
    "ins": ("in das", "Präposition + Artikel (Akkusativ)", "içine / -e, -a", "into the"),
    "ans": ("an das", "Präposition + Artikel (Akkusativ)", "-e, -a", "to the / onto the"),
}

# Common German Function Words
DE_FUNCTION_WORDS = {
    # Definite Articles
    "der": ("der", "Bestimmter Artikel (Mask / Dat-Fem / Gen-Plur)", "eril artikel / -in", "the"),
    "die": ("die", "Bestimmter Artikel (Fem / Plur)", "dişil / çoğul artikel", "the"),
    "das": ("das", "Bestimmter Artikel (Neut)", "nötr artikel", "the"),
    "den": ("der", "Bestimmter Artikel (Akk-Mask / Dat-Plur)", "eril belirtme / çoğul -e", "the"),
    "dem": ("der", "Bestimmter Artikel (Dat-Mask/Neut)", "eril/nötr -de, -e", "the"),
    "des": ("der", "Bestimmter Artikel (Gen-Mask/Neut)", "eril/nötr -in (tamlayan)", "of the"),

    # Indefinite Articles
    "ein": ("ein", "Unbestimmter Artikel (Mask/Neut)", "bir", "a / an"),
    "eine": ("ein", "Unbestimmter Artikel (Fem)", "bir", "a / an"),
    "einen": ("ein", "Unbestimmter Artikel (Akk-Mask)", "bir (belirtme)", "a / an"),
    "einem": ("ein", "Unbestimmter Artikel (Dat-Mask/Neut)", "bir (yönelme/bulunma)", "a / an"),
    "einer": ("ein", "Unbestimmter Artikel (Dat/Gen-Fem)", "bir (dişil -e / -in)", "a / an"),
    "eines": ("ein", "Unbestimmter Artikel (Gen-Mask/Neut)", "bir (tamlayan)", "of a"),

    # Prepositions
    "in": ("in", "Präposition", "içinde / -de, -da", "in / into"),
    "an": ("an", "Präposition", "yanında / üzerinde / -de", "at / on"),
    "auf": ("auf", "Präposition", "üzerinde / -e doğru", "on / upon"),
    "aus": ("aus", "Präposition", "-den, -dan / dışından", "from / out of"),
    "mit": ("mit", "Präposition (Dativ)", "ile / birlikte", "with"),
    "nach": ("nach", "Präposition (Dativ)", "-e doğru / sonra / göre", "after / towards / according to"),
    "von": ("von", "Präposition (Dativ)", "-den / tarafından / -in", "of / from / by"),
    "zu": ("zu", "Präposition (Dativ) / Partikel", "-e doğru / çok / mastar eki", "to / too"),
    "bei": ("bei", "Präposition (Dativ)", "yanında / esnasında", "at / near / with"),
    "über": ("über", "Präposition", "üzerinde / hakkında / aşkın", "over / about / above"),
    "unter": ("unter", "Präposition", "altında / arasında", "under / below / among"),
    "vor": ("vor", "Präposition", "önünde / önce", "in front of / before / ago"),
    "hinter": ("hinter", "Präposition", "arkasında", "behind"),
    "durch": ("durch", "Präposition (Akkusativ)", "aracılığıyla / içinden", "through / by"),
    "für": ("für", "Präposition (Akkusativ)", "için", "for"),
    "gegen": ("gegen", "Präposition (Akkusativ)", "karşı / sularında", "against / around"),
    "ohne": ("ohne", "Präposition (Akkusativ)", "-sız, -siz / olmadan", "without"),
    "um": ("um", "Präposition (Akkusativ)", "etrafında / saatte", "around / at"),

    # Conjunctions
    "und": ("und", "Konjunktion", "ve", "and"),
    "oder": ("oder", "Konjunktion", "veya / ya da", "or"),
    "aber": ("aber", "Konjunktion", "ama / fakat", "but"),
    "denn": ("denn", "Konjunktion", "çünkü", "because / for"),
    "sondern": ("sondern", "Konjunktion", "bilakis / aksine", "but rather"),
    "dass": ("dass", "Subjunktion", "ki / -dığı", "that"),
    "da": ("da", "Subjunktion / Adverb", "çünkü / orada", "since / because / there"),
    "weil": ("weil", "Subjunktion", "çünkü / -dığı için", "because"),
    "obwohl": ("obwohl", "Subjunktion", "-e rağmen", "although / even though"),
    "wenn": ("wenn", "Subjunktion", "eğer / -dığında", "if / when"),
    "als": ("als", "Konjunktion / Partikel", "olarak / -dığı zaman / -den", "as / when / than"),
    "wie": ("wie", "Konjunktion / Adverb", "gibi / nasıl", "like / as / how"),
    "während": ("während", "Subjunktion / Präposition", "iken / sırasında", "while / during"),

    # Adverbs & Pronouns
    "nicht": ("nicht", "Negationspartikel", "değil / -mez", "not"),
    "kein": ("kein", "Negationsartikel", "hiç / yok", "no / not any"),
    "keine": ("kein", "Negationsartikel (Fem/Plur)", "hiçbir / yok", "no / not any"),
    "sehr": ("sehr", "Gradadverb", "çok", "very"),
    "auch": ("auch", "Fokuspartikel", "da, de / ayrıca", "also / too"),
    "nur": ("nur", "Fokuspartikel", "sadece / yalnızca", "only"),
    "schon": ("schon", "Adverb", "zaten / çoktan", "already"),
    "noch": ("noch", "Adverb", "hâlâ / henüz / daha", "still / yet"),
    "oft": ("oft", "Temporaladverb", "sık sık", "often"),
    "immer": ("immer", "Temporaladverb", "her zaman / daima", "always"),
    "nie": ("nie", "Temporaladverb", "asla / hiçbir zaman", "never"),
    "hier": ("hier", "Lokaladverb", "burada / buraya", "here"),
    "dort": ("dort", "Lokaladverb", "orada / oraya", "there"),
    "so": ("so", "Adverb", "böyle / öyle", "so / thus"),
    "wieder": ("wieder", "Adverb", "tekrar / yeniden", "again"),
    "mehr": ("mehr", "Adverb / Indefinitum", "daha / daha fazla", "more"),
    "weniger": ("weniger", "Adverb", "daha az", "less"),
    "ganz": ("ganz", "Adverb / Adjektiv", "bütün / oldukça / tam", "quite / completely / whole"),
    "etwas": ("etwas", "Indefinitpronomen", "biraz / bir şey", "something / somewhat"),
    "nichts": ("nichts", "Indefinitpronomen", "hiçbir şey", "nothing"),
    "alles": ("alle", "Indefinitpronomen", "her şey / hepsi", "everything / all"),
    "alle": ("alle", "Indefinitpronomen (Plur)", "hepsi / tümü", "all / everyone"),
    "man": ("man", "Indefinitpronomen", "insan / kişi (genel özne)", "one / people"),
    "er": ("er", "Personalpronomen", "o (eril)", "he"),
    "sie": ("sie", "Personalpronomen", "o (dişil) / onlar", "she / they"),
    "es": ("es", "Personalpronomen", "o (nötr)", "it"),
    "wir": ("wir", "Personalpronomen", "biz", "we"),
    "ihr": ("ihr", "Personalpronomen / Possessiv", "siz / onun", "you (plur) / her"),
    "ihnen": ("sie", "Personalpronomen (Dativ)", "onlara", "to them"),
    "ihm": ("er", "Personalpronomen (Dativ)", "ona", "to him / to it"),
    "ihn": ("er", "Personalpronomen (Akkusativ)", "onu", "him / it"),
    "uns": ("wir", "Personalpronomen (Akk/Dat)", "bizi / bize", "us / to us"),
    "sich": ("sich", "Reflexivpronomen", "kendini / birbirini", "oneself / themselves"),
    "sein": ("sein", "Possessivartikel / Verb", "onun / olmak", "his / its / to be"),
    "seine": ("sein", "Possessivartikel (Fem/Plur)", "onun", "his / its"),
    "seiner": ("sein", "Possessivartikel", "onun", "his / its"),
    "seinem": ("sein", "Possessivartikel", "onun", "his / its"),
    "seinen": ("sein", "Possessivartikel", "onun", "his / its"),
    "ihr": ("ihr", "Possessivartikel", "onların / onun", "their / her"),
    "ihre": ("ihr", "Possessivartikel (Fem/Plur)", "onların / onun", "their / her"),
    "ihrer": ("ihr", "Possessivartikel", "onların / onun", "their / her"),
    "ihrem": ("ihr", "Possessivartikel", "onların / onun", "their / her"),
    "ihren": ("ihr", "Possessivartikel", "onların / onun", "their / her"),

    # Auxiliary / Copula: sein, haben, werden
    "ist": ("sein", "Kopulaverb (Präsens 3sg)", "-dır, -dir", "is"),
    "sind": ("sein", "Kopulaverb (Präsens 3pl)", "-dırlar, -dirler", "are"),
    "war": ("sein", "Kopulaverb (Präteritum 3sg)", "idi / oldu", "was"),
    "waren": ("sein", "Kopulaverb (Präteritum 3pl)", "idiler / oldular", "were"),
    "hat": ("haben", "Hilfsverb (Präsens 3sg)", "sahiptir / -miştir", "has"),
    "haben": ("haben", "Hilfsverb (Präsens 3pl / Infinitiv)", "sahip olmak / -mişlerdir", "have / to have"),
    "hatte": ("haben", "Hilfsverb (Präteritum 3sg)", "sahipti / -mişti", "had"),
    "hatten": ("haben", "Hilfsverb (Präteritum 3pl)", "sahiptiler / -miştiler", "had"),
    "wird": ("werden", "Hilfsverb (Präsens 3sg)", "oluyor / -ecek (gelecek/edilgen)", "becomes / will"),
    "werden": ("werden", "Hilfsverb (Präsens 3pl / Infinitiv)", "olmak / edilgen çatı", "become / will / are being"),
    "wurde": ("werden", "Hilfsverb (Präteritum 3sg)", "oldu / -ildi (edilgen geçmiş)", "became / was"),
    "wurden": ("werden", "Hilfsverb (Präteritum 3pl)", "oldular / -ildiler", "became / were"),
    "kann": ("können", "Modalverb (Präsens 3sg)", "-ebilir (yeterlilik)", "can"),
    "können": ("können", "Modalverb", "-ebilirler / -ebilmek", "can / to be able to"),
    "konnte": ("können", "Modalverb (Präteritum 3sg)", "-ebildi / -ebilirdi", "could"),
    "konnten": ("können", "Modalverb (Präteritum 3pl)", "-ebildiler", "could"),
    "muss": ("müssen", "Modalverb (Präsens 3sg)", "-meli, -malı (zorunluluk)", "must / has to"),
    "müssen": ("müssen", "Modalverb", "-meliler / -mek zorunda olmak", "must / have to"),
    "soll": ("sollen", "Modalverb (Präsens 3sg)", "-meli (görev/tavsiye)", "shall / is supposed to"),
    "sollen": ("sollen", "Modalverb", "-meliler", "shall / are supposed to"),
    "will": ("wollen", "Modalverb (Präsens 3sg)", "istiyor / niyetinde", "wants / intends to"),
    "wollen": ("wollen", "Modalverb", "istemek / niyetinde olmak", "want / intend to"),
}

# German Content Lexicon (Frequent Nouns & Adjectives)
DE_CONTENT_LEXICON = {
    # Nouns
    "kunst": ("Kunst", "Substantiv (Fem)", "sanat", "art"),
    "künstler": ("Künstler", "Substantiv (Mask)", "sanatçı", "artist"),
    "künstlern": ("Künstler", "Substantiv (Dat Plur)", "sanatçılara / sanatçılarla", "artists"),
    "malerei": ("Malerei", "Substantiv (Fem)", "resim sanatı", "painting / art"),
    "maler": ("Maler", "Substantiv (Mask)", "ressam", "painter"),
    "bild": ("Bild", "Substantiv (Neut)", "resim / tablo", "picture / painting"),
    "bilder": ("Bild", "Substantiv (Plur)", "resimler / tablolar", "pictures / paintings"),
    "bildern": ("Bild", "Substantiv (Dat Plur)", "resimlerle / tablolarda", "pictures"),
    "dichter": ("Dichter", "Substantiv (Mask)", "şair", "poet"),
    "gedicht": ("Gedicht", "Substantiv (Neut)", "şiir", "poem"),
    "gedichte": ("Gedicht", "Substantiv (Plur)", "şiirler", "poems"),
    "gedichten": ("Gedicht", "Substantiv (Dat Plur)", "şiirlerde", "poems"),
    "literatur": ("Literatur", "Substantiv (Fem)", "edebiyat", "literature"),
    "geschichte": ("Geschichte", "Substantiv (Fem)", "tarih / hikaye", "history / story"),
    "kultur": ("Kultur", "Substantiv (Fem)", "kültür", "culture"),
    "tradition": ("Tradition", "Substantiv (Fem)", "gelenek", "tradition"),
    "traditionen": ("Tradition", "Substantiv (Plur)", "gelenekler", "traditions"),
    "erbe": ("Erbe", "Substantiv (Neut)", "miras", "heritage"),
    "reise": ("Reise", "Substantiv (Fem)", "yolculuk / gezi", "journey / trip"),
    "reisen": ("Reise", "Substantiv (Plur)", "yolculuklar / geziler", "journeys"),
    "meer": ("Meer", "Substantiv (Neut)", "deniz", "sea"),
    "stadt": ("Stadt", "Substantiv (Fem)", "şehir / kent", "city"),
    "städte": ("Stadt", "Substantiv (Plur)", "şehirler", "cities"),
    "natur": ("Natur", "Substantiv (Fem)", "doğa", "nature"),
    "boot": ("Boot", "Substantiv (Neut)", "tekne / sandal", "boat"),
    "boote": ("Boot", "Substantiv (Plur)", "tekneler", "boats"),
    "pferd": ("Pferd", "Substantiv (Neut)", "at", "horse"),
    "holzpferd": ("Holzpferd", "Kompositum", "tahta at", "wooden horse"),
    "krieg": ("Krieg", "Substantiv (Mask)", "savaş", "war"),
    "mauer": ("Mauer", "Substantiv (Fem)", "sur / duvar", "wall"),
    "mauern": ("Mauer", "Substantiv (Plur)", "surlar / duvarlar", "walls"),
    "traum": ("Traum", "Substantiv (Mask)", "rüya / düş", "dream"),
    "träume": ("Traum", "Substantiv (Plur)", "rüyalar", "dreams"),
    "träumen": ("Traum", "Substantiv (Dat Plur)", "rüyalarda", "dreams"),
    "schlaf": ("Schlaf", "Substantiv (Mask)", "uyku", "sleep"),
    "gehirn": ("Gehirn", "Substantiv (Neut)", "beyin", "brain"),
    "gedächtnis": ("Gedächtnis", "Substantiv (Neut)", "bellek / hafıza", "memory"),
    "baum": ("Baum", "Substantiv (Mask)", "ağaç", "tree"),
    "bäume": ("Baum", "Substantiv (Plur)", "ağaçlar", "trees"),
    "bäumen": ("Baum", "Substantiv (Dat Plur)", "ağaçlarda", "trees"),
    "wald": ("Wald", "Substantiv (Mask)", "orman", "forest"),
    "tee": ("Tee", "Substantiv (Mask)", "çay", "tea"),
    "kaffee": ("Kaffee", "Substantiv (Mask)", "kahve", "coffee"),
    "tasse": ("Tasse", "Substantiv (Fem)", "fincan", "cup"),
    "glas": ("Glas", "Substantiv (Neut)", "bardak / cam", "glass"),
    "schatten": ("Schatten", "Substantiv (Mask)", "gölge", "shadow"),
    "musik": ("Musik", "Substantiv (Fem)", "müzik", "music"),
    "klang": ("Klang", "Substantiv (Mask)", "ses / tını", "sound / chime"),
    "klänge": ("Klang", "Substantiv (Plur)", "sesler / tınılar", "sounds"),
    "instrument": ("Instrument", "Substantiv (Neut)", "çalgı / enstrüman", "instrument"),
    "instrumente": ("Instrument", "Substantiv (Plur)", "çalgılar / enstrümanlar", "instruments"),
    "joghurt": ("Joghurt", "Substantiv (Mask/Neut)", "yoğurt", "yogurt"),
    "milch": ("Milch", "Substantiv (Fem)", "süt", "milk"),
    "duft": ("Duft", "Substantiv (Mask)", "koku / rayiha", "scent / aroma"),
    "stein": ("Stein", "Substantiv (Mask)", "taş", "stone"),
    "steine": ("Stein", "Substantiv (Plur)", "taşlar", "stones"),
    "steinen": ("Stein", "Substantiv (Dat Plur)", "taşlarda", "stones"),
    "höhle": ("Höhle", "Substantiv (Fem)", "mağara", "cave"),
    "höhlen": ("Höhle", "Substantiv (Plur)", "mağaralar", "caves"),
    "biene": ("Biene", "Substantiv (Fem)", "arı", "bee"),
    "bienen": ("Biene", "Substantiv (Plur)", "arılar", "bees"),
    "honig": ("Honig", "Substantiv (Mask)", "bal", "honey"),
    "öl": ("Öl", "Substantiv (Neut)", "yağ", "oil"),
    "olivenöl": ("Olivenöl", "Kompositum", "zeytinyağı", "olive oil"),
    "gold": ("Gold", "Substantiv (Neut)", "altın", "gold"),
    "pullover": ("Pullover", "Substantiv (Mask)", "kazak", "sweater"),
    "entscheidung": ("Entscheidung", "Substantiv (Fem)", "karar", "decision"),
    "entscheidungen": ("Entscheidung", "Substantiv (Plur)", "kararlar", "decisions"),
    "wahl": ("Wahl", "Substantiv (Fem)", "seçim", "choice"),
    "müdigkeit": ("Müdigkeit", "Substantiv (Fem)", "yorgunluk", "fatigue"),
    "entscheidungsmüdigkeit": ("Entscheidungsmüdigkeit", "Kompositum", "karar yorgunluğu", "decision fatigue"),
    "tempel": ("Tempel", "Substantiv (Mask)", "tapınak / mabet", "temple"),
    "säule": ("Säule", "Substantiv (Fem)", "sütun", "pillar / column"),
    "säulen": ("Säule", "Substantiv (Plur)", "sütunlar", "pillars / columns"),
    "jäger": ("Jäger", "Substantiv (Mask)", "avcı", "hunter"),
    "mensch": ("Mensch", "Substantiv (Mask)", "insan", "human / person"),
    "menschen": ("Mensch", "Substantiv (Plur/Akk)", "insanlar / insanı", "humans / people"),
    "leben": ("Leben", "Substantiv (Neut) / Verb", "hayat / yaşamak", "life / to live"),
    "zeit": ("Zeit", "Substantiv (Fem)", "zaman / vakit", "time"),
    "zeiten": ("Zeit", "Substantiv (Plur)", "zamanlar", "times"),
    "welt": ("Welt", "Substantiv (Fem)", "dünya", "world"),
    "jahrhundert": ("Jahrhundert", "Substantiv (Neut)", "yüzyıl", "century"),
    "jahr": ("Jahr", "Substantiv (Neut)", "yıl / sene", "year"),
    "jahre": ("Jahr", "Substantiv (Plur)", "yıllar", "years"),
    "jahren": ("Jahr", "Substantiv (Dat Plur)", "yıllarda / yıldan sonra", "years"),
    "tag": ("Tag", "Substantiv (Mask)", "gün", "day"),
    "tage": ("Tag", "Substantiv (Plur)", "günler", "days"),
    "tagen": ("Tag", "Substantiv (Dat Plur)", "günlerde", "days"),
    "nacht": ("Nacht", "Substantiv (Fem)", "gece", "night"),
    "ort": ("Ort", "Substantiv (Mask)", "yer / mekan", "place"),
    "orte": ("Ort", "Substantiv (Plur)", "yerler", "places"),
    "orten": ("Ort", "Substantiv (Dat Plur)", "yerlerde", "places"),

    # Adjectives
    "antik": ("antik", "Adjektiv", "antik / eski", "ancient"),
    "alt": ("alt", "Adjektiv", "eski / yaşlı", "old"),
    "alte": ("alt", "Adjektiv", "eski", "old"),
    "alten": ("alt", "Adjektiv", "eski", "old"),
    "neu": ("neu", "Adjektiv", "yeni", "new"),
    "neue": ("neu", "Adjektiv", "yeni", "new"),
    "neuen": ("neu", "Adjektiv", "yeni", "new"),
    "modern": ("modern", "Adjektiv", "modern / çağdaş", "modern"),
    "moderne": ("modern", "Adjektiv", "modern", "modern"),
    "modernen": ("modern", "Adjektiv", "modern", "modern"),
    "traditionell": ("traditionell", "Adjektiv", "geleneksel", "traditional"),
    "traditionelle": ("traditionell", "Adjektiv", "geleneksel", "traditional"),
    "berühmt": ("berühmt", "Adjektiv", "ünlü / meşhur", "famous"),
    "groß": ("groß", "Adjektiv", "büyük", "large / big"),
    "große": ("groß", "Adjektiv", "büyük", "large / big"),
    "großen": ("groß", "Adjektiv", "büyük", "large / big"),
    "klein": ("klein", "Adjektiv", "küçük", "small / little"),
    "kleine": ("klein", "Adjektiv", "küçük", "small / little"),
    "kleinen": ("klein", "Adjektiv", "küçük", "small / little"),
    "blau": ("blau", "Adjektiv", "mavi", "blue"),
    "blaue": ("blau", "Adjektiv", "mavi", "blue"),
    "blauen": ("blau", "Adjektiv", "mavi", "blue"),
    "tief": ("tief", "Adjektiv", "derin", "deep / profound"),
    "tiefe": ("tief", "Adjektiv", "derin", "deep"),
    "tiefen": ("tief", "Adjektiv", "derin", "deep"),
    "einfach": ("einfach", "Adjektiv", "basit / sade / kolay", "simple / plain"),
    "einfache": ("einfach", "Adjektiv", "basit / sade", "simple / plain"),
    "wichtig": ("wichtig", "Adjektiv", "önemli", "important"),
    "reich": ("reich", "Adjektiv", "zengin", "rich"),
    "frisch": ("frisch", "Adjektiv", "taze", "fresh"),
    "frische": ("frisch", "Adjektiv", "taze", "fresh"),
    "frischen": ("frisch", "Adjektiv", "taze", "fresh"),
    "erste": ("erste", "Ordinalzahl", "ilk / birinci", "first"),
    "ersten": ("erste", "Ordinalzahl", "ilk / birinci", "first"),
}


def analyze_german_token(token, sentence_de="", sentence_tr="", curated_vocab=None):
    clean = re.sub(r"[^\w'-]", "", token, flags=re.UNICODE).strip()
    if not clean:
        return None

    raw_lower = clean.lower()

    # 1. Curated Vocabulary Match
    if curated_vocab and raw_lower in curated_vocab:
        v = curated_vocab[raw_lower]
        tr_trans = v.get("translations", {}).get("tr") or clean
        return {
            "token": clean,
            "lemma": v.get("target") or clean,
            "pos": "Schlüsselwort (Lektionswortschatz)",
            "gloss": {"tr": tr_trans, "en": v.get("translations", {}).get("en") or clean},
            "note": f"\"{clean}\" — {tr_trans}"
        }

    # 2. Check Separable Verb in Sentence Context
    if sentence_de:
        s_words = [re.sub(r"[^\w'-]", "", w).lower() for w in sentence_de.split()]
        for (v_form, pfx), (inf, pos, tr_m, en_m) in SEPARABLE_VERB_PAIRS.items():
            if v_form in s_words and pfx in s_words:
                if raw_lower == v_form:
                    return {
                        "token": clean,
                        "lemma": inf,
                        "pos": "Trennbares Verb (Stamm)",
                        "gloss": {"tr": tr_m, "en": en_m},
                        "note": f"{clean} ... {pfx} (ayrılabilen fiil: {inf} [\"{tr_m}\"])"
                    }
                elif raw_lower == pfx:
                    return {
                        "token": clean,
                        "lemma": inf,
                        "pos": "Trennbares Verb (Präfix)",
                        "gloss": {"tr": f"{inf} ({tr_m})", "en": f"{inf} ({en_m})"},
                        "note": f"{v_form} ... {clean} (ayrılabilen fiil öneki: {inf})"
                    }

    # 3. Check Prepositional Contractions (im, am, zum, zur, beim, vom, ins)
    if raw_lower in DE_CONTRACTIONS:
        exp, pos, tr_m, en_m = DE_CONTRACTIONS[raw_lower]
        return {
            "token": clean,
            "lemma": exp,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m},
            "note": f"{clean} = {exp} (edat + artikel kaynaşması)"
        }

    # 4. Check German Function Words
    if raw_lower in DE_FUNCTION_WORDS:
        lemma, pos, tr_m, en_m = DE_FUNCTION_WORDS[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

    # 5. Check Content Lexicon
    if raw_lower in DE_CONTENT_LEXICON:
        lemma, pos, tr_m, en_m = DE_CONTENT_LEXICON[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

    # 6. Proper Noun Heuristic
    is_cap = clean[0].isupper() and clean[0] != clean[0].lower()
    return {
        "token": clean,
        "lemma": clean,
        "pos": "Eigenname" if is_cap and "'" in clean else ("Substantiv" if is_cap else "Wort"),
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


def process_german_articles(articles_path="articles.json"):
    print(f"Reading {articles_path} for German token-gloss generation...")
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    global_vocab = {}
    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("de", {}).items():
            for v in lvl_data.get("vocab", []):
                tgt = v.get("target", "").strip().lower()
                if tgt:
                    global_vocab[tgt] = v

    print(f"Loaded {len(global_vocab)} German curated vocab items.")

    total_sents = 0
    total_tokens_generated = 0

    for art_idx, art in enumerate(articles):
        art_id = art["id"]
        de_data = art.get("languages", {}).get("de", {})

        for lvl in ["A1", "A2", "B1", "B2", "C1"]:
            lvl_data = de_data.get(lvl, {})
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
                        gloss_obj = analyze_german_token(
                            clean_tok,
                            sentence_de=target_sent,
                            sentence_tr=tr_trans,
                            curated_vocab=art_vocab
                        )
                        if gloss_obj:
                            tokens_list.append(gloss_obj)

                    s["tokens"] = tokens_list
                    total_tokens_generated += len(tokens_list)

    print(f"\nCompleted German Generation!")
    print(f"Total German Sentences Processed: {total_sents}")
    print(f"Total German Tokens with Contextual Gloss: {total_tokens_generated}")

    print(f"\nWriting back to {articles_path}...")
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ Successfully updated articles.json with German token-gloss data.")


if __name__ == "__main__":
    process_german_articles()
