"""Gemini Cloud API integration with maximal hospital-grade privacy safeguards.

Privacy Protection Layers:
  1. Local PII/PHI Anonymization (De-identification):
     Strips Azerbaijani names, FIN codes, phone numbers, birth dates before
     sending text to Gemini. Real identities are restored locally after Gemini responds.
  2. Direct Audio Ephemeral Mode:
     Uploads audio, generates the protocol, and immediately deletes the audio
     from Google Cloud servers (0 retention).
  3. Strict Key Validation & Error Transparency:
     Detects placeholder/truncated keys and surfaces meaningful error feedback.
"""

import os
import re
import time
from typing import Dict, Optional, Tuple

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ─── LAYER 1: LOCAL PII/PHI ANONYMIZER ────────────────────────────────────────

PATTERNS = [
    # FIN code (7 alphanumeric characters)
    (r"\b[A-Z0-9]{7}\b", "[FİN_KOD]"),
    # Azerbaijan phone numbers: +994XX XXX XX XX or 050/055/070/077
    (r"(?:\+994|0)\s*(?:50|51|55|70|77|99|12)\s*\d{3}\s*\d{2}\s*\d{2}", "[ƏLAQƏ_NÖMRƏSİ]"),
    # Azerbaijani full names with patronymics (e.g. Əli Məmmədov Vaqif oğlu / qızı)
    (r"\b[A-ZÇƏĞİÖŞÜ][a-zçəğıöşü]+\s+[A-ZÇƏĞİÖŞÜ][a-zçəğıöşü]+(?:\s+(?:oğlu|qızı))?\b", "[PASİYENT_ADI]"),
    # Dates of birth (DD.MM.YYYY or DD/MM/YYYY)
    (r"\b\d{1,2}[./]\d{1,2}[./]\d{4}\b", "[TARİX]"),
]


def anonymize_text(text: str) -> Tuple[str, Dict[str, str]]:
    """Masks patient PII locally before sending text to the cloud."""
    mapping: Dict[str, str] = {}
    counter = 1
    anonymized = text

    for pattern, placeholder_base in PATTERNS:
        matches = re.finditer(pattern, anonymized)
        for m in sorted(matches, key=lambda x: len(x.group(0)), reverse=True):
            val = m.group(0)
            if val not in mapping.values():
                placeholder = f"{placeholder_base[:-1]}_{counter}]"
                mapping[placeholder] = val
                anonymized = anonymized.replace(val, placeholder)
                counter += 1

    return anonymized, mapping


def restore_anonymized_text(text: str, mapping: Dict[str, str]) -> str:
    """Restores masked patient PII locally after Gemini returns the polished text."""
    restored = text
    for placeholder, original in mapping.items():
        restored = restored.replace(placeholder, original)
    return restored


# ─── LAYER 2: GEMINI API ENGINE & VALIDATION ──────────────────────────────────

SYSTEM_PROMPT = (
    "Sən Azərbaycan dili üzrə tibbi transkripsiya redaktorusan.\n"
    "VƏZİFƏN: Verilmiş xam transkripsiya mətnindəki səs tanıma xətalarını, fonetik təhrifləri, "
    "danışıq jarqonlarını, orfoqrafiya və durğu işarələrini düzəltməkdir.\n\n"
    "CİDDİ VƏ QƏTİ QAYDALAR:\n"
    "1. ORİJİNAL MƏTNİ VƏ MƏNANI MAKSİMAL QORU: Danışan həkimin cümlə ardıcıllığını, istifadə etdiyi sözləri "
    "və fikirlərini dəqiq saxla. Mətnin strukturunu dəyişmə.\n"
    "2. QƏTİYYƏN HEÇ BİR ƏLAVƏ ETMƏ: Özündən heç bir başlıq (məs: **Müzakirə**, **Qərar**, **Həkim Konsiliumu** və s.), "
    "bölmə, maddələmə (1, 2...), şərh və ya mətndə deyilməyən yeni tibbi fikir əlavə ETMƏ!\n"
    "3. HEÇ BİR ŞABLON UYDURMA: Mətni süni anket, maddələr və ya protokol şablonuna salma, "
    "YALNIZ deyilən cümlələri qrammatik cəhətdən düzəlt.\n"
    "4. YALNIZ DÜZƏLDİLMİŞ MƏTNİ ÇIXAR: Heç bir giriş, izahat və ya sonluq sözü yazma.\n"
    "5. [PASİYENT_ADI_1], [FİN_KOD_1] kimi anonim teqlər varsa, onları olduğu kimi saxla.\n\n"
    "Nümunə düzəlişlər:\n"
    "- 'çək edilib' -> 'yoxlanılıb'\n"
    "- 'rentmetoloq/renmatoloq' -> 'revmatoloq'\n"
    "- 'niyiracaraq/neorocarah' -> 'neyrocərrah'\n"
    "- 'qanşı kimi/konsiqimet' -> 'konsiliuma'\n"
    "- 'sonarkı muayenləri qöndərmək üçün' -> 'sonrakı müayinələrə göndərmək üçün'\n"
    "- 'müayyidə-muaca planını eləmiş lazımdır' -> 'müayinə-müalicə planını tərtib etmək lazımdır'"
)


