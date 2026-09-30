#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Token-Gloss Generator for French (Leenardo).
Generates context-aware token glosses across all articles and CEFR levels.
Decomposes elisions (d'inspiration, l'héritage, s'assujettir, c'est, qu'Anatolie),
handles contracted articles (au, aux, du, des), and verbal agreement.
"""

import json
import re
import os
import sys

# Elision prefixes in French: prefix -> (expanded_form, pos, meaning_tr, meaning_en)
ELISION_PREFIXES = {
    "d'": ("de", "Préposition élidée (de)", "-den / -in", "of / from"),
    "d’": ("de", "Préposition élidée (de)", "-den / -in", "of / from"),
    "l'": ("le / la", "Article défini élidé", "o (belirli artikel)", "the"),
    "l’": ("le / la", "Article défini élidé", "o (belirli artikel)", "the"),
    "s'": ("se", "Pronom réfléchi élidé", "kendini / birbirini", "oneself / each other"),
    "s’": ("se", "Pronom réfléchi élidé", "kendini / birbirini", "oneself / each other"),
    "c'": ("ce", "Pronom démonstratif élidé", "bu / o", "this / it"),
    "c’": ("ce", "Pronom démonstratif élidé", "bu / o", "this / it"),
    "qu'": ("que", "Conjonction / Relatif élidé", "ki / -dığı", "that / which"),
    "qu’": ("que", "Conjonction / Relatif élidé", "ki / -dığı", "that / which"),
    "n'": ("ne", "Particule de négation élidée", "olumsuzluk eki", "not"),
    "n’": ("ne", "Particule de négation élidée", "olumsuzluk eki", "not"),
    "j'": ("je", "Pronom sujet élidé", "ben", "I"),
    "j’": ("je", "Pronom sujet élidé", "ben", "I"),
    "m'": ("me", "Pronom objet élidé", "bana / beni", "me / to me"),
    "m’": ("me", "Pronom objet élidé", "bana / beni", "me / to me"),
    "t'": ("te", "Pronom objet élidé", "sana / seni", "you / to you"),
    "t’": ("te", "Pronom objet élidé", "sana / seni", "you / to you"),
}

# Contracted Articles in French
FRENCH_CONTRACTIONS = {
    "au": ("à le", "Article contracté (à + le)", "-e, -a (yönelme/bulunma)", "to the / in the"),
    "aux": ("à les", "Article contracté (à + les)", "-e, -a (çoğul yönelme)", "to the (plural)"),
    "du": ("de le", "Article contracté / partitif (de + le)", "-in / -den (tamlayan/ayrılma)", "of the / from the / some"),
    "des": ("de les", "Article contracté / indéfini (de + les)", "-in / -den / belgisiz çoğul", "of the / from the / some"),
}

# Common French Function Words
FR_FUNCTION_WORDS = {
    # Definite Articles
    "le": ("le", "Article défini (Masc)", "eril artikel", "the (masc)"),
    "la": ("le", "Article défini (Fem)", "dişil artikel", "the (fem)"),
    "les": ("le", "Article défini (Plur)", "çoğul artikel", "the (plural)"),

    # Indefinite Articles
    "un": ("un", "Article indéfini (Masc)", "bir (eril)", "a / an (masc)"),
    "une": ("un", "Article indéfini (Fem)", "bir (dişil)", "a / an (fem)"),

    # Prepositions
    "de": ("de", "Préposition", "-in / -den / hakkında", "of / from"),
    "à": ("à", "Préposition", "-e, -a / -de, -da", "to / at / in"),
    "en": ("en", "Préposition / Pronom", "içinde / -de / bundan", "in / by / of it"),
    "dans": ("dans", "Préposition", "içinde / -de", "in / inside"),
    "par": ("par", "Préposition", "tarafından / ile / üzerinden", "by / through"),
    "pour": ("pour", "Préposition", "için / amacıyla", "for / in order to"),
    "sur": ("sur", "Préposition", "üzerinde / hakkında", "on / upon / about"),
    "sous": ("sous", "Préposition", "altında", "under / beneath"),
    "avec": ("avec", "Préposition", "ile / birlikte", "with"),
    "sans": ("sans", "Préposition", "-sız, -siz / olmadan", "without"),
    "vers": ("vers", "Préposition", "-e doğru / sularında", "towards / around"),
    "chez": ("chez", "Préposition", "-in evinde / nezdinde", "at the home/place of"),
    "pendant": ("pendant", "Préposition", "sırasında / boyunca", "during / while"),
    "selon": ("selon", "Préposition", "-e göre", "according to"),
    "entre": ("entre", "Préposition", "arasında", "between / among"),

    # Conjunctions
    "et": ("et", "Conjonction", "ve", "and"),
    "ou": ("ou", "Conjonction", "veya / ya da", "or"),
    "où": ("où", "Pronom relatif / Adverbe", "nerede / olduğu yer / zaman", "where / when"),
    "mais": ("mais", "Conjonction", "ama / fakat", "but"),
    "donc": ("donc", "Conjonction / Adverbe", "bu nedenle / öyleyse", "therefore / so"),
    "or": ("or", "Conjonction", "oysaki / nitekim", "now / whereas"),
    "ni": ("ni", "Conjonction", "ne de", "neither / nor"),
    "car": ("car", "Conjonction", "çünkü / zira", "because / for"),
    "que": ("que", "Conjonction / Relatif", "ki / olan / -dığı", "that / which"),
    "qui": ("qui", "Pronom relatif", "ki o (özne) / kim", "who / which"),
    "si": ("si", "Conjonction / Adverbe", "eğer / o kadar", "if / whether / so"),
    "comme": ("comme", "Conjonction / Adverbe", "gibi / olarak", "as / like"),
    "quand": ("quand", "Conjonction", "zaman / -dığında", "when"),
    "lorsque": ("lorsque", "Conjonction", "-dığı zaman / iken", "when / while"),
    "puisque": ("puisque", "Conjonction", "mademki / -dığı için", "since / seeing that"),

    # Adverbs & Pronouns
    "ne": ("ne", "Particule de négation", "olumsuzluk parçacığı", "not"),
    "pas": ("pas", "Adverbe de négation", "değil / -mez", "not"),
    "plus": ("plus", "Adverbe", "daha / artık (olumsuzda)", "more / no more"),
    "moins": ("moins", "Adverbe", "daha az", "less"),
    "très": ("très", "Adverbe", "çok", "very"),
    "bien": ("bien", "Adverbe", "iyi / pek çok", "well / indeed"),
    "aussi": ("aussi", "Adverbe", "da, de / ayrıca / o kadar", "also / as well / so"),
    "même": ("même", "Adverbe / Adjectif", "hatta / bile / aynı", "even / same"),
    "toujours": ("toujours", "Adverbe", "her zaman / daima / hâlâ", "always / still"),
    "jamais": ("jamais", "Adverbe", "asla / hiçbir zaman", "never / ever"),
    "souvent": ("souvent", "Adverbe", "sık sık", "often"),
    "déjà": ("déjà", "Adverbe", "zaten / çoktan / daha önce", "already"),
    "encore": ("encore", "Adverbe", "hâlâ / henüz / bir daha", "still / yet / again"),
    "ici": ("ici", "Adverbe", "burada / buraya", "here"),
    "là": ("là", "Adverbe", "orada / oraya", "there"),
    "tout": ("tout", "Adjectif / Pronom (Masc)", "bütün / her şey", "all / everything"),
    "toute": ("tout", "Adjectif (Fem)", "bütün / tüm", "all / whole"),
    "tous": ("tout", "Pronom / Adjectif (Plur)", "hepsi / herkes", "all / everyone"),
    "toutes": ("tout", "Pronom / Adjectif (Fem Plur)", "hepsi / tümü", "all"),
    "autre": ("autre", "Adjectif / Pronom", "başka / diğer", "other / another"),
    "autres": ("autre", "Adjectif / Pronom (Plur)", "diğerleri / başka", "others"),
    "même": ("même", "Adjectif", "aynı", "same"),
    "ce": ("ce", "Démonstratif (Masc)", "bu / şu", "this / that"),
    "cet": ("ce", "Démonstratif (Masc ön-ünlü)", "bu / şu", "this / that"),
    "cette": ("ce", "Démonstratif (Fem)", "bu / şu", "this / that"),
    "ces": ("ce", "Démonstratif (Plur)", "bunlar / şunlar", "these / those"),
    "il": ("il", "Pronom sujet", "o (eril)", "he / it"),
    "elle": ("elle", "Pronom sujet", "o (dişil)", "she / it"),
    "ils": ("il", "Pronom sujet (Plur)", "onlar (eril)", "they"),
    "elles": ("elle", "Pronom sujet (Plur)", "onlar (dişil)", "they"),
    "nous": ("nous", "Pronom sujet / objet", "biz / bizi / bize", "we / us"),
    "vous": ("vous", "Pronom sujet / objet", "siz / sizi / size", "you"),
    "on": ("on", "Pronom indéfini", "biri / insan / biz (genel)", "one / we / people"),
    "se": ("se", "Pronom réfléchi", "kendini / birbirini", "oneself / each other"),
    "son": ("son", "Possessif (Masc)", "onun", "his / her / its"),
    "sa": ("son", "Possessif (Fem)", "onun", "his / her / its"),
    "ses": ("son", "Possessif (Plur)", "onun", "his / her / its"),
    "leur": ("leur", "Possessif / Pronom", "onların / onlara", "their / to them"),
    "leurs": ("leur", "Possessif (Plur)", "onların", "their"),
    "notre": ("notre", "Possessif", "bizim", "our"),
    "nos": ("notre", "Possessif (Plur)", "bizim", "our"),
    "votre": ("votre", "Possessif", "sizin", "your"),
    "vos": ("votre", "Possessif (Plur)", "sizin", "your"),

    # Auxiliary / Copula: être / avoir
    "est": ("être", "Verbe copule (Présent 3sg)", "-dır, -dir", "is"),
    "sont": ("être", "Verbe copule (Présent 3pl)", "-dırlar, -dirler", "are"),
    "était": ("être", "Verbe copule (Imparfait 3sg)", "idi / idi", "was"),
    "étaient": ("être", "Verbe copule (Imparfait 3pl)", "idiler", "were"),
    "fut": ("être", "Verbe copule (Passé simple 3sg)", "oldu / idi", "was"),
    "furent": ("être", "Verbe copule (Passé simple 3pl)", "oldular", "were"),
    "été": ("être", "Verbe (Participe passé)", "olmuş / bulunmuş", "been"),
    "être": ("être", "Verbe (Infinitif)", "olmak", "to be"),
    "a": ("avoir", "Verbe auxiliaire (Présent 3sg)", "sahiptir / vardır", "has"),
    "ont": ("avoir", "Verbe auxiliaire (Présent 3pl)", "sahiptirler / vardır", "have"),
    "avait": ("avoir", "Verbe auxiliaire (Imparfait 3sg)", "sahipti / vardı", "had"),
    "avaient": ("avoir", "Verbe auxiliaire (Imparfait 3pl)", "sahiptiler / vardı", "had"),
    "eu": ("avoir", "Verbe (Participe passé)", "sahip olunmuş / geçirilmiş", "had"),
    "avoir": ("avoir", "Verbe (Infinitif)", "sahip olmak", "to have"),
    "fait": ("faire", "Verbe (Présent 3sg / Participe)", "yapar / yapılmış", "makes / does / done"),
    "font": ("faire", "Verbe (Présent 3pl)", "yaparlar", "make / do"),
    "faire": ("faire", "Verbe (Infinitif)", "yapmak / etmek", "to make / do"),
    "peut": ("pouvoir", "Verbe modal (Présent 3sg)", "-ebilir (yeterlilik)", "can"),
    "peuvent": ("pouvoir", "Verbe modal (Présent 3pl)", "-ebilirler", "can"),
    "pouvoir": ("pouvoir", "Verbe (Infinitif)", "-ebilmek", "to be able to"),
}

# French Content Lexicon (Frequent Nouns & Adjectives)
FR_CONTENT_LEXICON = {
    # Nouns
    "art": ("art", "Nom (Masc)", "sanat", "art"),
    "artiste": ("artiste", "Nom", "sanatçı", "artist"),
    "artistes": ("artiste", "Nom (Plur)", "sanatçılar", "artists"),
    "peinture": ("peinture", "Nom (Fem)", "resim / boyama", "painting"),
    "peintures": ("peinture", "Nom (Fem Plur)", "resimler / tablolar", "paintings"),
    "peintre": ("peintre", "Nom (Masc)", "ressam", "painter"),
    "poète": ("poète", "Nom (Masc)", "şair", "poet"),
    "poètes": ("poète", "Nom (Plur)", "şairler", "poets"),
    "poésie": ("poésie", "Nom (Fem)", "şiir", "poetry"),
    "poème": ("poème", "Nom (Masc)", "şiir", "poem"),
    "poèmes": ("poème", "Nom (Plur)", "şiirler", "poems"),
    "littérature": ("littérature", "Nom (Fem)", "edebiyat", "literature"),
    "histoire": ("histoire", "Nom (Fem)", "tarih / hikaye", "history / story"),
    "culture": ("culture", "Nom (Fem)", "kültür", "culture"),
    "tradition": ("tradition", "Nom (Fem)", "gelenek", "tradition"),
    "traditions": ("tradition", "Nom (Plur)", "gelenekler", "traditions"),
    "héritage": ("héritage", "Nom (Masc)", "miras", "heritage"),
    "voyage": ("voyage", "Nom (Masc)", "yolculuk / seyahat", "journey / trip"),
    "voyages": ("voyage", "Nom (Plur)", "yolculuklar", "journeys"),
    "périple": ("périple", "Nom (Masc)", "uzun yolculuk / sefer", "voyage / tour"),
    "périples": ("périple", "Nom (Plur)", "seferler", "voyages"),
    "mer": ("mer", "Nom (Fem)", "deniz", "sea"),
    "ville": ("ville", "Nom (Fem)", "şehir / kent", "city"),
    "villes": ("ville", "Nom (Plur)", "şehirler", "cities"),
    "nature": ("nature", "Nom (Fem)", "doğa", "nature"),
    "bateau": ("bateau", "Nom (Masc)", "tekne / gemi", "boat"),
    "bateaux": ("bateau", "Nom (Plur)", "tekneler / gemiler", "boats"),
    "cheval": ("cheval", "Nom (Masc)", "at", "horse"),
    "guerre": ("guerre", "Nom (Fem)", "savaş", "war"),
    "mur": ("mur", "Nom (Masc)", "duvar", "wall"),
    "murs": ("mur", "Nom (Plur)", "duvarlar / surlar", "walls"),
    "rêve": ("rêve", "Nom (Masc)", "rüya / düş", "dream"),
    "rêves": ("rêve", "Nom (Plur)", "rüyalar", "dreams"),
    "sommeil": ("sommeil", "Nom (Masc)", "uyku", "sleep"),
    "cerveau": ("cerveau", "Nom (Masc)", "beyin", "brain"),
    "mémoire": ("mémoire", "Nom (Fem)", "bellek / hafıza", "memory"),
    "arbre": ("arbre", "Nom (Masc)", "ağaç", "tree"),
    "arbres": ("arbre", "Nom (Plur)", "ağaçlar", "trees"),
    "forêt": ("forêt", "Nom (Fem)", "orman", "forest"),
    "thé": ("thé", "Nom (Masc)", "çay", "tea"),
    "café": ("café", "Nom (Masc)", "kahve", "coffee"),
    "tasse": ("tasse", "Nom (Fem)", "fincan", "cup"),
    "verre": ("verre", "Nom (Masc)", "bardak / cam", "glass"),
    "ombre": ("ombre", "Nom (Fem)", "gölge", "shadow"),
    "ombres": ("ombre", "Nom (Plur)", "gölgeler", "shadows"),
    "musique": ("musique", "Nom (Fem)", "müzik", "music"),
    "son": ("son", "Nom (Masc)", "ses", "sound"),
    "sons": ("son", "Nom (Plur)", "sesler", "sounds"),
    "instrument": ("instrument", "Nom (Masc)", "çalgı / enstrüman", "instrument"),
    "instruments": ("instrument", "Nom (Plur)", "çalgılar / enstrümanlar", "instruments"),
    "yaourt": ("yaourt", "Nom (Masc)", "yoğurt", "yogurt"),
    "lait": ("lait", "Nom (Masc)", "süt", "milk"),
    "odeur": ("odeur", "Nom (Fem)", "koku", "scent / smell"),
    "pierre": ("pierre", "Nom (Fem)", "taş", "stone"),
    "pierres": ("pierre", "Nom (Plur)", "taşlar", "stones"),
    "grotte": ("grotte", "Nom (Fem)", "mağara", "cave"),
    "grottes": ("grotte", "Nom (Plur)", "mağaralar", "caves"),
    "abeille": ("abeille", "Nom (Fem)", "arı", "bee"),
    "abeilles": ("abeille", "Nom (Plur)", "arılar", "bees"),
    "miel": ("miel", "Nom (Masc)", "bal", "honey"),
    "olive": ("olive", "Nom (Fem)", "zeytin", "olive"),
    "huile": ("huile", "Nom (Fem)", "yağ", "oil"),
    "or": ("or", "Nom (Masc)", "altın", "gold"),
    "pull": ("pull", "Nom (Masc)", "kazak", "sweater"),
    "décision": ("décision", "Nom (Fem)", "karar", "decision"),
    "décisions": ("décision", "Nom (Plur)", "kararlar", "decisions"),
    "choix": ("choix", "Nom (Masc)", "seçim", "choice"),
    "fatigue": ("fatigue", "Nom (Fem)", "yorgunluk", "fatigue"),
    "temple": ("temple", "Nom (Masc)", "tapınak / mabet", "temple"),
    "monument": ("monument", "Nom (Masc)", "anıt", "monument"),
    "pilier": ("pilier", "Nom (Masc)", "sütun", "pillar"),
    "piliers": ("pilier", "Nom (Plur)", "sütunlar", "pillars"),
    "chasseur": ("chasseur", "Nom (Masc)", "avcı", "hunter"),
    "chasseurs": ("chasseur", "Nom (Plur)", "avcılar", "hunters"),
    "homme": ("homme", "Nom (Masc)", "insan / adam", "man / human"),
    "hommes": ("homme", "Nom (Plur)", "insanlar / adamlar", "men / humans"),
    "vie": ("vie", "Nom (Fem)", "hayat / yaşam", "life"),
    "vies": ("vie", "Nom (Plur)", "hayatlar", "lives"),
    "temps": ("temps", "Nom (Masc)", "zaman / hava", "time / weather"),
    "monde": ("monde", "Nom (Masc)", "dünya", "world"),
    "siècle": ("siècle", "Nom (Masc)", "yüzyıl", "century"),
    "siècles": ("siècle", "Nom (Plur)", "yüzyıllar", "centuries"),
    "an": ("an", "Nom (Masc)", "yıl / sene", "year"),
    "année": ("année", "Nom (Fem)", "yıl", "year"),
    "années": ("année", "Nom (Plur)", "yıllar", "years"),
    "jour": ("jour", "Nom (Masc)", "gün", "day"),
    "jours": ("jour", "Nom (Plur)", "günler", "days"),
    "nuit": ("nuit", "Nom (Fem)", "gece", "night"),
    "lieu": ("lieu", "Nom (Masc)", "yer / mekan", "place"),
    "lieux": ("lieu", "Nom (Plur)", "yerler", "places"),
    "processus": ("processus", "Nom (Masc)", "süreç", "process"),
    "méthode": ("méthode", "Nom (Fem)", "yöntem", "method"),
    "méthodes": ("méthode", "Nom (Plur)", "yöntemler", "methods"),
    "inspiration": ("inspiration", "Nom (Fem)", "ilham", "inspiration"),
    "atelier": ("atelier", "Nom (Masc)", "atölye", "workshop / studio"),
    "éponge": ("éponge", "Nom (Fem)", "sünger", "sponge"),
    "éponges": ("éponge", "Nom (Plur)", "süngerler", "sponges"),

    # Adjectives
    "antique": ("antique", "Adjectif", "antik / kadim", "ancient"),
    "ancien": ("ancien", "Adjectif (Masc)", "eski / eski dönem", "old / former"),
    "ancienne": ("ancien", "Adjectif (Fem)", "eski", "old"),
    "nouveau": ("nouveau", "Adjectif (Masc)", "yeni", "new"),
    "nouvelle": ("nouveau", "Adjectif (Fem)", "yeni", "new"),
    "moderne": ("moderne", "Adjectif", "modern / çağdaş", "modern"),
    "traditionnel": ("traditionnel", "Adjectif (Masc)", "geleneksel", "traditional"),
    "traditionnelle": ("traditionnel", "Adjectif (Fem)", "geleneksel", "traditional"),
    "célèbre": ("célèbre", "Adjectif", "ünlü / meşhur", "famous"),
    "grand": ("grand", "Adjectif (Masc)", "büyük", "large / great"),
    "grande": ("grand", "Adjectif (Fem)", "büyük", "large / great"),
    "petit": ("petit", "Adjectif (Masc)", "küçük", "small / little"),
    "petite": ("petit", "Adjectif (Fem)", "küçük", "small / little"),
    "bleu": ("bleu", "Adjectif (Masc)", "mavi", "blue"),
    "bleue": ("bleu", "Adjectif (Fem)", "mavi", "blue"),
    "profond": ("profond", "Adjectif (Masc)", "derin", "deep / profound"),
    "profonde": ("profond", "Adjectif (Fem)", "derin", "deep / profound"),
    "simple": ("simple", "Adjectif", "basit / sade", "simple / plain"),
    "important": ("important", "Adjectif", "önemli", "important"),
    "riche": ("riche", "Adjectif", "zengin", "rich"),
    "frais": ("frais", "Adjectif (Masc)", "taze / serin", "fresh / cool"),
    "fraîche": ("frais", "Adjectif (Fem)", "taze", "fresh"),
    "premier": ("premier", "Ordinal (Masc)", "ilk / birinci", "first"),
    "première": ("premier", "Ordinal (Fem)", "ilk / birinci", "first"),
}


def analyze_french_token(token, sentence_fr="", sentence_tr="", curated_vocab=None):
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
            "pos": "Mot Clé (Vocabulaire de la Leçon)",
            "gloss": {"tr": tr_trans, "en": v.get("translations", {}).get("en") or clean},
            "note": f"\"{clean}\" — {tr_trans}"
        }

    # 2. Check French Contracted Articles (au, aux, du, des)
    if raw_lower in FRENCH_CONTRACTIONS:
        exp, pos, tr_m, en_m = FRENCH_CONTRACTIONS[raw_lower]
        return {
            "token": clean,
            "lemma": exp,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m},
            "note": f"{clean} = {exp} (article contracté)"
        }

    # 3. Check Elisions: d'inspiration, l'héritage, s'assujettir, c'est, l'art, etc.
    for el_pfx, (el_exp, el_pos, el_tr, el_en) in ELISION_PREFIXES.items():
        if raw_lower.startswith(el_pfx):
            base_part = clean[len(el_pfx):]
            base_low = base_part.lower()

            # Look up base part in lexicon or vocab
            base_info = FR_CONTENT_LEXICON.get(base_low) or FR_FUNCTION_WORDS.get(base_low)
            if base_info:
                lemma_base = base_info[0]
                tr_meaning = base_info[2]
                return {
                    "token": clean,
                    "lemma": lemma_base,
                    "pos": f"{base_info[1]} (avec {el_exp})",
                    "gloss": {"tr": f"{el_tr} {tr_meaning}", "en": f"{el_en} {base_info[3]}"},
                    "note": f"{clean} = {el_exp} + {lemma_base} (élision)"
                }
            else:
                return {
                    "token": clean,
                    "lemma": base_low,
                    "pos": f"Mot avec élision ({el_exp})",
                    "gloss": {"tr": f"{el_tr} {base_part}", "en": f"{el_en} {base_part}"},
                    "note": f"{clean} = {el_exp} + {base_part} (élision)"
                }

    # 4. Check French Function Words
    if raw_lower in FR_FUNCTION_WORDS:
        lemma, pos, tr_m, en_m = FR_FUNCTION_WORDS[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

    # 5. Check Content Lexicon
    if raw_lower in FR_CONTENT_LEXICON:
        lemma, pos, tr_m, en_m = FR_CONTENT_LEXICON[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

def make_turkish_plural(tr_text):
    if not tr_text:
        return ""
    parts = [p.strip() for p in tr_text.split("/")]
    res = []
    for part in parts:
        vowels = re.findall(r"[aeıioöuüAEIİOÖUÜ]", part)
        if vowels:
            last_v = vowels[-1].lower()
            if last_v in "aıou":
                res.append(part + "lar")
            else:
                res.append(part + "ler")
        else:
            res.append(part)
    return " / ".join(res)


    # 6. Check Regular Plural (-s / -x)
    if raw_lower.endswith("s") and len(raw_lower) > 3:
        cand = raw_lower[:-1]
        if cand in FR_CONTENT_LEXICON:
            lemma, pos, tr_m, en_m = FR_CONTENT_LEXICON[cand]
            # French adjectives agree in plural, but Turkish adjectives do not take plural suffixes!
            tr_plural = tr_m if "Adjectif" in pos else make_turkish_plural(tr_m)
            en_plural = en_m if en_m.endswith("s") else f"{en_m}s"
            return {
                "token": clean,
                "lemma": lemma,
                "pos": f"{pos} (Pluriel)",
                "gloss": {"tr": tr_plural, "en": en_plural}
            }

    # 7. Proper Noun Heuristic
    is_cap = clean[0].isupper() and clean[0] != clean[0].lower()
    return {
        "token": clean,
        "lemma": clean.lower(),
        "pos": "Nom Propre" if is_cap else "Mot",
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


def process_french_articles(articles_path="articles.json"):
    print(f"Reading {articles_path} for French token-gloss generation...")
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    global_vocab = {}
    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("fr", {}).items():
            for v in lvl_data.get("vocab", []):
                tgt = v.get("target", "").strip().lower()
                if tgt:
                    global_vocab[tgt] = v

    print(f"Loaded {len(global_vocab)} French curated vocab items.")

    total_sents = 0
    total_tokens_generated = 0

    for art_idx, art in enumerate(articles):
        art_id = art["id"]
        fr_data = art.get("languages", {}).get("fr", {})

        for lvl in ["A1", "A2", "B1", "B2", "C1"]:
            lvl_data = fr_data.get(lvl, {})
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
                        gloss_obj = analyze_french_token(
                            clean_tok,
                            sentence_fr=target_sent,
                            sentence_tr=tr_trans,
                            curated_vocab=art_vocab
                        )
                        if gloss_obj:
                            tokens_list.append(gloss_obj)

                    s["tokens"] = tokens_list
                    total_tokens_generated += len(tokens_list)

    print(f"\nCompleted French Generation!")
    print(f"Total French Sentences Processed: {total_sents}")
    print(f"Total French Tokens with Contextual Gloss: {total_tokens_generated}")

    print(f"\nWriting back to {articles_path}...")
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ Successfully updated articles.json with French token-gloss data.")


if __name__ == "__main__":
    process_french_articles()
