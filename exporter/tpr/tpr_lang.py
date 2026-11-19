"""Sinhala / Thai / Hindi / Myanmar versions of the TPR DPD package.

The English definitions are swapped for the AI translations made in
~/git/dictionary (translations.db: headwords.id -> definitions.key ->
definitions.si / th). Pāḷi fields are shown in Sinhala or Thai script, part of
speech, grammar and table labels in that language. dpd.db is never changed:
each headword is wrapped, not edited. Untranslated definitions (sutta
references) stay in English.

The translations are © their makers under the same licence as DPD:
CC BY-NC-SA 4.0, translated from the Digital Pāḷi Dictionary by Bodhirasa
Bhikkhu.
"""

import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import cast

from aksharamukha import transliterate

from tools.sinhala_tools import pos_dict

LANGS = {"si": "Sinhala", "th": "Thai", "hi": "Hindi", "my": "Myanmar"}
TITLES = {
    "si": "Digital Pāḷi Dictionary (සිංහල)",
    "th": "Digital Pāḷi Dictionary (ภาษาไทย)",
    "hi": "Digital Pāḷi Dictionary (हिन्दी)",
    "my": "Digital Pāḷi Dictionary (မြန်မာ)",
}
DESCRIPTIONS = {
    "si": "DPD {v}, definitions translated into Sinhala by AI (beta). "
    "Pāḷi in Sinhala script. Translated from the Digital Pāḷi Dictionary "
    "by Bodhirasa Bhikkhu, CC BY-NC-SA 4.0.",
    "th": "DPD {v}, definitions translated into Thai by AI (beta). "
    "Pāḷi in Thai script. Translated from the Digital Pāḷi Dictionary "
    "by Bodhirasa Bhikkhu, CC BY-NC-SA 4.0.",
    "hi": "DPD {v}, definitions translated into Hindi by AI (beta). "
    "Pāḷi in Devanagari script. Translated from the Digital Pāḷi Dictionary "
    "by Bodhirasa Bhikkhu, CC BY-NC-SA 4.0.",
    "my": "DPD {v}, definitions translated into Myanmar (Burmese) by AI (beta). "
    "Pāḷi in Myanmar script. Translated from the Digital Pāḷi Dictionary "
    "by Bodhirasa Bhikkhu, CC BY-NC-SA 4.0.",
}

POS_TH = {
    "letter": "อักษร", "prefix": "อุปสรรค", "cs": "วิกรณปัจจัย",
    "abbrev": "อักษรย่อ", "adj": "วิเสสนะ", "pron": "สัพพนาม",
    "ptp": "กิจจปัจจัย", "pp": "อดีตกิตก์", "masc": "ปุง", "aor": "อัชชัตตนี",
    "nt": "นปุง", "fem": "อิตถี", "ind": "นิบาต", "prp": "ปัจจุบันกิตก์",
    "abs": "ปุพพกาลกิริยา", "cond": "กาลาติปัตติ", "imperf": "หิยัตตนี",
    "sandhi": "สนธิ", "idiom": "สำนวน", "pr": "วัตตมานา", "inf": "ตุมัตถะ",
    "ger": "ภาวะ", "card": "สังขยา", "ordin": "ปูรณสังขยา", "imp": "ปัญจมี",
    "opt": "สัตตมี", "ve": "วาจก", "root": "ธาตุ", "suffix": "ปัจจัย",
    "perf": "ปโรกขา", "fut": "ภวิสสันติ",
}
POS_HI = {
    "letter": "अक्षर", "prefix": "उपसर्ग", "cs": "विकरण", "abbrev": "संक्षेप",
    "adj": "विशेषण", "pron": "सर्वनाम", "ptp": "कृत्य प्रत्यय", "pp": "भूतकालिक कृदन्त",
    "masc": "पुल्लिङ्ग", "aor": "अज्जतनी", "nt": "नपुंसकलिङ्ग", "fem": "स्त्रीलिङ्ग",
    "ind": "अव्यय", "prp": "वर्तमान कृदन्त", "abs": "पूर्वकालिक क्रिया",
    "cond": "कालातिपत्ति", "imperf": "हीयत्तनी", "sandhi": "सन्धि", "idiom": "मुहावरा",
    "pr": "वत्तमाना", "inf": "तुमन्त", "ger": "भाव", "card": "संख्यावाचक",
    "ordin": "क्रमवाचक", "imp": "पञ्चमी", "opt": "सत्तमी", "ve": "वाच्य",
    "root": "धातु", "suffix": "प्रत्यय", "perf": "परोक्खा", "fut": "भविस्सन्ति",
}
POS_MY = {
    "letter": "အက္ခရာ", "prefix": "ဥပသဂ္ဂ", "cs": "ဝိကရဏ", "abbrev": "အတိုကောက်",
    "adj": "ဂုဏ်နာမ်", "pron": "သဗ္ဗနာမ်", "ptp": "ကိစ္စပစ္စည်း", "pp": "အတီတကိတ်",
    "masc": "ပုလ္လိင်", "aor": "အဇ္ဇတနီ", "nt": "နပုံသကလိင်", "fem": "ဣတ္ထိလိင်",
    "ind": "နိပါတ်", "prp": "ပစ္စုပ္ပန်ကိတ်", "abs": "ပုဗ္ဗကာလကိရိယာ",
    "cond": "ကာလာတိပတ္တိ", "imperf": "ဟိယျတ္တနီ", "sandhi": "သန္ဓိ", "idiom": "စကားပုံ",
    "pr": "ဝတ္တမာနာ", "inf": "တုမန္တ", "ger": "ဘာဝ", "card": "သင်္ချာ",
    "ordin": "ပူရဏသင်္ချာ", "imp": "ပဉ္စမီ", "opt": "သတ္တမီ", "ve": "ဝါစက",
    "root": "ဓာတ်", "suffix": "ပစ္စည်း", "perf": "ပရောက္ခာ", "fut": "ဘဝိဿန္တိ",
}
POS_SI = {k: v["pos_si_full"].split(",")[0].split(".")[0].strip()
          for k, v in pos_dict.items()}

