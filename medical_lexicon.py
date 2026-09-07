"""Multi-specialty medical lexicon and text normalization module.

Covers surgery, cardiology, oncology, neurology, gastroenterology,
radiology, laboratory, and pharmacology terminology in Azerbaijani.
Provides phonetic and structural corrections for speech-to-text outputs.
"""

import re
from typing import Dict, List, Set, Tuple

# Comprehensive multi-specialty Azerbaijani medical terminology dictionary
MEDICAL_DOMAINS: Dict[str, List[str]] = {
    "Cərrahiyyə & Travmatologiya": [
        "laparoskopiya", "laparoskopik", "laparotomiya", "xolesistektomiya", "appendektomiya",
        "rezeksiya", "anastomoz", "torakotomiya", "trepanasiya", "osteosintez", "osteomielit",
        "yırtıq plastikası", "drenaj", "gemostaz", "traxeostomiya", "preoperativ", "postoperativ",
        "intravaskulyar", "amputasiya", "nekroz", "yaralanma", "hematoma", "hemoperitoneum"
    ],
    "Kardiologiya & Angiologiya": [
        "miokard infarktı", "stenokardiya", "kardiomiopatiya", "arterial hipertenziya",
        "hipotenziya", "taxikardiya", "bradikardiya", "aritmiya", "ekokardioqrafiya",
        "angioqrafiya", "stentləmə", "ateroskleroz", "sol mədəcik", "sağ mədəcik",
        "qulaqcıq fibrillyasiyası", "troponin", "koronar damarlar", "işemiya", "kardioqramma"
    ],
    "Onkologiya & Hematologiya": [
        "adenokarsinoma", "metastaz", "limfoma", "leykemiya", "karsinoma", "biopsiya",
        "histopatologiya", "histoloji", "neoplaziya", "bədxassəli", "xoşxassəli", "sitostatik",
        "kimyaterapiya", "radioterapiya", "trombositopeniya", "leykopeniya", "blast hüceyrələr",
        "onkomarker", "kaxeksiya", "melanoma", "sarkoma"
    ],
    "Nevrologiya & Neyrocərrahiyyə": [
        "ensefalopatiya", "serebrovaskulyar", "işemik insult", "hemorragik insult",
        "anevrizma", "kəllədaxili hipertenziya", "neyropatiya", "parez", "plegiya",
        "epilepsiya", "konvulsiya", "meningit", "qlioblastoma", "reflekslər", "koma"
    ],
    "Qastroenterologiya & Terapiya": [
        "xolesistit", "pankreatit", "sirroz", "hepatosplenomeqaliya", "ezofagit", "qastrit",
        "duodenit", "kolit", "bağırsaq keçməməzliyi", "asit", "pankreas", "qaraciyər çatışmazlığı",
        "qastroenterokolit", "reflyuks", "xolangit"
    ],
    "Pulmonologiya": [
        "pnevmoniya", "bronxit", "emfizema", "plevrit", "tənəffüs çatışmazlığı",
        "bronxoskopiya", "dispnoe", "hemoptizi", "ağciyər atelektazı", "hipoksiya"
    ],
    "Radiologiya & Funksional Diaqnostika": [
        "kompüter tomoqrafiyası", "KT", "maqnit-rezonans tomoqrafiya", "MRT",
        "ultrasəs müayinəsi", "USM", "rentgenoqrafiya", "PET-KT", "hipodens ocaq",
        "hiperdens", "kontrast maddə", "exogenlik", "kalsinat", "kista"
    ],
    "Laboratoriya & Biokimya": [
        "leykositoz", "leykopeniya", "eritrosit", "hemoqlobin", "trombosit",
        "eritrositlərin çökmə sürəti", "EÇS", "C-reaktiv zülal", "CRZ", "bilirubin",
        "kreatinin", "sidik cövhəri", "ALT", "AST", "qlükoza", "qələvi fosfataza",
        "koaquloqramma", "asidoz", "hipokaliemiya", "hiperkaliemiya"
    ],
    "Farmakologiya & Təyinat": [
        "antibiotikoterapiya", "antikoaqulyant", "antiplatelet", "analgetik",
        "kortikosteroid", "diuretik", "infuziya", "venadaxili", "əzələdaxili",
        "doza", "sefalosporin", "heparin", "morfin", "analgin"
    ]
}