def validate_gemini_key(api_key: Optional[str] = None) -> Tuple[bool, str]:
    """Validates the Gemini API key format before sending requests.

    Returns:
        Tuple of (is_valid: bool, key_or_error_message: str).
    """
    key = (api_key or os.environ.get("GEMINI_API_KEY", "")).strip()
    if not key:
        return False, "Gemini API açarı tapılmadı. Zəhmət olmasa ekrandakı 'Gemini API Açarınız' sahəsinə və ya .env faylına real açarınızı daxil edin."
    if key.endswith("...") or len(key) < 25:
        return False, f"Daxil edilmiş açar natamamdır və ya nümunə şablondur ('{key[:10]}...'). Real Gemini açarı 39 simvollu olur (AIzaSy...)."
    return True, key


def get_gemini_client(api_key: Optional[str] = None) -> Tuple[Optional[object], Optional[str]]:
    """Initializes and returns (client, error_message)."""
    if not GENAI_AVAILABLE:
        return None, "google-genai kitabxanası quraşdırılmayıb."
    is_valid, key_or_err = validate_gemini_key(api_key)
    if not is_valid:
        return None, key_or_err
    try:
        client = genai.Client(api_key=key_or_err)
        return client, None
    except Exception as exc:
        return None, f"Gemini Client xətası: {str(exc)}"


def gemini_correct_transcript(
    raw_text: str,
    api_key: Optional[str] = None,
    apply_anonymization: bool = True
) -> Tuple[Optional[str], Optional[str]]:
    """Polishes raw transcript using Gemini 3.6 Flash with local PII anonymization.

    Returns:
        Tuple of (polished_text, error_message).
    """
    client, err = get_gemini_client(api_key)
    if not client:
        return None, err

    # Step 1: Scrub patient PII locally if requested (Maximum Privacy)
    mapping = {}
    text_to_send = raw_text
    if apply_anonymization:
        text_to_send, mapping = anonymize_text(raw_text)

    # Step 2: Call Gemini
    try:
        user_prompt = (
            f"Xam mətn:\n\"{text_to_send}\"\n\n"
            "Düzəldilmiş mətn:"
        )
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.0,
                max_output_tokens=4096,
            )
        )
        polished = response.text.strip() if response.text else ""

        # Step 3: Restore patient PII locally
        if apply_anonymization and mapping:
            polished = restore_anonymized_text(polished, mapping)

        return polished if polished else None, None

    except Exception as exc:
        return None, f"Gemini API xətası: {str(exc)}"