# other grammar words in DPD's grammar line; unknown words stay as they are
GRAM = {
    "si": {"comp": "සමාස", "abstr": "භාව නාම", "caus": "කාරිත", "pass": "කර්ම වාච්‍ය",
           "act": "කර්තෘ වාච්‍ය", "reflx": "ආත්මනේ පද", "desid": "ඉච්ඡාර්ථ",
           "intens": "අතිශයාර්ථ", "denom": "නාම ධාතු", "redup": "ද්විත්ව",
           "irreg": "අක්‍රමවත්", "neg": "නිෂේධ", "trans": "සකර්මක",
           "intrans": "අකර්මක", "ditrans": "ද්විකර්මක", "impers": "භාව වාච්‍ය",
           "pl": "බහු", "sg": "ඒක", "dual": "ද්වි", "der": "තද්ධිත",
           "adv": "ක්‍රියා විශේෂණ", "excl": "නිපාත", "interr": "ප්‍රශ්නාර්ථ",
           "emph": "අවධාරණ", "kammadhāraya": "කම්මධාරය", "dvanda": "ද්වන්ද්ව",
           "bahubbīhi": "බහුබ්බීහි", "tappurisa": "තප්පුරිස", "digu": "දිගු"},
    "th": {"comp": "สมาส", "abstr": "ภาวนาม", "caus": "เหตุกัตตุ", "pass": "กัมมวาจก",
           "act": "กัตตุวาจก", "reflx": "อัตตโนบท", "desid": "อิจฉัตถะ",
           "intens": "อติสยัตถะ", "denom": "นามธาตุ", "redup": "เทฺวภาวะ",
           "irreg": "ไม่ปกติ", "neg": "ปฏิเสธ", "trans": "สกัมมธาตุ",
           "intrans": "อกัมมธาตุ", "ditrans": "ทวิกัมมธาตุ", "impers": "ภาววาจก",
           "pl": "พหุ.", "sg": "เอก.", "dual": "ทวิ.", "der": "ตัทธิต",
           "adv": "กิริยาวิเสสนะ", "excl": "นิบาต", "interr": "ปุจฉา",
           "emph": "เน้นความ", "kammadhāraya": "กัมมธารยะ", "dvanda": "ทวันทะ",
           "bahubbīhi": "พหุพพีหิ", "tappurisa": "ตัปปุริสะ", "digu": "ทิคุ"},
    "hi": {"comp": "समास", "abstr": "भाववाचक", "caus": "प्रेरणार्थक", "pass": "कर्मवाच्य",
           "act": "कर्तृवाच्य", "reflx": "अत्तनोपद", "desid": "इच्छार्थक",
           "intens": "अतिशयार्थक", "denom": "नामधातु", "redup": "द्वित्व",
           "irreg": "अनियमित", "neg": "निषेध", "trans": "सकर्मक",
           "intrans": "अकर्मक", "ditrans": "द्विकर्मक", "impers": "भाववाच्य",
           "pl": "बहुवचन", "sg": "एकवचन", "dual": "द्विवचन", "der": "तद्धित",
           "adv": "क्रियाविशेषण", "excl": "विस्मयादिबोधक", "interr": "प्रश्नवाचक",
           "emph": "बलसूचक", "kammadhāraya": "कम्मधारय", "dvanda": "द्वन्द",
           "bahubbīhi": "बहुब्बीहि", "tappurisa": "तप्पुरिस", "digu": "दिगु"},
    "my": {"comp": "သမာသ်", "abstr": "ဘာဝနာမ်", "caus": "ဟေတုကတ္တား", "pass": "ကမ္မဝါစက",
           "act": "ကတ္တုဝါစက", "reflx": "အတ္တနောပုဒ်", "desid": "ဣစ္ဆတ္ထ",
           "intens": "အတိသယတ္ထ", "denom": "နာမဓာတ်", "redup": "ဒွေဘာဝ",
           "irreg": "ပုံမမှန်", "neg": "ပဋိသေဓ", "trans": "သကမ္မက",
           "intrans": "အကမ္မက", "ditrans": "ဒွိကမ္မက", "impers": "ဘာဝဝါစက",
           "pl": "ဗဟုဝုစ်", "sg": "ဧကဝုစ်", "dual": "ဒွိဝုစ်", "der": "တဒ္ဓိတ်",
           "adv": "ကြိယာဝိသေသန", "excl": "အာမေဍိတ်", "interr": "ပုစ္ဆာ",
           "emph": "အလေးပေး", "kammadhāraya": "ကမ္မဓာရယ", "dvanda": "ဒွန္ဒ",
           "bahubbīhi": "ဗဟုဗ္ဗီဟိ", "tappurisa": "တပ္ပုရိသ", "digu": "ဒိဂု"},
}