# Common ASR phonetic splits and transcription errors to standard Azerbaijani medical spelling
PHONETIC_CORRECTIONS: List[Tuple[re.Pattern, str]] = [
    # General medical protocol phrasing
    (re.compile(r"\btip\s*bir\s*konsilium\b", re.IGNORECASE), "tibbi konsilium"),
    (re.compile(r"\bfurotokalı\b", re.IGNORECASE), "protokolu"),
    (re.compile(r"\bprotokalı\b", re.IGNORECASE), "protokolu"),

    # Surgery & Procedures
    (re.compile(r"\bLaporoscopic\s*Exilocystectomia\b", re.IGNORECASE), "laparoskopik xolesistektomiya"),
    (re.compile(r"\bleparos\s*kopik\b", re.IGNORECASE), "laparoskopik"),
    (re.compile(r"\blaparo\s*skopik\b", re.IGNORECASE), "laparoskopik"),
    (re.compile(r"\blaparo\s*skopiya\b", re.IGNORECASE), "laparoskopiya"),
    (re.compile(r"\bıksılı\s*sistəktomiy[yəea]+\b", re.IGNORECASE), "xolesistektomiya"),
    (re.compile(r"\bxole\s*sistektomiya\b", re.IGNORECASE), "xolesistektomiya"),
    (re.compile(r"\bxole\s*sistit\b", re.IGNORECASE), "xolesistit"),
    (re.compile(r"\bəksılı\s*sistetmüyn\b", re.IGNORECASE), "xolesistit"),
    (re.compile(r"\bəksili\s*sistet\b", re.IGNORECASE), "xolesistit"),
    (re.compile(r"\bıksılı\s*sastit\b", re.IGNORECASE), "xolesistit"),
    (re.compile(r"\bxalestestit\b", re.IGNORECASE), "xolesistit"),
    (re.compile(r"\bPreoperative\b", re.IGNORECASE), "preoperativ"),
    (re.compile(r"\bpıre\s*operativ\b", re.IGNORECASE), "preoperativ"),
    (re.compile(r"\bpre\s*operativ\b", re.IGNORECASE), "preoperativ"),
    (re.compile(r"\bpost\s*operativ\b", re.IGNORECASE), "postoperativ"),
    (re.compile(r"\bQirrahiyi\s*komissiyası\b", re.IGNORECASE), "cərrahiyyə komissiyası"),
    (re.compile(r"\bQirahiyi\s*Komissiası\b", re.IGNORECASE), "cərrahiyyə komissiyası"),

    # Hematology & Laboratory
    (re.compile(r"\b[viı\s]*trombositopiniya\b", re.IGNORECASE), " və trombositopeniya"),
    (re.compile(r"\bturombositopniyə\b", re.IGNORECASE), "trombositopeniya"),
    (re.compile(r"\btrambasit\s*openiya\b", re.IGNORECASE), "trombositopeniya"),
    (re.compile(r"\btrombosit\s*openiya\b", re.IGNORECASE), "trombositopeniya"),
    (re.compile(r"\blekozitos\b", re.IGNORECASE), "leykositoz"),
    (re.compile(r"\btəyikozytoz\b", re.IGNORECASE), "leykositoz"),
    (re.compile(r"\bleyko\s*sitoz\b", re.IGNORECASE), "leykositoz"),
    (re.compile(r"\bleykasitoz\b", re.IGNORECASE), "leykositoz"),

    # Radiology
    (re.compile(r"\bkomputer\s*tomografiyası\b", re.IGNORECASE), "kompüter tomoqrafiyası"),
    (re.compile(r"\bkomputır\s*tomografiyası\b", re.IGNORECASE), "kompüter tomoqrafiyası"),
    (re.compile(r"\bkompyuter\s*tomoqrafiyasi\b", re.IGNORECASE), "kompüter tomoqrafiyası"),
    (re.compile(r"\bVRT\b", re.IGNORECASE), "və MRT"),
    (re.compile(r"\bvmrt\b", re.IGNORECASE), "və MRT"),
    (re.compile(r"\bməyriyətə\b", re.IGNORECASE), "MRT"),
    (re.compile(r"\bemerti\b", re.IGNORECASE), "MRT"),
    (re.compile(r"\be\s*m\s*er\s*ti\b", re.IGNORECASE), "MRT"),
    (re.compile(r"\bkayte\b", re.IGNORECASE), "KT"),
    (re.compile(r"\bka\s*te\b", re.IGNORECASE), "KT"),
    (re.compile(r"\byuesem\b", re.IGNORECASE), "USM"),
    (re.compile(r"\bu\s*es\s*em\b", re.IGNORECASE), "USM"),

    # Cardiology
    (re.compile(r"\bCardioloqun\b", re.IGNORECASE), "kardioloqun"),
    (re.compile(r"\bkardiologun\b", re.IGNORECASE), "kardioloqun"),
    (re.compile(r"\bRheingör[- ]*MioKart\s*infarktır\s*iski\s*yoğdur\b", re.IGNORECASE), "rəyinə görə miokard infarktı riski yoxdur"),
    (re.compile(r"\bRheingör[- ]*myocard\s*infarkti\s*riski\s*yoğdur\b", re.IGNORECASE), "rəyinə görə miokard infarktı riski yoxdur"),
    (re.compile(r"\bMioKart\s*infarkt[ıi]\b", re.IGNORECASE), "miokard infarktı"),
    (re.compile(r"\bmyocard\s*infarkti\b", re.IGNORECASE), "miokard infarktı"),
    (re.compile(r"\bmüyor\s*kard\s*infarktiris\s*ki\b", re.IGNORECASE), "miokard infarktı riski"),
    (re.compile(r"\bmeyokard\s*infarkt[ıi]\b", re.IGNORECASE), "miokard infarktı"),
    (re.compile(r"\bmeyokard\b", re.IGNORECASE), "miokard"),
    (re.compile(r"\bArterial\s*hypertenzia\b", re.IGNORECASE), "arterial hipertenziya"),
    (re.compile(r"\bArterial\s*hypertənziya\b", re.IGNORECASE), "arterial hipertenziya"),
    (re.compile(r"\bartiril\s*hipertenziyə\b", re.IGNORECASE), "arterial hipertenziya"),
    (re.compile(r"\barterial\s*hiper\s*tenziya\b", re.IGNORECASE), "arterial hipertenziya"),
    (re.compile(r"\bkardio\s*miopatiya\b", re.IGNORECASE), "kardiomiopatiya"),

    # Pharmacology
    (re.compile(r"\bantibiotik\s*oterapiy[yəea]+\b", re.IGNORECASE), "antibiotikoterapiya"),
    (re.compile(r"\bantibiotiko\s*terapiya\b", re.IGNORECASE), "antibiotikoterapiya"),

    # Neurology & Gastroenterology
    (re.compile(r"\bensefalo\s*patiya\b", re.IGNORECASE), "ensefalopatiya"),
    (re.compile(r"\badeno\s*karsinoma\b", re.IGNORECASE), "adenokarsinoma"),
    (re.compile(r"\bhepato\s*splenomeqaliya\b", re.IGNORECASE), "hepatosplenomeqaliya"),
    (re.compile(r"\bpankreato\s*duodenal\b", re.IGNORECASE), "pankreatoduodenal"),
    (re.compile(r"\bserebro\s*vaskulyar\b", re.IGNORECASE), "serebrovaskulyar"),

    # Dialectal & Acoustic Consilium Corrections
    (re.compile(r"\bkəstəmizin\b", re.IGNORECASE), "xəstəmizin"),
    (re.compile(r"\bkəstənin\b", re.IGNORECASE), "xəstənin"),
    (re.compile(r"\bkəstə\b", re.IGNORECASE), "xəstə"),
    (re.compile(r"\bnevraloji\s*simtom[lar]*\b", re.IGNORECASE), "nevroloji simptomlar"),
    (re.compile(r"\beləmət\s*ologun\b", re.IGNORECASE), "hematoloqun"),
    (re.compile(r"\beləmət\s*oloqun\b", re.IGNORECASE), "hematoloqun"),
    (re.compile(r"\bqadiyologun\b", re.IGNORECASE), "kardioloqun"),
    (re.compile(r"\bqadiyoloqun\b", re.IGNORECASE), "kardioloqun"),
    (re.compile(r"\bniyir\s*azərəm\b", re.IGNORECASE), "nevropatoloqun"),
    (re.compile(r"\bkansik\s*imat\b", re.IGNORECASE), "konsilium"),
    (re.compile(r"\byiküm\s*bir\s*qərər\b", re.IGNORECASE), "yekun bir qərar"),
    (re.compile(r"\bdoğrulqaçıq\b", re.IGNORECASE), "dəqiqləşdirilib"),
]


