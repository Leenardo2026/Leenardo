#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Patch Script for Turkish Fallthrough Verb & Predicate Tokens.
Patches tokens in articles.json that fell through to generic 'Kelime' / 'Özel İsim'
with identical echo translations (gloss.en == token).
Does NOT touch tokens that already have high-confidence rule-based matches.
"""

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_JSON = BASE_DIR / "articles.json"

try:
    from scripts.turkish_fallthrough_dict import TR_ADDITIONAL_FALLTHROUGH_MAP
except ImportError:
    try:
        from turkish_fallthrough_dict import TR_ADDITIONAL_FALLTHROUGH_MAP
    except ImportError:
        TR_ADDITIONAL_FALLTHROUGH_MAP = {}

# Comprehensive Turkish Verb Stems Database
# Maps stem -> (infinitive, base_meaning, 3sg_pres, past, pres_part)
VERB_STEMS = {
    'aç': ('açmak', 'open / set sail', 'opens', 'opened', 'opening'),
    'açıl': ('açılmak', 'open up / set sail', 'sets sail / opens up', 'set sail / opened up', 'setting sail'),
    'adlandır': ('adlandırmak', 'name / designate', 'names', 'named', 'naming'),
    'adlandırıl': ('adlandırılmak', 'be named / designated', 'is named', 'was named', 'being named'),
    'ak': ('akmak', 'flow', 'flows', 'flowed', 'flowing'),
    'aktar': ('aktarmak', 'transfer / convey', 'transfers / conveys', 'transferred / conveyed', 'transferring'),
    'aktarıl': ('aktarılmak', 'be transferred / conveyed', 'is transferred', 'was transferred', 'being transferred'),
    'al': ('almak', 'take / receive / get', 'takes / receives', 'took / received', 'taking'),
    'alın': ('alınmak', 'be taken / received', 'is taken', 'was taken', 'being taken'),
    'alış': ('alışmak', 'get used to', 'gets used to', 'got used to', 'getting used to'),
    'anla': ('anlamak', 'understand', 'understands', 'understood', 'understanding'),
    'anlat': ('anlatmak', 'tell / narrate / explain', 'tells / narrates', 'told / narrated', 'telling'),
    'anlatıl': ('anlatılmak', 'be told / narrated', 'is told / narrated', 'was told / narrated', 'being told'),
    'anlaş': ('anlaşmak', 'agree / be understood', 'agrees / is understood', 'agreed / was understood', 'agreeing'),
    'anlaşıl': ('anlaşılmak', 'be understood', 'is understood', 'was understood', 'being understood'),
    'an': ('anmak', 'commemorate / mention', 'commemorates', 'commemorated', 'commemorating'),
    'anıl': ('anılmak', 'be commemorated / remembered', 'is remembered', 'was remembered', 'being remembered'),
    'ara': ('aramak', 'search / seek', 'searches', 'searched', 'searching'),
    'art': ('artmak', 'increase', 'increases', 'increased', 'increasing'),
    'artır': ('artırmak', 'increase / boost', 'increases / boosts', 'increased / boosted', 'increasing'),
    'as': ('asmak', 'hang', 'hangs', 'hung', 'hanging'),
    'asıl': ('asılmak', 'be hung', 'is hung', 'was hung', 'being hung'),
    'at': ('atmak', 'throw / cast', 'throws / casts', 'threw / cast', 'throwing'),
    'ayır': ('ayırmak', 'separate / allocate', 'separates / allocates', 'separated / allocated', 'separating'),
    'ayrıl': ('ayrılmak', 'depart / separate', 'departs / separates', 'departed / separated', 'departing'),
    'bağla': ('bağlamak', 'connect / bind', 'connects / binds', 'connected / bound', 'connecting'),
    'bağlan': ('bağlanmak', 'be connected / linked', 'is connected', 'was connected', 'being connected'),
    'bak': ('bakmak', 'look / gaze', 'looks / gazes', 'looked / gazed', 'looking'),
    'barın': ('barınmak', 'shelter / dwell', 'shelters / dwells', 'sheltered / dwelled', 'sheltering'),
    'barındır': ('barındırmak', 'house / host / harbor', 'houses / harbors', 'housed / harbored', 'housing'),
    'bas': ('basmak', 'press / step / print', 'presses / prints', 'pressed / printed', 'pressing'),
    'başla': ('başlamak', 'begin / start', 'begins / starts', 'began / started', 'beginning'),
    'başlat': ('başlatmak', 'initiate / trigger', 'initiates / triggers', 'initiated / triggered', 'initiating'),
    'bat': ('batmak', 'sink / set', 'sinks / sets', 'sank / set', 'sinking'),
    'batır': ('batırmak', 'dip / immerse', 'dips / immerses', 'dipped / immersed', 'dipping'),
    'bekle': ('beklemek', 'wait / expect', 'waits / expects', 'waited / expected', 'waiting'),
    'belir': ('belirmek', 'appear / emerge', 'appears / emerges', 'appeared / emerged', 'appearing'),
    'belirle': ('belirlemek', 'determine / define', 'determines / defines', 'determined / defined', 'determining'),
    'belirt': ('belirtmek', 'indicate / state', 'indicates / states', 'indicated / stated', 'indicating'),
    'benze': ('benzemek', 'resemble / look like', 'resembles', 'resembled', 'resembling'),
    'benzet': ('benzetmek', 'liken / compare', 'likens / compares', 'likened / compared', 'likening'),
    'besle': ('beslemek', 'feed / nourish', 'feeds / nourishes', 'fed / nourished', 'feeding'),
    'beslen': ('beslenmek', 'feed on / be nourished', 'feeds on', 'fed on', 'feeding on'),
    'bırak': ('bırakmak', 'leave / let go', 'leaves / lets go', 'left', 'leaving'),
    'bil': ('bilmek', 'know', 'knows', 'knew', 'knowing'),
    'bilin': ('bilinmek', 'be known', 'is known', 'was known', 'being known'),
    'bin': ('binmek', 'ride / board', 'rides / boards', 'rode / boarded', 'riding'),
    'bindir': ('bindirmek', 'load / impose', 'imposes / loads', 'imposed / loaded', 'imposing'),
    'birik': ('birikmek', 'accumulate', 'accumulates', 'accumulated', 'accumulating'),
    'birleş': ('birleşmek', 'unite / merge', 'unites / merges', 'united / merged', 'uniting'),
    'bit': ('bitmek', 'end / finish', 'ends / finishes', 'ended / finished', 'ending'),
    'bitir': ('bitirmek', 'finish / complete', 'finishes / completes', 'finished / completed', 'finishing'),
    'boğ': ('boğmak', 'choke / drown', 'chokes / drowns', 'choked / drowned', 'choking'),
    'boya': ('boyamak', 'paint / dye', 'paints / dyes', 'painted / dyed', 'painting'),
    'boz': ('bozmak', 'spoil / break', 'spoils / breaks', 'spoiled / broke', 'spoiling'),
    'bozul': ('bozulmak', 'spoil / deteriorate', 'spoils / deteriorates', 'spoiled / deteriorated', 'spoiling'),
    'böl': ('bölmek', 'divide / split', 'divides', 'divided', 'dividing'),
    'bul': ('bulmak', 'find / discover', 'finds / discovers', 'found / discovered', 'finding'),
    'bulun': ('bulunmak', 'be found / be located', 'is located / found', 'was located / found', 'being located'),
    'büyü': ('büyümek', 'grow', 'grows', 'grew', 'growing'),
    'büyüt': ('büyütmek', 'enlarge / raise', 'enlarges / raises', 'enlarged / raised', 'enlarging'),
    'canlan': ('canlanmak', 'come alive / revive', 'comes alive', 'came alive', 'coming alive'),
    'canlandır': ('canlandırmak', 'revive / depict', 'revives / depicts', 'revived / depicted', 'reviving'),
    'çalış': ('çalışmak', 'work / strive', 'works / strives', 'worked / strove', 'working'),
    'çek': ('çekmek', 'pull / draw / shoot', 'pulls / draws', 'pulled / drew', 'pulling'),
    'çekil': ('çekilmek', 'withdraw / retreat', 'withdraws / retreats', 'withdrew / retreated', 'withdrawing'),
    'çevir': ('çevirmek', 'turn / translate', 'turns / translates', 'turned / translated', 'turning'),
    'çık': ('çıkmak', 'emerge / go out', 'emerges / goes out', 'emerged / went out', 'emerging'),
    'çıkar': ('çıkarmak', 'extract / remove / produce', 'extracts / produces', 'extracted / produced', 'extracting'),
    'çiz': ('çizmek', 'draw / sketch', 'draws / sketches', 'drew / sketched', 'drawing'),
    'çök': ('çökmek', 'collapse', 'collapses', 'collapsed', 'collapsing'),
    'çöz': ('çözmek', 'solve / untie', 'solves', 'solved', 'solving'),
    'çözül': ('çözülmek', 'dissolve / be solved', 'dissolves', 'dissolved', 'dissolving'),
    'dağıl': ('dağılmak', 'disperse / scatter', 'disperses', 'dispersed', 'dispersing'),
    'dağıt': ('dağıtmak', 'distribute / scatter', 'distributes', 'distributed', 'distributing'),
    'dayan': ('dayanmak', 'date back / endure / rely on', 'dates back to / endures', 'dated back to / endured', 'dating back to'),
    'de': ('demek', 'say / mean', 'says', 'said', 'saying'),
    'değiş': ('değişmek', 'change', 'changes', 'changed', 'changing'),
    'değiştir': ('değiştirmek', 'alter / change', 'alters / changes', 'altered / changed', 'altering'),
    'den': ('denmek', 'be called / said', 'is called / said', 'was called / said', 'being called'),
    'dene': ('denemek', 'try / test', 'tries / tests', 'tried / tested', 'trying'),
    'destekle': ('desteklemek', 'support', 'supports', 'supported', 'supporting'),
    'dik': ('dikmek', 'erect / plant', 'erects / plants', 'erected / planted', 'erecting'),
    'dikil': ('dikilmek', 'be erected / stand', 'is erected / stands', 'was erected / stood', 'standing'),
    'dinle': ('dinlemek', 'listen', 'listens', 'listened', 'listening'),
    'dinlen': ('dinlenmek', 'rest', 'rests', 'rested', 'resting'),
    'diren': ('direnmek', 'resist', 'resists', 'resisted', 'resisting'),
    'doğ': ('doğmak', 'be born / rise', 'is born / rises', 'was born / rose', 'rising'),
    'doku': ('dokumak', 'weave', 'weaves', 'wove', 'weaving'),
    'dokun': ('dokunmak', 'touch', 'touches', 'touched', 'touching'),
    'dolaş': ('dolaşmak', 'wander / circulate', 'wanders / circulates', 'wandered / circulated', 'wandering'),
    'doldur': ('doldurmak', 'fill', 'fills', 'filled', 'filling'),
    'dol': ('dolmak', 'fill up', 'fills up', 'filled up', 'filling up'),
    'dön': ('dönmek', 'return / turn', 'returns / turns', 'returned / turned', 'returning'),
    'dönüş': ('dönüşmek', 'turn into / transform', 'turns into / transforms', 'turned into / transformed', 'transforming'),
    'dönüştür': ('dönüştürmek', 'transform / convert', 'transforms / converts', 'transformed / converted', 'transforming'),
    'dök': ('dökmek', 'pour / shed', 'pours / sheds', 'poured / shed', 'pouring'),
    'dökül': ('dökülmek', 'spill / be poured out', 'spills / pours out', 'spilled / poured out', 'spilling'),
    'dur': ('durmak', 'stand / remain / stop', 'stands / remains', 'stood / remained', 'standing'),
    'durdur': ('durdurmak', 'stop / halt', 'stops / halts', 'stopped / halted', 'stopping'),
    'duy': ('duymak', 'hear / feel', 'hears / feels', 'heard / felt', 'hearing'),
    'duyul': ('duyulmak', 'be heard', 'is heard', 'was heard', 'being heard'),
    'düzenle': ('düzenlemek', 'organize / arrange', 'organizes / arranges', 'organized / arranged', 'organizing'),
    'düş': ('düşmek', 'fall', 'falls', 'fell', 'falling'),
    'düşün': ('düşünmek', 'think / reflect', 'thinks / reflects', 'thought / reflected', 'thinking'),
    'et': ('etmek', 'do / make', 'does / makes', 'did / made', 'doing'),
    'etkile': ('etkilemek', 'influence / affect', 'influences / affects', 'influenced / affected', 'influencing'),
    'etkilen': ('etkilenmek', 'be influenced / affected', 'is influenced', 'was influenced', 'being influenced'),
    'evril': ('evrilmek', 'evolve', 'evolves', 'evolved', 'evolving'),
    'fark et': ('fark etmek', 'notice / realize', 'notices / realizes', 'noticed / realized', 'noticing'),
    'geç': ('geçmek', 'pass / cross', 'passes / crosses', 'passed / crossed', 'passing'),
    'geçir': ('geçirmek', 'pass / spend (time)', 'spends / passes', 'spent / passed', 'spending'),
    'gel': ('gelmek', 'come / arrive', 'comes / arrives', 'came / arrived', 'coming'),
    'geliş': ('gelişmek', 'develop / evolve', 'develops / evolves', 'developed / evolved', 'developing'),
    'geliştir': ('geliştirmek', 'develop / improve', 'develops / improves', 'developed / improved', 'developing'),
    'gerek': ('gerekmek', 'be required / necessary', 'is required / necessary', 'was required', 'requiring'),
    'getir': ('getirmek', 'bring', 'brings', 'brought', 'bringing'),
    'gez': ('gezmek', 'tour / travel / visit', 'tours / visits', 'toured / visited', 'touring'),
    'gir': ('girmek', 'enter', 'enters', 'entered', 'entering'),
    'git': ('gitmek', 'go', 'goes', 'went', 'going'),
    'giy': ('giymek', 'wear', 'wears', 'wore', 'wearing'),
    'göç': ('göçmek', 'migrate', 'migrates', 'migrated', 'migrating'),
    'göm': ('gömmek', 'bury', 'buries', 'buried', 'burying'),
    'gömül': ('gömülmek', 'be buried', 'is buried', 'was buried', 'being buried'),
    'gör': ('görmek', 'see', 'sees', 'saw', 'seeing'),
    'görün': ('görünmek', 'appear / seem', 'appears / seems', 'appeared / seemed', 'appearing'),
    'göster': ('göstermek', 'show / demonstrate', 'shows / demonstrates', 'showed / demonstrated', 'showing'),
    'gözlemle': ('gözlemlemek', 'observe', 'observes', 'observed', 'observing'),
    'güçlendir': ('güçlendirmek', 'strengthen / reinforce', 'strengthens / reinforces', 'strengthened / reinforced', 'strengthening'),
    'hatırla': ('hatırlamak', 'remember', 'remembers', 'remembered', 'remembering'),
    'hatırlat': ('hatırlatmak', 'remind', 'reminds', 'reminded', 'reminding'),
    'hazırla': ('hazırlamak', 'prepare', 'prepares', 'prepared', 'preparing'),
    'hisset': ('hissetmek', 'feel', 'feels', 'felt', 'feeling'),
    'inan': ('inanmak', 'believe', 'believes', 'believed', 'believing'),
    'inanıl': ('inanılmak', 'be believed', 'is believed', 'was believed', 'being believed'),
    'incele': ('incelemek', 'examine / study', 'examines / studies', 'examined / studied', 'examining'),
    'inşa et': ('inşa etmek', 'build / construct', 'builds / constructs', 'built / constructed', 'building'),
    'iste': ('istemek', 'want / desire', 'wants / desires', 'wanted / desired', 'wanting'),
    'işle': ('işlemek', 'carve / craft / process', 'carves / crafts', 'carved / crafted', 'carving'),
    'işlen': ('işlenmek', 'be carved / crafted', 'is carved / crafted', 'was carved / crafted', 'being carved'),
    'kaç': ('kaçmak', 'escape / flee', 'escapes / flees', 'escaped / fled', 'escaping'),
    'kal': ('kalmak', 'stay / remain', 'stays / remains', 'stayed / remained', 'staying'),
    'kalk': ('kalkmak', 'rise / depart', 'rises / departs', 'rose / departed', 'rising'),
    'kanıtla': ('kanıtlamak', 'prove / demonstrate', 'proves / demonstrates', 'proved / demonstrated', 'proving'),
    'kapan': ('kapanmak', 'close / shut', 'closes / shuts', 'closed / shut', 'closing'),
    'karar ver': ('karar vermek', 'decide', 'decides', 'decided', 'deciding'),
    'karış': ('karışmak', 'blend / mingle', 'blends / mingles', 'blended / mingled', 'blending'),
    'karşıla': ('karşılamak', 'meet / welcome', 'meets / welcomes', 'met / welcomed', 'meeting'),
    'kat': ('katmak', 'add / include', 'adds / includes', 'added / included', 'adding'),
    'katıl': ('katılmak', 'join / participate', 'joins / participates', 'joined / participated', 'joining'),
    'kaybet': ('kaybetmek', 'lose', 'loses', 'lost', 'losing'),
    'kaybol': ('kaybolmak', 'disappear / vanish', 'disappears / vanishes', 'disappeared / vanished', 'disappearing'),
    'kazan': ('kazanmak', 'gain / acquire / win', 'gains / acquires', 'gained / acquired', 'gaining'),
    'kazandır': ('kazandırmak', 'endow / bring / impart', 'endows / imparts', 'endowed / imparted', 'endowing'),
    'kes': ('kesmek', 'cut / stop', 'cuts', 'cut', 'cutting'),
    'keşfet': ('keşfetmek', 'discover / explore', 'discovers / explores', 'discovered / explored', 'discovering'),
    'kıl': ('kılmak', 'make / render', 'makes / renders', 'made / rendered', 'making'),
    'kır': ('kırmak', 'break', 'breaks', 'broke', 'breaking'),
    'kırıl': ('kırılmak', 'be broken', 'is broken', 'was broken', 'breaking'),
    'koku': ('kokmak', 'smell', 'smells', 'smelled', 'smelling'),
    'kon': ('konmak', 'perch / settle', 'perches / settles', 'perched / settled', 'perching'),
    'konuş': ('konuşmak', 'speak / talk', 'speaks / talks', 'spoke / talked', 'speaking'),
    'kork': ('korkmak', 'fear / be afraid', 'fears', 'feared', 'fearing'),
    'koru': ('korumak', 'protect / preserve', 'protects / preserves', 'protected / preserved', 'protecting'),
    'korun': ('korunmak', 'be protected / preserved', 'is protected / preserved', 'was protected / preserved', 'being preserved'),
    'koş': ('koşmak', 'run', 'runs', 'ran', 'running'),
    'koy': ('koymak', 'put / place', 'puts / places', 'put / placed', 'putting'),
    'kur': ('kurmak', 'establish / set up', 'establishes / sets up', 'established / set up', 'establishing'),
    'kurul': ('kurulmak', 'be established / founded', 'is established / founded', 'was established / founded', 'being founded'),
    'kurtar': ('kurtarmak', 'rescue / save', 'rescues / saves', 'rescued / saved', 'rescuing'),
    'kurtul': ('kurtulmak', 'escape / break free', 'escapes / breaks free', 'escaped / broke free', 'escaping'),
    'kullan': ('kullanmak', 'use / employ', 'uses / employs', 'used / employed', 'using'),
    'kullanıl': ('kullanılmak', 'be used / employed', 'is used / employed', 'was used / employed', 'being used'),
    'küçül': ('küçülmek', 'shrink / diminish', 'shrinks / diminishes', 'shrank / diminished', 'shrinking'),
    'meydana gel': ('meydana gelmek', 'occur / take place', 'occurs / takes place', 'occurred / took place', 'occurring'),
    'oluş': ('oluşmak', 'form / emerge', 'forms / emerges', 'formed / emerged', 'forming'),
    'oluştur': ('oluşturmak', 'create / form', 'creates / forms', 'created / formed', 'creating'),
    'onar': ('onarmak', 'repair / restore', 'repairs / restores', 'repaired / restored', 'repairing'),
    'onarıl': ('onarılmak', 'be repaired / restored', 'is repaired / restored', 'was repaired / restored', 'being repaired'),
    'otur': ('oturmak', 'reside / sit', 'resides / sits', 'resided / sat', 'residing'),
    'oyna': ('oynamak', 'play / perform', 'plays / performs', 'played / performed', 'playing'),
    'öğren': ('öğrenmek', 'learn', 'learns', 'learned', 'learning'),
    'öğret': ('öğretmek', 'teach', 'teaches', 'taught', 'teaching'),
    'öl': ('ölmek', 'die', 'dies', 'died', 'dying'),
    'ölç': ('ölçmek', 'measure', 'measures', 'measured', 'measuring'),
    'ölçül': ('ölçülmek', 'be measured', 'is measured', 'was measured', 'being measured'),
    'öne çık': ('öne çıkmak', 'stand out / come forward', 'stands out', 'stood out', 'standing out'),
    'önle': ('önlemek', 'prevent', 'prevents', 'prevented', 'preventing'),
    'ör': ('örmek', 'knit / weave', 'knits / weaves', 'knitted / wove', 'weaving'),
    'ört': ('örtmek', 'cover', 'covers', 'covered', 'covering'),
    'örtül': ('örtülmek', 'be covered', 'is covered', 'was covered', 'being covered'),
    'özdeşleş': ('özdeşleşmek', 'become identified with', 'becomes identified with', 'became identified with', 'becoming identified with'),
    'özetle': ('özetlemek', 'summarize', 'summarizes', 'summarized', 'summarizing'),
    'paylaş': ('paylaşmak', 'share', 'shares', 'shared', 'sharing'),
    'piş': ('pişmek', 'cook (intransitive)', 'cooks', 'cooked', 'cooking'),
    'pişir': ('pişirmek', 'cook / brew', 'cooks / brews', 'cooked / brewed', 'cooking'),
    'sakla': ('saklamak', 'hide / store / preserve', 'hides / stores', 'hid / stored', 'hiding'),
    'saklan': ('saklanmak', 'hide / conceal oneself', 'hides', 'hid', 'hiding'),
    'sağla': ('sağlamak', 'provide / ensure', 'provides / ensures', 'provided / ensured', 'providing'),
    'sar': ('sarmak', 'wrap / encompass', 'wraps / encompasses', 'wrapped / encompassed', 'wrapping'),
    'sars': ('sarsmak', 'shake / shock', 'shakes / shocks', 'shook / shocked', 'shaking'),
    'sat': ('satmak', 'sell', 'sells', 'sold', 'selling'),
    'savun': ('savunmak', 'defend', 'defends', 'defended', 'defending'),
    'say': ('saymak', 'count / consider', 'counts / considers', 'counted / considered', 'counting'),
    'sayıl': ('sayılmak', 'be considered / regarded', 'is considered / regarded', 'was considered / regarded', 'being considered'),
    'seç': ('seçmek', 'choose / select', 'chooses / selects', 'chose / selected', 'choosing'),
    'sergile': ('sergilemek', 'exhibit / display', 'exhibits / displays', 'exhibited / displayed', 'exhibiting'),
    'sev': ('sevmek', 'love / like', 'loves / likes', 'loved / liked', 'loving'),
    'sık': ('sıkmak', 'squeeze / tighten', 'squeezes / tightens', 'squeezed / tightened', 'squeezing'),
    'sığ': ('sığmak', 'fit into', 'fits into', 'fit into', 'fitting into'),
    'sona er': ('sona ermek', 'come to an end', 'comes to an end', 'came to an end', 'ending'),
    'sor': ('sormak', 'ask', 'asks', 'asked', 'asking'),
    'söndür': ('söndürmek', 'extinguish', 'extinguishes', 'extinguished', 'extinguishing'),
    'söyle': ('söylemek', 'say / express', 'says / expresses', 'said / expressed', 'saying'),
    'söylen': ('söylenmek', 'be said / told', 'is said / told', 'was said / told', 'being said'),
    'sür': ('sürmek', 'last / continue / drive', 'lasts / continues', 'lasted / continued', 'lasting'),
    'sürdür': ('sürdürmek', 'maintain / perpetuate', 'maintains / perpetuates', 'maintained / perpetuated', 'maintaining'),
    'taşı': ('taşımak', 'carry / bear', 'carries / bears', 'carried / bore', 'carrying'),
    'taşın': ('taşınmak', 'be transported / move', 'is transported / moves', 'was transported / moved', 'being transported'),
    'tanı': ('tanımak', 'recognize / know', 'recognizes / knows', 'recognized / knew', 'recognizing'),
    'tanıt': ('tanıtmak', 'introduce / promote', 'introduces / promotes', 'introduced / promoted', 'introducing'),
    'tart': ('tartmak', 'weigh / ponder', 'weighs / ponders', 'weighed / pondered', 'weighing'),
    'temsil et': ('temsil etmek', 'represent', 'represents', 'represented', 'representing'),
    'terk et': ('terk etmek', 'abandon / leave', 'abandons / leaves', 'abandoned / left', 'abandoning'),
    'topla': ('toplamak', 'gather / collect', 'gathers / collects', 'gathered / collected', 'gathering'),
    'tut': ('tutmak', 'hold / keep', 'holds / keeps', 'held / kept', 'holding'),
    'tüket': ('tüketmek', 'consume', 'consumes', 'consumed', 'consuming'),
    'uç': ('uçmak', 'fly', 'flies', 'flew', 'flying'),
    'uğra': ('uğramak', 'undergo / visit', 'undergoes / visits', 'underwent / visited', 'undergoing'),
    'ulaş': ('ulaşmak', 'reach / attain', 'reaches / attains', 'reached / attained', 'reaching'),
    'unut': ('unutmak', 'forget', 'forgets', 'forgot', 'forgetting'),
    'unutul': ('unutulmak', 'be forgotten', 'is forgotten', 'was forgotten', 'being forgotten'),
    'uygula': ('uygulamak', 'apply / practice', 'applies / practices', 'applied / practiced', 'applying'),
    'uyu': ('uyumak', 'sleep', 'sleeps', 'slept', 'sleeping'),
    'uzan': ('uzanmak', 'extend / lie down', 'extends / lies down', 'extended / lay down', 'extending'),
    'üret': ('üretmek', 'produce / generate', 'produces / generates', 'produced / generated', 'producing'),
    'ver': ('vermek', 'give / grant', 'gives / grants', 'gave / granted', 'giving'),
    'veril': ('verilmek', 'be given / granted', 'is given / granted', 'was given / granted', 'being given'),
    'vur': ('vurmak', 'strike / hit', 'strikes / hits', 'struck / hit', 'striking'),
    'yak': ('yakmak', 'burn / ignite', 'burns / ignites', 'burned / ignited', 'burning'),
    'yaklaş': ('yaklaşmak', 'approach', 'approaches', 'approached', 'approaching'),
    'yansıt': ('yansıtmak', 'reflect / mirror', 'reflects / mirrors', 'reflected / mirrored', 'reflecting'),
    'yap': ('yapmak', 'make / do', 'makes / does', 'made / did', 'making'),
    'yapıl': ('yapılmak', 'be made / done', 'is made / done', 'was made / done', 'being made'),
    'yarat': ('yaratmak', 'create', 'creates', 'created', 'creating'),
    'yaşa': ('yaşamak', 'live / experience', 'lives / experiences', 'lived / experienced', 'living'),
    'yaşat': ('yaşatmak', 'keep alive / sustain', 'keeps alive / sustains', 'kept alive / sustained', 'keeping alive'),
    'yat': ('yatmak', 'lie down', 'lies down', 'lay down', 'lying down'),
    'yatır': ('yatırmak', 'deposit / invest / lay down', 'deposits / invests', 'deposited / invested', 'depositing'),
    'yaz': ('yazmak', 'write', 'writes', 'wrote', 'writing'),
    'yazıl': ('yazılmak', 'be written', 'is written', 'was written', 'being written'),
    'ye': ('yemek', 'eat', 'eats', 'ate', 'eating'),
    'yet': ('yetmek', 'suffice', 'suffices', 'sufficed', 'sufficing'),
    'yık': ('yıkmak', 'tear down / demolish', 'tears down / demolishes', 'tore down / demolished', 'tearing down'),
    'yıkıl': ('yıkılmak', 'collapse / be destroyed', 'collapses / is destroyed', 'collapsed / was destroyed', 'collapsing'),
    'yıprat': ('yıpratmak', 'wear out / exhaust', 'wears out / exhausts', 'wore out / exhausted', 'wearing out'),
    'yitir': ('yitirmek', 'lose', 'loses', 'lost', 'losing'),
    'yok ol': ('yok olmak', 'vanish / disappear', 'vanishes / disappears', 'vanished / disappeared', 'vanishing'),
    'yol aç': ('yol açmak', 'cause / lead to', 'causes / leads to', 'caused / led to', 'causing'),
    'yönet': ('yönetmek', 'manage / direct / rule', 'rules / directs', 'ruled / directed', 'ruling'),
    'yüksel': ('yükselmek', 'rise / ascend', 'rises / ascends', 'rose / ascended', 'rising'),
    'yürüt': ('yürütmek', 'conduct / carry out', 'conducts / carries out', 'conducted / carried out', 'conducting'),
    'yüz': ('yüzmek', 'swim', 'swims', 'swam', 'swimming'),
    'yüzleş': ('yüzleşmek', 'confront / face', 'confronts / faces', 'confronted / faced', 'confronting')
}

# Contextual overrides for special words / homonyms
SPECIAL_VERB_OVERRIDES = {
    'yıkamadılar': ('yıkmak', 'Fiil (Yetersizlik Olumsuz 3. Çoğul)', 'could not tear down / destroy', '"yıkamadılar" (kök: yıkmak — could not tear down)'),
    'yıkamadı': ('yıkmak', 'Fiil (Yetersizlik Olumsuz 3. Tekil)', 'could not tear down / destroy', '"yıkamadı" (kök: yıkmak — could not tear down)'),
    'geçiremediler': ('geçirmek', 'Fiil (Yetersizlik Olumsuz 3. Çoğul)', 'could not take / pass', '"geçiremediler" (ele geçiremediler: could not capture)'),
    'geçemedi': ('geçmek', 'Fiil (Yetersizlik Olumsuz 3. Tekil)', 'could not cross / pass', '"geçemedi" (kök: geçmek — could not pass)'),
    'açılır': ('açılmak', 'Fiil (Geniş Zaman)', 'sets sail / ventures out', '"açılır" (denize açılır: sets sail)'),
    'açıldı': ('açılmak', 'Fiil (Görülen Geçmiş Zaman)', 'opened / set sail', '"açıldı" (kök: açılmak — was opened / set sail)'),
    'açıldılar': ('açılmak', 'Fiil (Görülen Geçmiş Zaman 3. Çoğul)', 'set sail / ventured out', '"açıldılar" (denize açıldılar: set sail)'),
    'denir': ('denmek', 'Fiil (Geniş Zaman)', 'is called / is said', '"denir" (kök: denmek — is called)'),
    'saklandılar': ('saklanmak', 'Fiil (Görülen Geçmiş Zaman 3. Çoğul)', 'hid / concealed themselves', '"saklandılar" (kök: saklanmak — hid)'),
    'gezdiler': ('gezmek', 'Fiil (Görülen Geçmiş Zaman 3. Çoğul)', 'toured / visited', '"gezdiler" (kök: gezmek — toured / visited)'),
    'kurulmuştur': ('kurulmak', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'was established / founded', '"kurulmuştur" (kök: kurulmak — was established)'),
    'sergilemektedir': ('sergilemek', 'Fiil (Süreklilik / Şimdiki Zaman)', 'exhibits / displays', '"sergilemektedir" (kök: sergilemek — exhibits / displays)'),
    'kazandırmıştır': ('kazandırmak', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'has endowed / imparted', '"kazandırmıştır" (kök: kazandırmak — has endowed / imparted)'),
    'özdeşleşmiştir': ('özdeşleşmek', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'has become identified with', '"özdeşleşmiştir" (kök: özdeşleşmek — has become identified with)'),
    'doğrulamaktadır': ('doğrulamak', 'Fiil (Süreklilik / Şimdiki Zaman)', 'confirms / corroborates', '"doğrulamaktadır" (kök: doğrulamak — confirms)'),
    'kanıtlamaktadır': ('kanıtlamak', 'Fiil (Süreklilik / Şimdiki Zaman)', 'proves / demonstrates', '"kanıtlamaktadır" (kök: kanıtlamak — proves)'),
    'yüzleşmektedir': ('yüzleşmek', 'Fiil (Süreklilik / Şimdiki Zaman)', 'faces / confronts', '"yüzleşmektedir" (kök: yüzleşmek — confronts)'),
    'getirmektedir': ('getirmek', 'Fiil (Süreklilik / Şimdiki Zaman)', 'brings', '"getirmektedir" (kök: getirmek — brings)'),
    'hatırlatmaktadır': ('hatırlatmak', 'Fiil (Süreklilik / Şimdiki Zaman)', 'reminds', '"hatırlatmaktadır" (kök: hatırlatmak — reminds)'),
    'dayanmaktadır': ('dayanmak', 'Fiil (Süreklilik / Şimdiki Zaman)', 'dates back to / relies on', '"dayanmaktadır" (kök: dayanmak — dates back to)'),
    'gelişmiştir': ('gelişmek', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'developed / evolved', '"gelişmiştir" (kök: gelişmek — developed)'),
    'başlamıştır': ('başlamak', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'began / started', '"başlamıştır" (kök: başlamak — began)'),
    'taşınmıştır': ('taşınmak', 'Fiil (Duyulan Geçmiş Zaman + Bildirme)', 'was transported / moved', '"taşınmıştır" (kök: taşınmak — was transported)'),
    'inanılıyordu': ('inanılmak', 'Fiil (Şimdiki Zamanın Hikayesi - Edilgen)', 'was believed', '"inanılıyordu" (kök: inanılmak — was believed)'),
    'istiyorlardı': ('istemek', 'Fiil (Şimdiki Zamanın Hikayesi 3. Çoğul)', 'were wanting / sought', '"istiyorlardı" (kök: istemek — wanted / sought)'),
    'sarstı': ('sarsmak', 'Fiil (Görülen Geçmiş Zaman)', 'shook / shattered', '"sarstı" (kök: sarsmak — shook / rattled)'),
    'yıpratır': ('yıpratmak', 'Fiil (Geniş Zaman)', 'wears out / exhausts', '"yıpratır" (kök: yıpratmak — wears out)'),
    'bindiriyor': ('bindirmek', 'Fiil (Şimdiki Zaman)', 'imposes / burdens', '"bindiriyor" (kök: bindirmek — imposes a load)'),
    'ölçülür': ('ölçülmek', 'Fiil (Geniş Zaman - Edilgen)', 'is measured', '"ölçülür" (kök: ölçülmek — is measured)'),
    'yatırılır': ('yatırılmak', 'Fiil (Geniş Zaman - Edilgen)', 'is deposited / placed', '"yatırılır" (kök: yatırılmak — is laid down / deposited)'),
    'diktiler': ('dikmek', 'Fiil (Görülen Geçmiş Zaman 3. Çoğul)', 'erected / planted', '"diktiler" (kök: dikmek — erected)'),
    'düzenledi': ('düzenlemek', 'Fiil (Görülen Geçmiş Zaman)', 'organized / arranged', '"düzenledi" (kök: düzenlemek — organized)'),
    'inceliyor': ('incelemek', 'Fiil (Şimdiki Zaman)', 'examines / investigates', '"inceliyor" (kök: incelemek — examines)'),
    'işlenmiş': ('işlenmek', 'Fiilimsi / Fiil (Duyulan Geçmiş)', 'carved / crafted / processed', '"işlenmiş" (kök: işlenmek — carved / crafted)'),
    'unutulmuş': ('unutulmak', 'Fiilimsi / Fiil (Duyulan Geçmiş)', 'forgotten', '"unutulmuş" (kök: unutulmak — forgotten)'),
    'canlanır': ('canlanmak', 'Fiil (Geniş Zaman)', 'comes to life / revives', '"canlanır" (kök: canlanmak — comes to life)'),
    'özetler': ('özetlemek', 'Fiil (Geniş Zaman)', 'summarizes', '"özetler" (kök: özetlemek — summarizes)'),
    'tartar': ('tartmak', 'Fiil (Geniş Zaman)', 'weighs / ponders', '"tartar" (kök: tartmak — weighs)'),
    'uğrar': ('uğramak', 'Fiil (Geniş Zaman)', 'undergoes / stops by', '"uğrar" (kök: uğramak — undergoes)'),
    'korunur': ('korunmak', 'Fiil (Geniş Zaman - Edilgen)', 'is protected / preserved', '"korunur" (kök: korunmak — is preserved)'),
    'batırdı': ('batırmak', 'Fiil (Görülen Geçmiş Zaman)', 'dipped / immersed', '"batırdı" (kök: batırmak — dipped)'),
    'getirdi': ('getirmek', 'Fiil (Görülen Geçmiş Zaman)', 'brought', '"getirdi" (kök: getirmek — brought)')
}

# Tense deconstruction rules
TENSE_RULES = [
    # Şimdiki zamanın hikayesi (-ıyordu, -iyordu)
    (r'^(.*?)([ıiuü]?yor)(du|dı|lar|ler|du|duk|dük)$', 'Fiil (Şimdiki Zamanın Hikayesi)', lambda info, p: f"was {info[4]}" if not p.endswith(('lar', 'ler')) else f"were {info[4]}"),
    # Süreklilik bildirme (-maktadır, -mektedir)
    (r'^(.*?)(makta|mekte)(dır|dir|lar|ler)?$', 'Fiil (Süreklilik / Şimdiki Zaman -makta)', lambda info, p: info[2] if not (p and 'lar' in p) else info[1]),
    # Duyulan geçmiş zaman bildirme (-miştir, -mıştır)
    (r'^(.*?)([m][ıiuü]ş)(tir|tür|dır|dir|ler|lar)?$', 'Fiil (Duyulan Geçmiş Zaman)', lambda info, p: info[3]),
    # Gelecek zaman (-acak, -ecek)
    (r'^(.*?)([ae]ca[kğ]|[ae]ce[kğ])(tı|ti|lar|ler)?$', 'Fiil (Gelecek Zaman)', lambda info, p: f"will {info[1]}"),
    # Geniş zaman olumsuz (-maz, -mez)
    (r'^(.*?)(m[ae]z)(di|dı|ler|lar)?$', 'Fiil (Geniş Zaman Olumsuz)', lambda info, p: f"does not {info[1]}"),
    # Yeterlik olumsuz (-amadı, -emedi, -amaz, -emez)
    (r'^(.*?)([ae]ma|[ae]me)(dı|di|z|dılar|diler)?$', 'Fiil (Yetersizlik / Olumsuz)', lambda info, p: f"could not {info[1]}"),
    # Görülen geçmiş zaman çoğul (-dılar, -tiler)
    (r'^(.*?)([dt][ıiuü])(lar|ler)$', 'Fiil (Görülen Geçmiş Zaman 3. Çoğul)', lambda info, p: info[3]),
    # Görülen geçmiş zaman tekil (-dı, -di, -du, -dü, -tı, -ti, -tu, -tü)
    (r'^(.*?)([dt][ıiuü])(k|m|n)?$', 'Fiil (Görülen Geçmiş Zaman)', lambda info, p: info[3]),
    # Şimdiki zaman (-ıyor)
    (r'^(.*?)([ıiuü]?yor)(lar|ler)?$', 'Fiil (Şimdiki Zaman)', lambda info, p: info[2] if not (p and 'lar' in p) else info[1]),
    # Geniş zaman (-ar, -er, -ır, -ir, -ur, -ür)
    (r'^(.*?)([aeıiuü]r)(ken|di|dı|ler|lar)?$', 'Fiil (Geniş Zaman)', lambda info, p: info[2] if not (p and 'lar' in p) else info[1]),
    # Zarf-fiil (-arak, -erek, -ınca, -ince)
    (r'^(.*?)(arak|erek|ınca|ince|unca|ünce|dıkça|dikçe)$', 'Fiilimsi (Zarf-fiil)', lambda info, p: f"by {info[4]}" if 'erek' in p or 'arak' in p else f"upon {info[4]}"),
    # Sıfat-fiil (-dığı, -diği)
    (r'^(.*?)([dt][ıiuü]ğ|[ae]ceğ|[ae]cağ)([ıiuü]|ım|in|imiz)?$', 'Fiilimsi (Sıfat-fiil)', lambda info, p: f"that {info[2]}"),
    (r'^(.*?)([ae]n)$', 'Fiilimsi (Sıfat-fiil)', lambda info, p: f"who / which {info[2]}")
]


def resolve_turkish_fallthrough_verb(clean_token):
    lower = clean_token.lower()

    # 1. Exact override
    if lower in SPECIAL_VERB_OVERRIDES:
        return SPECIAL_VERB_OVERRIDES[lower]

    # 2. Check verified fallthrough dictionary
    if lower in TR_ADDITIONAL_FALLTHROUGH_MAP:
        return TR_ADDITIONAL_FALLTHROUGH_MAP[lower]

    # 3. Check direct stem lookup in VERB_STEMS
    if lower in VERB_STEMS:
        info = VERB_STEMS[lower]
        return info[0], "Fiil (Geniş Zaman / Mastar)", info[1], f'"{clean_token}" (kök: {info[0]} — {info[1]})'

    # 3. Rule-based deconstruction against VERB_STEMS
    for pat, label, trans_fn in TENSE_RULES:
        m = re.match(pat, lower)
        if m:
            stem = m.group(1)
            ending = m.group(2) + (m.group(3) if len(m.groups()) >= 3 and m.group(3) else "")
            
            # Stem restorations
            # Progressive vowel contraction (ist -> iste, oyn -> oyna)
            cand_stems = [stem]
            if stem.endswith(('ist', 'söyl', 'bekl', 'özl', 'gözl', 'dinl', 'ilerl', 'temizl', 'den')):
                cand_stems.append(stem + 'e')
            elif stem.endswith(('başl', 'yaş', 'anl', 'sakl', 'kutl', 'oyn', 'topl', 'hazırl', 'kor', 'boy')):
                cand_stems.append(stem + 'a')
                if stem.endswith('kor'): cand_stems.append('koru')
                if stem.endswith('boy'): cand_stems.append('boya')

            # Consonant softening inversion (t->d, k->ğ, p->b, ç->c)
            rev_stems = []
            for cs in cand_stems:
                rev_stems.append(cs)
                if cs.endswith('d'): rev_stems.append(cs[:-1] + 't')
                elif cs.endswith('c'): rev_stems.append(cs[:-1] + 'ç')
                elif cs.endswith('b'): rev_stems.append(cs[:-1] + 'p')
                elif cs.endswith('ğ'): rev_stems.append(cs[:-1] + 'k')

            for s in rev_stems:
                if s in VERB_STEMS:
                    v_info = VERB_STEMS[s]
                    en_meaning = trans_fn(v_info, ending)
                    lemma = v_info[0]
                    note = f'"{clean_token}" (kök: {lemma} — {en_meaning})'
                    return lemma, label, en_meaning, note

    return None


def patch_articles():
    print(f"Reading {ARTICLES_JSON}...")
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    patched_count = 0
    skipped_high_conf = 0

    for art in articles:
        for lvl, lvl_data in art.get("languages", {}).get("tr", {}).items():
            for p in lvl_data.get("paragraphs", []):
                if isinstance(p, list):
                    for s in p:
                        for tok in s.get("tokens", []):
                            raw = tok.get("token", "")
                            clean = re.sub(r"[^\w]", "", raw).lower()
                            if not clean or len(clean) <= 1:
                                continue

                            pos = tok.get("pos", "")
                            g = tok.get("gloss", {})
                            en = g.get("en", "")
                            is_echo = (not en or en.lower() == raw.lower())

                            # STRICT GUARD: Only patch tokens in the generic fallthrough set
                            if pos not in ["Kelime", "Özel İsim"] and not is_echo:
                                skipped_high_conf += 1
                                continue

                            # Try resolving verb
                            res = resolve_turkish_fallthrough_verb(clean)
                            if res:
                                lemma, new_pos, en_trans, note = res
                                tok["lemma"] = lemma
                                tok["pos"] = new_pos
                                g["en"] = en_trans
                                tok["gloss"] = g
                                tok["note"] = note
                                patched_count += 1

    print(f"\n✓ Successfully patched {patched_count} Turkish fallthrough verb tokens!")
    print(f"✓ Preserved {skipped_high_conf} high-confidence rule-based matches without modification.")

    print(f"\nWriting updated database to {ARTICLES_JSON}...")
    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print("✓ articles.json successfully saved.")


if __name__ == "__main__":
    patch_articles()