LABELS = {
    "si": {"Pāḷi": "පාලි", "Grammar": "ව්‍යාකරණ", "Root": "ධාතුව",
           "√ In Sandhi": "√ සන්ධියෙහි", "Base": "පාදය", "Construction": "පද සිද්ධිය",
           "Derivative": "ව්‍යුත්පන්නය", "Phonetic": "ශබ්ද විපර්යාසය",
           "Compound": "සමාසය", "Antonym": "විරුද්ධ පද", "Synonym": "සමාන පද",
           "Variant": "පාඨභේද", "Commentary": "අටුවාව", "Notes": "සටහන්",
           "Cognate": "සජාතීය පද", "Link": "සබැඳිය", "Non IA": "ඉන්දු-ආර්ය නොවන",
           "Sanskrit": "සංස්කෘත", "Sanskrit Root": "සංස්කෘත ධාතුව",
           "Submit a correction": "නිවැරදි කිරීමක් යොමු කරන්න"},
    "th": {"Pāḷi": "บาลี", "Grammar": "ไวยากรณ์", "Root": "ธาตุ",
           "√ In Sandhi": "√ ในสนธิ", "Base": "ฐาน", "Construction": "การประกอบศัพท์",
           "Derivative": "รูปแปลง", "Phonetic": "การเปลี่ยนเสียง",
           "Compound": "สมาส", "Antonym": "คำตรงข้าม", "Synonym": "คำพ้องความหมาย",
           "Variant": "รูปแปร", "Commentary": "อรรถกถา", "Notes": "หมายเหตุ",
           "Cognate": "คำร่วมเชื้อสาย", "Link": "ลิงก์", "Non IA": "ไม่ใช่อินโด-อารยัน",
           "Sanskrit": "สันสกฤต", "Sanskrit Root": "ธาตุสันสกฤต",
           "Submit a correction": "แจ้งแก้ไข"},
    "hi": {"Pāḷi": "पालि", "Grammar": "व्याकरण", "Root": "धातु",
           "√ In Sandhi": "√ सन्धि में", "Base": "आधार", "Construction": "पद-रचना",
           "Derivative": "व्युत्पन्न", "Phonetic": "ध्वनि परिवर्तन",
           "Compound": "समास", "Antonym": "विलोम", "Synonym": "पर्याय",
           "Variant": "पाठभेद", "Commentary": "अट्ठकथा", "Notes": "टिप्पणी",
           "Cognate": "सजातीय शब्द", "Link": "लिंक", "Non IA": "गैर-भारतीय-आर्य",
           "Sanskrit": "संस्कृत", "Sanskrit Root": "संस्कृत धातु",
           "Submit a correction": "सुधार भेजें"},
    "my": {"Pāḷi": "ပါဠိ", "Grammar": "သဒ္ဒါ", "Root": "ဓာတ်",
           "√ In Sandhi": "√ သန္ဓိတွင်", "Base": "အခြေ", "Construction": "ပုဒ်ပြီးပုံ",
           "Derivative": "ဆင့်ပွားပုဒ်", "Phonetic": "အသံပြောင်းခြင်း",
           "Compound": "သမာသ်", "Antonym": "ဆန့်ကျင်ဘက်စကား", "Synonym": "အနက်တူစကား",
           "Variant": "ပါဌ်ကွဲ", "Commentary": "အဋ္ဌကထာ", "Notes": "မှတ်ချက်",
           "Cognate": "ဆွေမျိုးစကား", "Link": "လင့်ခ်", "Non IA": "အင်ဒို-အာရိယန် မဟုတ်",
           "Sanskrit": "သက္ကတ", "Sanskrit Root": "သက္ကတ ဓာတ်",
           "Submit a correction": "ပြင်ဆင်ချက် ပေးပို့ရန်"},
}

