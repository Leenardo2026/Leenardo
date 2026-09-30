#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Token-Gloss Generator for Spanish (Leenardo).
Generates context-aware token glosses across all articles and CEFR levels.
Decomposes enclitic pronouns (convirtiéndolo, respirarla, alejarse),
handles contractions (al, del), verb conjugations, and gender/number agreement.
"""

import json
import re
import os
import sys
from pathlib import Path

# Add project root to sys.path to import curated lexicon data
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spanish_lexicon_data import ES_CURATED_MAP

try:
    from scripts.spanish_fallthrough_dict import ES_ADDITIONAL_FALLTHROUGH_MAP
except ImportError:
    try:
        from spanish_fallthrough_dict import ES_ADDITIONAL_FALLTHROUGH_MAP
    except ImportError:
        ES_ADDITIONAL_FALLTHROUGH_MAP = {}

# Clitic pronouns in Spanish
CLITIC_PRONOUNS = {
    "melo": "me it", "telo": "you it", "selo": "him/her it", "noslo": "us it",
    "me": "me / myself", "te": "you / yourself", "se": "himself / herself / itself / themselves / each other",
    "nos": "us / ourselves", "os": "you (plural)",
    "lo": "him / it (masc)", "la": "her / it (fem)",
    "los": "them (masc)", "las": "them (fem)",
    "le": "to him / to her", "les": "to them"
}

# Accent restoration map when clitic is stripped from gerunds
ACCENT_STRIP_MAP = {
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"
}

# Contractions
SPANISH_CONTRACTIONS = {
    "al": ("a el", "Contracción (a + el)", "to the / upon", "-e / -a (a + el)"),
    "del": ("de el", "Contracción (de + el)", "of the / from the", "-in / -den (de + el)")
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


# Spanish Function Words
ES_FUNCTION_WORDS = {
    # Negations & Quantifiers
    "no": ("no", "Adverbio de Negación", "no / not", "hayır / değil / -ma, -me"),
    "ni": ("ni", "Conjunción", "neither / nor / not even", "ne / ne de / bile"),
    "nada": ("nada", "Pronombre Indefinido", "nothing / anything", "hiçbir şey"),
    "nadie": ("nadie", "Pronombre Indefinido", "nobody / no one", "hiç kimse"),
    "ningún": ("ninguno", "Determinante", "no / none / any", "hiçbir"),
    "ninguno": ("ninguno", "Pronombre", "none / no one", "hiçbiri"),
    "ninguna": ("ninguno", "Determinante / Pronombre", "none / no one", "hiçbiri"),
    "uno": ("uno", "Numeral / Pronombre", "one", "bir / biri"),
    "unos": ("un", "Artículo Indeterminado (Masc Plur)", "some / a few", "bazı / birkaç"),
    "unas": ("un", "Artículo Indeterminado (Fem Plur)", "some / a few", "bazı / birkaç"),
    "alguien": ("alguien", "Pronombre Indefinido", "someone / somebody", "biri / birisi"),
    "algo": ("algo", "Pronombre Indefinido / Adverbio", "something / somewhat", "bir şey / biraz"),
    "algún": ("alguno", "Determinante", "some / any", "bazı / herhangi bir"),
    "alguno": ("alguno", "Pronombre", "some / any", "bazısı / biri"),
    "alguna": ("alguno", "Determinante / Pronombre", "some / any", "bazı / biri"),
    "algunos": ("alguno", "Pronombre / Determinante (Plur)", "some / a few", "bazıları / birkaç"),
    "algunas": ("alguno", "Pronombre / Determinante (Fem Plur)", "some / a few", "bazıları / birkaç"),
    "varios": ("varios", "Determinante / Pronombre", "several / various", "çeşitli / birkaç"),
    "varias": ("varios", "Determinante / Pronombre (Fem)", "several / various", "çeşitli / birkaç"),

    # Pronouns (Subject & Object)
    "yo": ("yo", "Pronombre Personal (1sg)", "I", "ben"),
    "tú": ("tú", "Pronombre Personal (2sg)", "you", "sen"),
    "él": ("él", "Pronombre Personal (3sg masc)", "he / him", "o (eril)"),
    "ella": ("ella", "Pronombre Personal (3sg fem)", "she / her", "o (dişil)"),
    "ello": ("ello", "Pronombre Neutro", "it / that", "o / bu durum"),
    "usted": ("usted", "Pronombre Formal (2sg)", "you (formal)", "siz"),
    "nosotros": ("nosotros", "Pronombre Personal (1pl masc)", "we", "biz"),
    "nosotras": ("nosotros", "Pronombre Personal (1pl fem)", "we", "biz"),
    "vosotros": ("vosotros", "Pronombre Personal (2pl masc)", "you all", "siz"),
    "vosotras": ("vosotros", "Pronombre Personal (2pl fem)", "you all", "siz"),
    "ellos": ("ellos", "Pronombre Personal (3pl masc)", "they", "onlar"),
    "ellas": ("ellos", "Pronombre Personal (3pl fem)", "they", "onlar"),
    "ustedes": ("ustedes", "Pronombre Formal (2pl)", "you all", "sizler"),
    "me": ("me", "Pronombre (Objeto)", "me / to me / myself", "beni / bana / kendimi"),
    "te": ("te", "Pronombre (Objeto)", "you / to you / yourself", "seni / sana / kendini"),
    "se": ("se", "Pronombre Reflexivo", "himself / herself / itself / themselves / each other", "kendisi / kendini / (dönüşlülük zamiri)"),
    "nos": ("nos", "Pronombre (Objeto)", "us / to us / ourselves", "bizi / bize / kendimizi"),
    "os": ("os", "Pronombre (Objeto)", "you all (object)", "sizi / size"),
    "le": ("le", "Pronombre (Objeto Indirecto)", "to him / to her / to you", "ona / size"),
    "les": ("le", "Pronombre (Objeto Indirecto Plur)", "to them / to you all", "onlara / sizlere"),

    # Possessives
    "mi": ("mi", "Posesivo", "my", "benim"),
    "mis": ("mi", "Posesivo (Plural)", "my", "benim"),
    "tu": ("tu", "Posesivo", "your", "senin"),
    "tus": ("tu", "Posesivo (Plural)", "your", "senin"),
    "su": ("su", "Posesivo", "his / her / its / their / your", "onun / onların / sizin"),
    "sus": ("su", "Posesivo (Plural)", "his / her / its / their / your", "onun / onların / sizin"),
    "nuestro": ("nuestro", "Posesivo", "our (masc)", "bizim"),
    "nuestra": ("nuestro", "Posesivo (Fem)", "our (fem)", "bizim"),
    "nuestros": ("nuestro", "Posesivo (Plur)", "our", "bizim"),
    "nuestras": ("nuestro", "Posesivo (Fem Plur)", "our", "bizim"),

    # Articles
    "el": ("el", "Artículo Determinado (Masc)", "the (masc)", "o / eril artikel"),
    "la": ("el", "Artículo Determinado (Fem)", "the (fem)", "o / dişil artikel"),
    "los": ("el", "Artículo Determinado (Masc Plur)", "the (masc plur)", "onlar / çoğul eril"),
    "las": ("el", "Artículo Determinado (Fem Plur)", "the (fem plur)", "onlar / çoğul dişil"),
    "un": ("un", "Artículo Indeterminado (Masc)", "a / an (masc)", "bir (eril)"),
    "una": ("un", "Artículo Indeterminado (Fem)", "a / an (fem)", "bir (dişil)"),
    "lo": ("lo", "Artículo Neutro / Pronombre", "the (neutral) / it / that which", "nötr artikel / onu"),

    # Prepositions
    "de": ("de", "Preposición", "of / from", "-in / -den"),
    "en": ("en", "Preposición", "in / on / at", "-de / -da"),
    "a": ("a", "Preposición", "to / at", "-e / -a"),
    "por": ("por", "Preposición", "by / for / through", "tarafından / için / nedeniyle"),
    "para": ("para", "Preposición", "for / in order to", "için / amacıyla"),
    "con": ("con", "Preposición", "with", "ile / birlikte"),
    "sin": ("sin", "Preposición", "without", "-siz / olmadan"),
    "sobre": ("sobre", "Preposición", "on / about / over", "üzerinde / hakkında"),
    "entre": ("entre", "Preposición", "between / among", "arasında"),
    "hacia": ("hacia", "Preposición", "towards", "-e doğru"),
    "hasta": ("hasta", "Preposición", "until / up to / even", "-e kadar / hatta"),
    "desde": ("desde", "Preposición", "from / since", "-den beri / -den"),
    "según": ("según", "Preposición", "according to", "-e göre"),
    "contra": ("contra", "Preposición", "against", "karşı"),
    "durante": ("durante", "Preposición", "during", "sırasında / boyunca"),
    "mediante": ("mediante", "Preposición", "by means of / through", "aracılığıyla"),
    "tras": ("tras", "Preposición", "after / behind", "-den sonra / arkasında"),
    "bajo": ("bajo", "Preposición", "under / below", "altında"),
    "ante": ("ante", "Preposición", "before / in the face of", "karşısında / önünde"),

    # Conjunctions
    "y": ("y", "Conjunción", "and", "ve"),
    "e": ("y", "Conjunción", "and (before i-/hi-)", "ve"),
    "o": ("o", "Conjunción", "or", "veya / ya da"),
    "u": ("o", "Conjunción", "or (before o-/ho-)", "veya / ya da"),
    "pero": ("pero", "Conjunción", "but", "ama / fakat"),
    "sino": ("sino", "Conjunción", "but rather / except", "aksine / bilakis"),
    "porque": ("porque", "Conjunción", "because", "çünkü"),
    "aunque": ("aunque", "Conjunción", "although / even though", "-e rağmen / gerçi"),
    "si": ("si", "Conjunción", "if / whether", "eğer / ise"),
    "que": ("que", "Conjunción / Relativo", "that / which / who", "ki / olan / -dığı"),
    "como": ("como", "Conjunción / Adverbio", "as / like / how", "gibi / olarak"),
    "cuando": ("cuando", "Conjunción / Adverbio", "when", "zaman / iken"),
    "donde": ("donde", "Adverbio Relativo", "where", "nerede / olduğu yer"),
    "mientras": ("mientras", "Conjunción", "while / as long as", "iken / sürece"),

    # Adverbs & Pronouns
    "más": ("más", "Adverbio", "more / most", "daha / en çok"),
    "menos": ("menos", "Adverbio", "less / least", "daha az / en az"),
    "muy": ("muy", "Adverbio", "very", "çok"),
    "mucho": ("mucho", "Adverbio / Adjetivo", "much / a lot", "çok"),
    "muchos": ("mucho", "Adjetivo / Pronombre (Plur)", "many (masc)", "birçok / çok"),
    "muchas": ("mucho", "Adjetivo / Pronombre (Plur)", "many (fem)", "birçok / çok"),
    "poco": ("poco", "Adverbio / Adjetivo", "little / few", "az"),
    "pocos": ("poco", "Adjetivo (Plur)", "few (masc)", "az sayıda / birkaç"),
    "pocas": ("poco", "Adjetivo (Plur)", "few (fem)", "az sayıda / birkaç"),
    "tan": ("tan", "Adverbio", "so / as", "o kadar / öyle"),
    "tanto": ("tanto", "Adverbio / Adjetivo", "so much / so many", "o kadar / o derece"),
    "también": ("también", "Adverbio", "also / too", "da, de / ayrıca"),
    "tampoco": ("tampoco", "Adverbio", "neither / nor / not either", "de değil / ne de"),
    "ya": ("ya", "Adverbio", "already / now", "zaten / artık / hemen"),
    "todavía": ("todavía", "Adverbio", "still / yet", "hâlâ / henüz"),
    "aún": ("aún", "Adverbio", "still / even", "hâlâ / bile"),
    "siempre": ("siempre", "Adverbio", "always", "her zaman / daima"),
    "nunca": ("nunca", "Adverbio", "never", "asla / hiçbir zaman"),
    "jamás": ("jamás", "Adverbio", "never", "asla / katiyen"),
    "casi": ("casi", "Adverbio", "almost / nearly", "neredeyse / hemen hemen"),
    "sólo": ("sólo", "Adverbio", "only / solely", "sadece / yalnızca"),
    "solo": ("solo", "Adjetivo / Adverbio", "alone / only", "yalnız / sadece"),
    "bien": ("bien", "Adverbio", "well", "iyi / güzel"),
    "mal": ("mal", "Adverbio", "badly", "kötü"),
    "hoy": ("hoy", "Adverbio", "today", "bugün"),
    "ayer": ("ayer", "Adverbio", "yesterday", "dün"),
    "ahora": ("ahora", "Adverbio", "now", "şimdi"),
    "entonces": ("entonces", "Adverbio", "then / at that time", "o zaman / o halde"),
    "así": ("así", "Adverbio", "thus / so / in this way", "böylece / bu şekilde"),
    "antes": ("antes", "Adverbio", "before / earlier", "önce / eskiden"),
    "después": ("después", "Adverbio", "after / afterwards", "sonra"),
    "luego": ("luego", "Adverbio", "then / later", "daha sonra / sonra"),
    "pronto": ("pronto", "Adverbio", "soon", "yakında / erkenden"),
    "tarde": ("tarde", "Adverbio / Sustantivo", "late / afternoon", "geç / öğleden sonra"),
    "temprano": ("temprano", "Adverbio", "early", "erken"),
    "aquí": ("aquí", "Adverbio de Lugar", "here", "burada"),
    "acá": ("acá", "Adverbio de Lugar", "here / over here", "buraya / burada"),
    "allí": ("allí", "Adverbio de Lugar", "there", "orada"),
    "allá": ("allá", "Adverbio de Lugar", "over there", "orada / ötelerde"),
    "arriba": ("arriba", "Adverbio de Lugar", "up / above", "yukarıda"),
    "abajo": ("abajo", "Adverbio de Lugar", "down / below", "aşağıda"),
    "cerca": ("cerca", "Adverbio de Lugar", "near / close", "yakın / yakında"),
    "lejos": ("lejos", "Adverbio de Lugar", "far / away", "uzak / uzakta"),
    "dentro": ("dentro", "Adverbio de Lugar", "inside", "içinde / içeriye"),
    "fuera": ("fuera", "Adverbio de Lugar", "outside", "dışında / dışarıda"),
    "delante": ("delante", "Adverbio de Lugar", "in front", "önünde"),
    "detrás": ("detrás", "Adverbio de Lugar", "behind", "arkasında"),
    "alrededor": ("alrededor", "Adverbio de Lugar", "around", "etrafında / çevresinde"),
    "además": ("además", "Adverbio", "in addition / moreover", "ayrıca / üstelik"),
    "embargo": ("embargo", "Sustantivo / Locución", "sin embargo: however / nonetheless", "sin embargo: ancak / yine de"),
    "todo": ("todo", "Pronombre / Adjetivo", "all / everything", "her şey / bütün"),
    "toda": ("todo", "Adjetivo (Fem)", "all / whole", "bütün / tüm"),
    "todos": ("todo", "Pronombre / Adjetivo (Plur)", "all / everyone", "herkes / tüm"),
    "todas": ("todo", "Pronombre / Adjetivo (Fem Plur)", "all", "tüm / bütün"),
    "cada": ("cada", "Determinante", "each / every", "her bir / her"),
    "otro": ("otro", "Adjetivo / Pronombre", "other / another", "başka / diğer"),
    "otra": ("otro", "Adjetivo / Pronombre (Fem)", "other / another", "başka / diğer"),
    "otros": ("otro", "Adjetivo / Pronombre (Plur)", "others", "diğerleri / başka"),
    "otras": ("otro", "Adjetivo / Pronombre (Fem Plur)", "others", "diğerleri / başka"),
    "mismo": ("mismo", "Adjetivo", "same / self", "aynı / kendi"),
    "misma": ("mismo", "Adjetivo (Fem)", "same / self", "aynı / kendi"),
    "mismos": ("mismo", "Adjetivo (Plur)", "same / selves", "aynı / kendileri"),
    "mismas": ("mismo", "Adjetivo (Fem Plur)", "same / selves", "aynı / kendileri"),
    "este": ("este", "Demostrativo (Masc)", "this", "bu"),
    "esta": ("este", "Demostrativo (Fem)", "this", "bu"),
    "estos": ("este", "Demostrativo (Masc Plur)", "these", "bunlar"),
    "estas": ("este", "Demostrativo (Fem Plur)", "these", "bunlar"),
    "ese": ("ese", "Demostrativo (Masc)", "that", "şu / o"),
    "esa": ("ese", "Demostrativo (Fem)", "that", "şu / o"),
    "esos": ("ese", "Demostrativo (Masc Plur)", "those", "şunlar / onlar"),
    "esas": ("ese", "Demostrativo (Fem Plur)", "those", "şunlar / onlar"),
    "aquel": ("aquel", "Demostrativo", "that (over there)", "o / şu uzaktaki"),
    "aquella": ("aquel", "Demostrativo (Fem)", "that (over there)", "o / şu uzaktaki"),
    "aquellos": ("aquel", "Demostrativo (Plur)", "those (over there)", "onlar / uzaktakiler"),
    "aquellas": ("aquel", "Demostrativo (Fem Plur)", "those (over there)", "onlar / uzaktakiler"),

    # Essential Verbs: ser / estar / haber
    "es": ("ser", "Verbo Copulativo (Presente 3sg)", "is", "dır, dir"),
    "son": ("ser", "Verbo Copulativo (Presente 3pl)", "are", "dırlar, dirler"),
    "era": ("ser", "Verbo Copulativo (Imperfecto 3sg)", "was", "idi / idi"),
    "eran": ("ser", "Verbo Copulativo (Imperfecto 3pl)", "were", "idiler"),
    "fue": ("ser", "Verbo Copulativo (Pretérito 3sg)", "was", "oldu / idi"),
    "fueron": ("ser", "Verbo Copulativo (Pretérito 3pl)", "were", "oldular / idiler"),
    "ser": ("ser", "Verbo (Infinitivo)", "to be", "olmak"),
    "sido": ("ser", "Verbo (Participio)", "been", "olmuş"),
    "siendo": ("ser", "Verbo (Gerundio)", "being", "olarak / olarak"),
    "está": ("estar", "Verbo (Presente 3sg)", "is (state/location)", "bulunmaktadır / -dir"),
    "están": ("estar", "Verbo (Presente 3pl)", "are (state/location)", "bulunmaktadırlar"),
    "estaba": ("estar", "Verbo (Imperfecto 3sg)", "was (state/location)", "bulunuyordu"),
    "estaban": ("estar", "Verbo (Imperfecto 3pl)", "were (state/location)", "bulunuyorlardı"),
    "estuvo": ("estar", "Verbo (Pretérito 3sg)", "was (state/location)", "bulundu"),
    "estuvieron": ("estar", "Verbo (Pretérito 3pl)", "were (state/location)", "bulundular"),
    "estar": ("estar", "Verbo (Infinitivo)", "to be", "bulunmak / olmak"),
    "estado": ("estar", "Verbo (Participio) / Sustantivo", "been / state", "bulunmuş / durum"),
    "estando": ("estar", "Verbo (Gerundio)", "being", "bulunarak"),
    "hay": ("haber", "Verbo Impersonal (Presente)", "there is / there are", "vardır / var"),
    "había": ("haber", "Verbo Impersonal (Imperfecto)", "there was / there were / had", "vardı / -mıştı"),
    "hubo": ("haber", "Verbo Impersonal (Pretérito)", "there was / there were", "oldu / vuku buldu"),
    "ha": ("haber", "Verbo Auxiliar (Presente 3sg)", "has", "-mıştır / sahip"),
    "han": ("haber", "Verbo Auxiliar (Presente 3pl)", "have", "-mışlardır"),
    "hemos": ("haber", "Verbo Auxiliar (Presente 1pl)", "we have", "-dık / -mışız"),
    "haber": ("haber", "Verbo (Infinitivo)", "to have / to exist", "bulunmak / olmak"),
}

# Common Spanish Content Lexicon
ES_CONTENT_LEXICON = {
    # Nouns
    "arte": ("arte", "Sustantivo", "art", "sanat"),
    "artista": ("artista", "Sustantivo", "artist", "sanatçı"),
    "artistas": ("artista", "Sustantivo (Plural)", "artists", "sanatçılar"),
    "pintura": ("pintura", "Sustantivo", "painting", "resim / boyama"),
    "pinturas": ("pintura", "Sustantivo (Plural)", "paintings", "resimler / tablolar"),
    "pintor": ("pintor", "Sustantivo", "painter", "ressam"),
    "poeta": ("poeta", "Sustantivo", "poet", "şair"),
    "poetas": ("poeta", "Sustantivo (Plural)", "poets", "şairler"),
    "poesía": ("poesía", "Sustantivo", "poetry", "şiir"),
    "poema": ("poema", "Sustantivo", "poem", "şiir"),
    "poemas": ("poema", "Sustantivo (Plural)", "poems", "şiirler"),
    "literatura": ("literatura", "Sustantivo", "literature", "edebiyat"),
    "historia": ("historia", "Sustantivo", "history / story", "tarih / hikaye"),
    "cultura": ("cultura", "Sustantivo", "culture", "kültür"),
    "tradición": ("tradición", "Sustantivo", "tradition", "gelenek"),
    "tradiciones": ("tradición", "Sustantivo (Plural)", "traditions", "gelenekler"),
    "patrimonio": ("patrimonio", "Sustantivo", "heritage", "miras / kültürel miras"),
    "viaje": ("viaje", "Sustantivo", "journey / trip", "yolculuk / seyahat"),
    "viajes": ("viaje", "Sustantivo (Plural)", "journeys / trips", "yolculuklar / seyahatler"),
    "travesía": ("travesía", "Sustantivo", "crossing / voyage", "deniz yolculuğu / sefer"),
    "travesías": ("travesía", "Sustantivo (Plural)", "voyages", "seferler"),
    "mar": ("mar", "Sustantivo", "sea", "deniz"),
    "ciudad": ("ciudad", "Sustantivo", "city", "şehir / kent"),
    "ciudades": ("ciudad", "Sustantivo (Plural)", "cities", "şehirler"),
    "naturaleza": ("naturaleza", "Sustantivo", "nature", "doğa"),
    "barco": ("barco", "Sustantivo", "boat / ship", "tekne / gemi"),
    "barcos": ("barco", "Sustantivo (Plural)", "boats / ships", "tekneler / gemiler"),
    "caballo": ("caballo", "Sustantivo", "horse", "at"),
    "guerra": ("guerra", "Sustantivo", "war", "savaş"),
    "muralla": ("muralla", "Sustantivo", "wall / rampart", "sur / kale duvarı"),
    "murallas": ("muralla", "Sustantivo (Plural)", "walls / ramparts", "surlar"),
    "soldado": ("soldado", "Sustantivo", "soldier", "asker"),
    "soldados": ("soldado", "Sustantivo (Plural)", "soldiers", "askerler"),
    "ejército": ("ejército", "Sustantivo", "army", "ordu"),
    "sueño": ("sueño", "Sustantivo", "dream / sleep", "rüya / uyku"),
    "sueños": ("sueño", "Sustantivo (Plural)", "dreams", "rüyalar"),
    "cerebro": ("cerebro", "Sustantivo", "brain", "beyin"),
    "memoria": ("memoria", "Sustantivo", "memory", "hafıza / bellek"),
    "árbol": ("árbol", "Sustantivo", "tree", "ağaç"),
    "árboles": ("árbol", "Sustantivo (Plural)", "trees", "ağaçlar"),
    "bosque": ("bosque", "Sustantivo", "forest", "orman"),
    "té": ("té", "Sustantivo", "tea", "çay"),
    "café": ("café", "Sustantivo", "coffee", "kahve"),
    "taza": ("taza", "Sustantivo", "cup / mug", "fincan"),
    "vaso": ("vaso", "Sustantivo", "glass", "bardak"),
    "sombra": ("sombra", "Sustantivo", "shadow", "gölge"),
    "sombras": ("sombra", "Sustantivo (Plural)", "shadows", "gölgeler"),
    "música": ("música", "Sustantivo", "music", "müzik"),
    "sonido": ("sonido", "Sustantivo", "sound", "ses"),
    "sonidos": ("sonido", "Sustantivo (Plural)", "sounds", "sesler"),
    "instrumento": ("instrumento", "Sustantivo", "instrument", "çalgı / enstrüman"),
    "instrumentos": ("instrumento", "Sustantivo (Plural)", "instruments", "çalgılar / enstrümanlar"),
    "yogur": ("yogur", "Sustantivo", "yogurt", "yoğurt"),
    "leche": ("leche", "Sustantivo", "milk", "süt"),
    "olor": ("olor", "Sustantivo", "scent / smell", "koku"),
    "piedra": ("piedra", "Sustantivo", "stone", "taş"),
    "piedras": ("piedra", "Sustantivo (Plural)", "stones", "taşlar"),
    "cueva": ("cueva", "Sustantivo", "cave", "mağara"),
    "cuevas": ("cueva", "Sustantivo (Plural)", "caves", "mağaralar"),
    "abeja": ("abeja", "Sustantivo", "bee", "arı"),
    "abejas": ("abeja", "Sustantivo (Plural)", "bees", "arılar"),
    "miel": ("miel", "Sustantivo", "honey", "bal"),
    "olivo": ("olivo", "Sustantivo", "olive tree", "zeytin ağacı"),
    "aceite": ("aceite", "Sustantivo", "oil", "yağ"),
    "aceituna": ("aceituna", "Sustantivo", "olive", "zeytin"),
    "oro": ("oro", "Sustantivo", "gold", "altın"),
    "suéter": ("suéter", "Sustantivo", "sweater", "kazak"),
    "decisión": ("decisión", "Sustantivo", "decision", "karar"),
    "decisiones": ("decisión", "Sustantivo (Plural)", "decisions", "kararlar"),
    "elección": ("elección", "Sustantivo", "choice / election", "seçim"),
    "elecciones": ("elección", "Sustantivo (Plural)", "choices", "seçimler"),
    "fatiga": ("fatiga", "Sustantivo", "fatigue", "yorgunluk"),
    "templo": ("templo", "Sustantivo", "temple", "tapınak / mabet"),
    "monumento": ("monumento", "Sustantivo", "monument", "anıt"),
    "monolito": ("monolito", "Sustantivo", "monolith", "dikilitaş / monolit"),
    "monolitos": ("monolito", "Sustantivo (Plural)", "monoliths", "monolitler"),
    "columna": ("columna", "Sustantivo", "column / pillar", "sütun"),
    "columnas": ("columna", "Sustantivo (Plural)", "columns", "sütunlar"),
    "cazador": ("cazador", "Sustantivo", "hunter", "avcı"),
    "cazadores": ("cazador", "Sustantivo (Plural)", "hunters", "avcılar"),
    "gente": ("gente", "Sustantivo", "people", "insanlar / halk"),
    "persona": ("persona", "Sustantivo", "person", "kişi / insan"),
    "personas": ("persona", "Sustantivo (Plural)", "people / persons", "insanlar / kişiler"),
    "vida": ("vida", "Sustantivo", "life", "hayat / yaşam"),
    "vidas": ("vida", "Sustantivo (Plural)", "lives", "hayatlar"),
    "tiempo": ("tiempo", "Sustantivo", "time / weather", "zaman / hava"),
    "mundo": ("mundo", "Sustantivo", "world", "dünya"),
    "siglo": ("siglo", "Sustantivo", "century", "yüzyıl"),
    "siglos": ("siglo", "Sustantivo (Plural)", "centuries", "yüzyıllar"),
    "año": ("año", "Sustantivo", "year", "yıl / sene"),
    "años": ("año", "Sustantivo (Plural)", "years", "yıllar"),
    "día": ("día", "Sustantivo", "day", "gün"),
    "días": ("día", "Sustantivo (Plural)", "days", "günler"),
    "noche": ("noche", "Sustantivo", "night", "gece"),
    "lugar": ("lugar", "Sustantivo", "place / spot", "yer / mekan"),
    "lugares": ("lugar", "Sustantivo (Plural)", "places", "yerler"),
    "proceso": ("proceso", "Sustantivo", "process", "süreç"),
    "método": ("método", "Sustantivo", "method", "yöntem"),
    "métodos": ("método", "Sustantivo (Plural)", "methods", "yöntemler"),
}


def remove_accents(text):
    for acc, plain in ACCENT_STRIP_MAP.items():
        text = text.replace(acc, plain)
    return text


def analyze_spanish_token(token, sentence_es="", sentence_tr="", curated_vocab=None):
    clean = token.strip("'-_\"«»“”‘’¿?¡!.,;:()")
    clean = re.sub(r"[^\w'-]", "", clean, flags=re.UNICODE).strip("'-_\"«»“”‘’¿?¡!.,;:()")
    if not clean:
        return None

    raw_lower = clean.lower()

    # 0. Check Master Curated Spanish Lexicon (exact verified translations)
    if raw_lower in ES_CURATED_MAP:
        lemma, pos, en_m, tr_m, note = ES_CURATED_MAP[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m},
            "note": note
        }

    # 1. Curated Vocabulary Match from current level / database
    if curated_vocab and raw_lower in curated_vocab:
        v = curated_vocab[raw_lower]
        tr_trans = v.get("translations", {}).get("tr") or clean
        return {
            "token": clean,
            "lemma": v.get("target") or clean,
            "pos": "Palabra Clave (Vocabulario de la Lección)",
            "gloss": {"tr": tr_trans, "en": v.get("translations", {}).get("en") or clean},
            "note": f"\"{clean}\" — {tr_trans}"
        }

    # 2. Check Spanish Contractions (al, del)
    if raw_lower in SPANISH_CONTRACTIONS:
        exp, pos, en_meaning, tr_meaning = SPANISH_CONTRACTIONS[raw_lower]
        return {
            "token": clean,
            "lemma": exp,
            "pos": pos,
            "gloss": {"tr": tr_meaning, "en": en_meaning},
            "note": f"{clean} = {exp} (contracción gramatical)"
        }

    # 3. Check Clitic Pronouns attached to Infinitives or Gerunds
    # Examples:
    # convirtiéndolo -> convertir + lo ("onu dönüştürerek")
    # respirarla -> respirar + la ("onu solumak")
    # alejarse -> alejar + se ("uzaklaşmak")
    # someterse -> someter + se ("boyun eğmek")
    clitic_match = re.search(r"^(.*?(?:[aá]ndo|[eé]ndo|[ií]ndo|[aei]r))(" + "|".join(CLITIC_PRONOUNS.keys()) + ")$", raw_lower)
    if clitic_match:
        verb_part = clitic_match.group(1)
        clitic_part = clitic_match.group(2)

        # De-accent verb part: e.g. convirtiéndo -> convirtiendo
        verb_plain = remove_accents(verb_part)
        clitic_meaning = CLITIC_PRONOUNS.get(clitic_part, clitic_part)

        # Determine if infinitive or gerund
        if verb_plain.endswith("ndo"):
            pos_label = f"Verbo (Gerundio con pronombre '{clitic_part}')"
            note_str = f"{clean} (gerundio + pronombre enclítico: -{clitic_part} [\"{clitic_meaning}\"])"
        elif verb_plain.endswith("se"):
            pos_label = "Verbo Pronominal / Reflexivo"
            note_str = f"{clean} (verbo pronominal con -se)"
        else:
            pos_label = f"Verbo (Infinitivo con pronombre '{clitic_part}')"
            note_str = f"{clean} (infinitivo + pronombre enclítico: -{clitic_part} [\"{clitic_meaning}\"])"

        # Infer base infinitive
        if verb_plain.endswith(("ando", "ándo")):
            base_infinitive = verb_plain[:-4] + "ar"
        elif verb_plain.endswith(("iendo", "iéndo")):
            base_infinitive = verb_plain[:-5] + "ir"
            if base_infinitive == "convirtir":
                base_infinitive = "convertir"
            elif base_infinitive == "sintir":
                base_infinitive = "sentir"
            elif base_infinitive == "durmir":
                base_infinitive = "dormir"
        else:
            base_infinitive = verb_plain

        return {
            "token": clean,
            "lemma": base_infinitive,
            "pos": pos_label,
            "gloss": {"tr": f"{base_infinitive} + {clitic_part}", "en": f"{base_infinitive} ({clitic_meaning})"},
            "note": note_str
        }

    # 4. Check Spanish Function Words
    if raw_lower in ES_FUNCTION_WORDS:
        lemma, pos, en_m, tr_m = ES_FUNCTION_WORDS[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

    # 5. Check Content Lexicon
    if raw_lower in ES_CONTENT_LEXICON:
        lemma, pos, en_m, tr_m = ES_CONTENT_LEXICON[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m}
        }

    # 6. Check Regular Verb Endings with intelligent infinitive resolution
    cand_inf = None
    verb_pos = "Verbo"
    verb_suffix_tr = ""
    verb_suffix_en = ""

    if raw_lower.endswith("ó") and len(raw_lower) > 3:
        cand_inf = raw_lower[:-1] + "ar"
        verb_pos = "Verbo (Pretérito Indefinido)"
        verb_suffix_tr = "dı / di"
        verb_suffix_en = "ed"
    elif raw_lower.endswith("aron") and len(raw_lower) > 5:
        cand_inf = raw_lower[:-4] + "ar"
        verb_pos = "Verbo (Pretérito Indefinido)"
        verb_suffix_tr = "dılar / diler"
        verb_suffix_en = "ed"
    elif raw_lower.endswith("ió") and len(raw_lower) > 4:
        cand_inf = raw_lower[:-2] + "er"
        if cand_inf not in ES_CONTENT_LEXICON and cand_inf not in ES_CURATED_MAP:
            cand_inf = raw_lower[:-2] + "ir"
        verb_pos = "Verbo (Pretérito Indefinido)"
        verb_suffix_tr = "dı / di"
        verb_suffix_en = "ed"
    elif raw_lower.endswith("ieron") and len(raw_lower) > 6:
        cand_inf = raw_lower[:-5] + "er"
        if cand_inf not in ES_CONTENT_LEXICON and cand_inf not in ES_CURATED_MAP:
            cand_inf = raw_lower[:-5] + "ir"
        verb_pos = "Verbo (Pretérito Indefinido)"
        verb_suffix_tr = "dılar / diler"
        verb_suffix_en = "ed"
    elif raw_lower.endswith("aba") and len(raw_lower) > 4:
        cand_inf = raw_lower[:-3] + "ar"
        verb_pos = "Verbo (Pretérito Imperfecto)"
        verb_suffix_tr = "ıyordu / ardı"
        verb_suffix_en = "was -ing"
    elif raw_lower.endswith("aban") and len(raw_lower) > 5:
        cand_inf = raw_lower[:-4] + "ar"
        verb_pos = "Verbo (Pretérito Imperfecto)"
        verb_suffix_tr = "ıyorlardı / arlardı"
        verb_suffix_en = "were -ing"

    if cand_inf and (cand_inf in ES_CONTENT_LEXICON or cand_inf in ES_CURATED_MAP):
        source = ES_CONTENT_LEXICON.get(cand_inf) or ES_CURATED_MAP.get(cand_inf)
        lemma = source[0]
        en_m = source[2]
        tr_m = source[3]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": verb_pos,
            "gloss": {"tr": tr_m, "en": en_m},
            "note": f"{clean} (kök: {lemma})"
        }

    # 7. Check Regular Plural (-s / -es)
    if raw_lower.endswith("es") and len(raw_lower) > 4:
        cand = raw_lower[:-2]
        if cand in ES_CONTENT_LEXICON:
            lemma, pos, en_m, tr_m = ES_CONTENT_LEXICON[cand]
            en_plural = en_m if en_m.endswith("s") else f"{en_m}s"
            return {
                "token": clean,
                "lemma": lemma,
                "pos": f"{pos} (Plural)",
                "gloss": {"tr": make_turkish_plural(tr_m), "en": en_plural}
            }
    if raw_lower.endswith("s") and len(raw_lower) > 3:
        cand = raw_lower[:-1]
        if cand in ES_CONTENT_LEXICON:
            lemma, pos, en_m, tr_m = ES_CONTENT_LEXICON[cand]
            en_plural = en_m if en_m.endswith("s") else f"{en_m}s"
            return {
                "token": clean,
                "lemma": lemma,
                "pos": f"{pos} (Plural)",
                "gloss": {"tr": make_turkish_plural(tr_m), "en": en_plural}
            }

    # 7b. Check Verified Fallthrough & Additional Lexicon
    if raw_lower in ES_ADDITIONAL_FALLTHROUGH_MAP:
        lemma, pos, tr_m, en_m, note = ES_ADDITIONAL_FALLTHROUGH_MAP[raw_lower]
        return {
            "token": clean,
            "lemma": lemma,
            "pos": pos,
            "gloss": {"tr": tr_m, "en": en_m},
            "note": note
        }

    # 8. Proper Noun Heuristic
    is_cap = clean[0].isupper() and clean[0] != clean[0].lower()
    return {
        "token": clean,
        "lemma": clean.lower(),
        "pos": "Nombre Propio" if is_cap else "Palabra",
        "gloss": {"tr": clean, "en": clean}
    }


def tokenize_target(target):
    raw_tokens = re.split(r"(\s+|[.,!?:;«»\"“”()]+)", target)
    clean_words = []
    for tok in raw_tokens:
        if re.match(r"^\s+$", tok) or re.match(r"^[.,!?:;«»\"“”()]+$", tok):
            continue
        c = tok.strip("'-_\"«»“”‘’¿?¡!.,;:()")
        c = re.sub(r"[^\w'-]", "", c, flags=re.UNICODE).strip("'-_\"«»“”‘’¿?¡!.,;:()")
        if c:
            clean_words.append((tok, c))
    return clean_words


def process_spanish_articles(articles_path="articles.json"):
    print(f"Reading {articles_path} for Spanish token-gloss generation...")
    with open(articles_path, "r", encoding="utf-8") as f:
        articles = json.load(f)

    global_vocab = {}
    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("es", {}).items():
            for v in lvl_data.get("vocab", []):
                tgt = v.get("target", "").strip().lower()
                if tgt:
                    global_vocab[tgt] = v

    print(f"Loaded {len(global_vocab)} Spanish curated vocab items.")

    total_sents = 0
    total_tokens_generated = 0

    for art_idx, art in enumerate(articles):
        art_id = art["id"]
        es_data = art.get("languages", {}).get("es", {})

        for lvl in ["A1", "A2", "B1", "B2", "C1"]:
            lvl_data = es_data.get(lvl, {})
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
                        gloss_obj = analyze_spanish_token(
                            clean_tok,
                            sentence_es=target_sent,
                            sentence_tr=tr_trans,
                            curated_vocab=art_vocab
                        )
                        if gloss_obj:
                            tokens_list.append(gloss_obj)

                    s["tokens"] = tokens_list
                    total_tokens_generated += len(tokens_list)

    print(f"\nCompleted Spanish Generation!")
    print(f"Total Spanish Sentences Processed: {total_sents}")
    print(f"Total Spanish Tokens with Contextual Gloss: {total_tokens_generated}")

    print(f"\nWriting back to {articles_path}...")
    with open(articles_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ Successfully updated articles.json with Spanish token-gloss data.")


if __name__ == "__main__":
    process_spanish_articles()