def remove_repetitive_loops(text: str) -> str:
    """Detects and eliminates runaway hallucination loops (e.g. 'niyə niyə niyə...').

    Args:
        text: Raw text potentially containing repetitive loops.

    Returns:
        Cleaned text with repetitive phrases collapsed.
    """
    if not text:
        return ""

    # Collapse any phrase/word repeated 2 or more times
    # e.g., "niyə niyə niyə..." -> "" (or single token)
    pattern = r"\b(\w+(?:\s+\w+)?)(?:\s+\1){2,}\b"
    cleaned = re.sub(pattern, r"\1", text, flags=re.IGNORECASE)

    # Clean trailing repeated single tokens
    tokens = cleaned.split()
    if len(tokens) >= 3:
        # Check if the end of the text is stuck repeating
        last_tok = tokens[-1].lower()
        if tokens[-2].lower() == last_tok and tokens[-3].lower() == last_tok:
            while tokens and tokens[-1].lower() == last_tok:
                tokens.pop()
            cleaned = " ".join(tokens)

    return cleaned


def normalize_medical_text(text: str) -> str:
    """Applies phonetic corrections and cleans formatting for medical transcripts.

    Args:
        text: Raw transcribed string.

    Returns:
        Normalized string with corrected medical terminology and standard punctuation.
    """
    if not text:
        return ""

    # First: Remove any hallucination loops
    result = remove_repetitive_loops(text)

    # Second: Apply phonetic/orthographic medical rules
    for pattern, replacement in PHONETIC_CORRECTIONS:
        result = pattern.sub(replacement, result)

    # Normalize multiple whitespace
    result = re.sub(r"\s+", " ", result).strip()

    # Ensure sentence beginnings are capitalized
    sentences = re.split(r"([.!?]\s+)", result)
    capitalized_sentences = []
    for s in sentences:
        if s and not re.match(r"^[.!?]\s+$", s):
            s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        capitalized_sentences.append(s)

    result = "".join(capitalized_sentences)
    return result


def extract_recognized_medical_terms(text: str) -> List[Dict[str, str]]:
    """Identifies and classifies medical terminology present in the text.

    Args:
        text: Transcribed and normalized text.

    Returns:
        List of dictionaries with 'term' and 'domain' information.
    """
    if not text:
        return []

    found_terms: List[Dict[str, str]] = []
    text_lower = text.lower()
    seen: Set[str] = set()

    for domain, terms in MEDICAL_DOMAINS.items():
        for term in terms:
            term_lower = term.lower()
            if term_lower in seen:
                continue
            # Match whole word or compound phrase
            pattern = rf"\b{re.escape(term_lower)}\b"
            if re.search(pattern, text_lower):
                found_terms.append({"term": term, "domain": domain})
                seen.add(term_lower)

    return found_terms