SCRIPTS = {"th": "Thai", "hi": "Devanagari", "my": "Burmese"}
POS = {"hi": POS_HI, "my": POS_MY, "th": POS_TH}


@lru_cache(maxsize=None)
def to_script(text: str, lang: str) -> str:
    """Roman Pāḷi -> Sinhala / Thai / Devanagari / Myanmar script. Digits, punctuation and + > √
    pass through."""
    if not text:
        return text
    if lang == "si":
        out = transliterate.process(
            "IASTPali", "Sinhala", text, post_options=["SinhalaPali", "SinhalaConjuncts"]
        )
    else:
        out = transliterate.process("IASTPali", SCRIPTS[lang], text)
    return cast(str, out)


def load_translations(path: Path, lang: str) -> dict[int, str]:
    """headword id -> translated definition (only translated ones)."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    rows = con.execute(
        f"select h.id, d.{lang} from headwords h join definitions d on d.key = h.key "
        f"where d.{lang} is not null"
    ).fetchall()
    con.close()
    return dict(rows)


class _Root:
    def __init__(self, rt, lang: str):
        self._rt, self._lang = rt, lang

    def __getattr__(self, name):
        return getattr(self._rt, name)

    @property
    def root_clean(self):
        return to_script(self._rt.root_clean, self._lang)

    @property
    def root_in_comps(self):
        return to_script(self._rt.root_in_comps or "", self._lang)


class LangHeadword:
    """A DpdHeadword seen in another language. Everything not overridden is
    the original headword's."""

    def __init__(self, i, lang: str, meaning: str | None):
        self._i, self._lang, self._meaning = i, lang, meaning

    def __getattr__(self, name):
        return getattr(self._i, name)

    def _s(self, text):
        return to_script(text or "", self._lang)

    @property
    def lemma_1(self):
        return self._s(self._i.lemma_1)

    @property
    def lemma_2(self):
        return self._s(self._i.lemma_2)

    @property
    def construction(self):
        return self._s(self._i.construction)

    @property
    def root_base(self):
        return self._s(self._i.root_base)

    @property
    def compound_construction(self):
        return self._s(self._i.compound_construction)

    @property
    def synonym(self):
        return self._s(self._i.synonym)

    @property
    def antonym(self):
        return self._s(self._i.antonym)

    @property
    def variant(self):
        return self._s(self._i.variant)

    @property
    def rt(self):
        return _Root(self._i.rt, self._lang)

    @property
    def pos(self):
        table = POS_SI if self._lang == "si" else POS[self._lang]
        return table.get(self._i.pos, self._i.pos)

    @property
    def grammar(self):
        table = {**(POS_SI if self._lang == "si" else POS[self._lang]), **GRAM[self._lang]}
        return ", ".join(table.get(w.strip(), w.strip()) for w in self._i.grammar.split(","))

    @property
    def meaning_combo_html(self):
        if self._meaning is None:  # not translated: English as before
            return self._i.meaning_combo_html
        return f"<b>{self._meaning}</b>" if self._i.meaning_1 else self._meaning


_TH_RE = re.compile(r'<th valign="top">([^<]+)</th>')


def localise_labels(html: str, lang: str) -> str:
    labels = LABELS[lang]
    html = _TH_RE.sub(lambda m: f'<th valign="top">{labels.get(m.group(1), m.group(1))}</th>', html)
    return html.replace(">Submit a correction<", f">{labels['Submit a correction']}<")


def generate_tpr_data_lang(g, lang: str, translations_db: Path) -> None:
    """Run after tpr_exporter.generate_tpr_data: replaces the headword
    definitions in g.tpr_data_list with translated ones. Root entries
    (id 0) are left as built."""
    from exporter.goldendict.helpers import TODAY
    from exporter.jinja2_env import get_jinja2_env
    from tools.printer import printer as pr

    pr.green_tmr(f"compiling dpd headword data ({LANGS[lang]})")
    tr = load_translations(translations_db, lang)
    template = get_jinja2_env("exporter/tpr/templates").get_template("tpr_headword.jinja")
    defs = {}
    for i in g.dpd_db:
        html = template.render(i=LangHeadword(i, lang, tr.get(i.id)), today=TODAY)
        html = html.replace("\n", "").replace("    ", "").replace("'", "’")
        defs[i.id] = f"<p>{localise_labels(html, lang)}</p>"
    for d in g.tpr_data_list:  # word stays roman: TPR looks words up by it
        if int(d["id"]) in defs:
            d["definition"] = defs[int(d["id"])]
    pr.yes(f"{len(defs)} ({len(tr)} translated)")