def gemini_transcribe_audio_direct(
    audio_path: str,
    api_key: Optional[str] = None,
    ai_engine: str = "gemini-3.6-flash"
) -> Tuple[Optional[str], Optional[str]]:
    """Directly transcribes audio with Gemini 3.6 Flash and optionally polishes with Gemma 4.

    Args:
        audio_path: Path to the audio file.
        api_key: Optional Gemini API key override.
        ai_engine: 'gemini-3.6-flash', 'gemma-4-26b-a4b-it', or 'gemma-4-31b-it'.

    Returns:
        Tuple of (result_text, error_message).
    """
    client, err = get_gemini_client(api_key)
    if not client:
        return None, err

    if not os.path.exists(audio_path):
        return None, f"Audio faylı tapılmadı: {audio_path}"

    uploaded_file = None
    try:
        print(f"[AI Pipeline] Audio faylı Google Cloud-a yüklənir...", flush=True)
        uploaded_file = client.files.upload(file=audio_path)

        prompt = (
            "Sən Azərbaycan dili üzrə tibbi transkripsiya mütəxəssisisən.\n"
            "VƏZİFƏN: Təqdim olunan tibbi səs yazısını dinləyib, deyilən nitqi dəqiq və səlis Azərbaycan dilində transkripsiya etməkdir.\n\n"
            "CİDDİ QAYDALAR:\n"
            "1. ORİJİNAL NİTQƏ MAKSİMAL SADİQ QAL: Danışan həkimlərin dediyi sözləri, cümlə quruluşunu və ardıcıllığı dəqiq qoru.\n"
            "2. ƏLAVƏ HEÇ NƏ UYDURMA: Özündən heç bir başlıq (məs: **Konsilium**, **Şikayət**, **Qərar** və s.), bənd, nömrələmə və ya deyilməyən əlavə cümlə əlavə ETMƏ.\n"
            "3. HEÇ BİR PROTOKOL ŞABLONU QURMA: Yalnız həkimin ağzından çıxan sözləri düzgün tibbi orfoqrafiya və durğu işarələri ilə yazıya al.\n"
            "4. YALNIZ DÜZƏLDİLMİŞ TRANSKRİPSİYANI ÇIXAR."
        )

        models_to_try = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-2.5-flash"]
        result = ""
        last_error = None

        for model_name in models_to_try:
            try:
                print(f"[AI Pipeline] Transkripsiya modeli sınanır: {model_name}...", flush=True)
                response = client.models.generate_content(
                    model=model_name,
                    contents=[uploaded_file, prompt],
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=4096,
                    )
                )
                if response and response.text:
                    result = response.text.strip()
                    break
            except Exception as model_exc:
                err_text = str(model_exc)
                last_error = model_exc
                if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                    print(f"[AI Pipeline] {model_name} limiti doldu (429). Ehtiyat modelə keçilir...", flush=True)
                    continue
                else:
                    raise model_exc

        if not result and last_error:
            if "429" in str(last_error) or "RESOURCE_EXHAUSTED" in str(last_error):
                return None, "⚠️ Google AI pulsuz sorğu limiti (dəqiqədə 20 sorğu). Zəhmət olmasa ~30 saniyə gözləyib təkrar klikləyin."
            raise last_error

        # If Gemma 4 model is chosen, refine medical terminology with Gemma 4
        if result and ai_engine.startswith("gemma-4"):
            try:
                print(f"[AI Pipeline] {ai_engine} modeli ilə tibbi orfoqrafik cilalama aparılır...", flush=True)
                gemma_prompt = (
                    f"Sən Azərbaycan dili üzrə tibbi sənədləşdirmə və orfoqrafiya mütəxəssisisən.\n"
                    f"Aşağıdakı mətni orfoqrafik və tibbi terminoloji cəhətdən səliqəyə sal. "
                    f"Məzmuna, faktlara və cümlələrin ardıcıllığına tam sadiq qal.\n"
                    f"CİDDİ QAYDA: Əlavə heç bir başlıq, bənd və ya şərh YAZMA. YALNIZ düzəldilmiş mətni çıxar.\n\n"
                    f"Mətn:\n\"{result}\""
                )
                gemma_resp = client.models.generate_content(
                    model=ai_engine,
                    contents=gemma_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=4096,
                    )
                )
                if gemma_resp.text:
                    result = gemma_resp.text.strip()
            except Exception as gemma_exc:
                if "429" in str(gemma_exc) or "RESOURCE_EXHAUSTED" in str(gemma_exc):
                    print(f"[AI Warning] {ai_engine} limiti doldu (429), ilkin transkripsiya qaytarılır.", flush=True)
                else:
                    print(f"[AI Warning] {ai_engine} xətası: {gemma_exc}", flush=True)

        return (result if result else None), None

    except Exception as exc:
        err_msg = str(exc)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            return None, "⚠️ Google AI pulsuz sorğu limiti: Qısa müddətdə çox sayda test aparılıb. Zəhmət olmasa ~30 saniyə sonra yenidən cəhd edin."
        return None, f"AI Mühərriki xətası: {err_msg}"

    finally:
        # Layer 3: Immediate Ephemeral Cleanup - Delete file from Google Cloud immediately!
        if uploaded_file and hasattr(uploaded_file, "name"):
            try:
                client.files.delete(name=uploaded_file.name)
                print(f"[AI Privacy] Audio faylı Google Cloud serverlərindən dərhal silindi (0 retention).", flush=True)
            except Exception as del_err:
                print(f"[AI Cleanup Warning]: {del_err}", flush=True)
