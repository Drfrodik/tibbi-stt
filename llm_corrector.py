"""Offline LLM post-processor supporting dual modes:

  1. "gemma" - Gemma-4 12B: Maximum accuracy, deep semantic restructuring, official medical protocol format.
  2. "qwen"  - Qwen 2.5 3B: Ultra-fast (1-2s), lightweight for CPU-only / 8GB RAM systems.

100% offline via local Ollama server at 127.0.0.1:11434.
No data leaves the hospital network.
"""

import re
import time
import requests
from typing import Optional

from medical_lexicon import normalize_medical_text

OLLAMA_BASE_URL = "http://127.0.0.1:11434"
MODEL_GEMMA = "hf.co/unsloth/gemma-4-12b-it-GGUF:Q4_K_M"
MODEL_QWEN = "qwen2.5:3b"

# Specialized Medical & General transcription instructions
SYSTEM_PROMPT_MEDICAL = (
    "Sən Azərbaycanın aparıcı klinikalarında çalışan təcrübəli tibbi redaktor və ekspert həkimsən.\n"
    "VƏZİFƏN: Həkimin səsli diktəsini səliqəli, rəsmi, akademik və qüsursuz TİBBİ KLİNİK PROTOKOL "
    "(həkim rəyi, epikriz) dilinə çevirməkdir.\n\n"
    "CİDDİ TƏLİMATLAR:\n"
    "1. Təhrif olunmuş, fonetik xətaları və anlaşılmaz ifadələri tibbi məntiqlə bərpa et:\n"
    "   - 'qastrın / xəstərimiz' -> 'xəstəmizin'\n"
    "   - 'doğruluqla çəkilib' -> 'dəqiqliklə qiymətləndirilib / yoxlanılıb'\n"
    "   - 'hala zədəki sonraki mərhələləri' -> 'hazırkı və növbəti mərhələlərdə vəziyyətini'\n"
    "   - 'baxışları müvafiqdir' -> 'konsultasiyası / baxışı məqsədəuyğundur'\n"
    "   - 'macarlanı kəni eləmək lazımdır' -> 'müayinə-müalicə planını təyin etmək lazımdır'\n"
    "   - 'qərar qəbləmən' -> 'yekun qərara gəlmək'\n"
    "   - 'rentmetoloq' -> 'revmatoloq', 'çək edilib' -> 'yoxlanılıb', 'müəyyənə' -> 'müayinə'\n"
    "2. Danışıq dili ifadələrini və qeyri-rəsmi sözləri peşəkar həkim protokol üslubuna uyğunlaşdır.\n"
    "3. YALNIZ düzəldilmiş tibbi mətni çıxar. Heç bir başlıq, giriş və ya əlavə şərh yazma."
)

SYSTEM_PROMPT_GENERAL = (
    "Sən peşəkar Azərbaycan dili nitq və transkripsiya redaktorusan.\n"
    "VƏZİFƏN: Səs tanıma (Speech-to-Text) zamanı yaranmış fonetik təhrifləri, eşitmə xətalarını, "
    "tələffüz qüsurlarını, orfoqrafiya və durğu işarələrini cümlənin kontekstinə uyğun bərpa etməkdir.\n\n"
    "DÜZƏLİŞ QAYDALARI:\n"
    "1. Kontekstual Bərpa: Eşitmə zamanı təhrif olunmuş adları, qırıq və anlaşılmaz sözləri cümlənin ümumi məzmununa görə bərpa et "
    "('xeyr olsun' -> 'xeyir olsun', 'mehtəbdə' -> 'məktəbdə', 'köşağlar' -> 'uşaqlar', 'daha mən sulaklı' -> 'daha məsuliyyətli', 'varut xoştur' -> 'çox xoşdur').\n"
    "2. Durğu İşarələri: Cümlələri aydın, səlis və oxunaqlı şəkildə formalaşdır, nöqtə və vergülləri dəqiq qoy.\n"
    "3. YALNIZ düzəldilmiş mətni çıxar. Heç bir giriş sözü, izahat, şərh və ya başlıq yazma."
)

SYSTEM_PROMPT_QWEN = (
    "Sən Azərbaycan dili üzrə transkripsiya redaktorusan. "
    "Vəzifən: Xam səs mətndəki fonetik eşitmə səhvlərini, orfoqrafiya və durğu işarələrini kontekstə uyğun düzəltməkdir. "
    "QAYDALAR: Cümlələri səlis və oxunaqlı et. Özündən heç bir şərh və ya başlıq yazma. Yalnız düzəldilmiş mətni yaz."
)


def _clean_response(text: str) -> str:
    """Strips thinking/channel tags and unwanted model commentary."""
    text = re.sub(r"<\|channel>.*?<channel\|>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"<thought>.*?</thought>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"\n?\*?\(Qeyd:[^)]*\)\*?\s*$", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"\n?\*\([^)]*\)\*\s*$", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"^(?:\*\*)?(?:Protokol|Düzəldilmiş Protokol|Düzəldilmiş mətn|Düzəldilmiş səlis mətn|Düzəldilmiş rəsmi tibbi protokol mətni)[:\*]*\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^Xam (?:transkripsiya|diktə).*?Düzəldilmiş (?:rəsmi tibbi protokol |səlis )?mətn(?:i)?:\s*", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    text = text.strip('"').strip("'").strip()
    return text


def is_ollama_available() -> bool:
    """Checks if the local Ollama server is running and reachable."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def get_available_llm_models() -> list:
    """Returns a list of model names currently available in Ollama."""
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if r.status_code == 200:
            return [m.get("name", "") for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def llm_correct_transcript(
    raw_text: str,
    model_choice: str = "gemma",
    timeout: int = 120
) -> Optional[str]:
    """Corrects raw transcript using the selected local Ollama model.

    Args:
        raw_text: Raw phonetically distorted Azerbaijani medical transcript.
        model_choice: "gemma" (Gemma-4 12B, max accuracy) or "qwen" (Qwen 2.5 3B, ultra fast).
        timeout: Request timeout in seconds.

    Returns:
        Corrected text string, or None if Ollama is unavailable.
    """
    if not is_ollama_available():
        return None

    if model_choice == "qwen":
        # Ultra-fast mode using Qwen 2.5 3B via chat API
        try:
            r = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": MODEL_QWEN,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_QWEN},
                        {"role": "user", "content": f"Xam transkripsiya:\n\"{raw_text}\"\n\nDüzəldilmiş səlis mətn:"}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 800}
                },
                timeout=timeout
            )
            r.raise_for_status()
            content = r.json().get("message", {}).get("content", "").strip()
            cleaned = _clean_response(content)
            # Apply regex medical lexicon as a safety net for any terms 3B model might miss
            cleaned = normalize_medical_text(cleaned)
            return cleaned if cleaned else None
        except Exception as e:
            print(f"[LLM Corrector Qwen] Warning: {e}")
            return None

    else:
        # Gemma-4 12B: Support both deep medical protocol and general speech
        if model_choice in ("gemma", "gemma_medical"):
            system_instruction = SYSTEM_PROMPT_MEDICAL
            target_label = "Düzəldilmiş rəsmi tibbi protokol mətni:"
            temperature = 0.1
        else:
            system_instruction = SYSTEM_PROMPT_GENERAL
            target_label = "Düzəldilmiş səlis mətn:"
            temperature = 0.2

        full_prompt = (
            f"{system_instruction}\n\n"
            f"Xam transkripsiya:\n\"\"\"{raw_text}\"\"\"\n\n"
            f"{target_label}"
        )
        payload = {
            "model": MODEL_GEMMA,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_predict": 1200,
            }
        }

        try:
            response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
            if response.status_code == 500:
                print("[LLM Corrector Gemma] Model GPU/CPU-ya yüklənir, 20s gözlənilir...")
                time.sleep(20)
                response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)

            response.raise_for_status()
            raw_resp = response.json().get("response", "").strip()
            corrected = _clean_response(raw_resp)
            return corrected if corrected else None

        except Exception as e:
            print(f"[LLM Corrector Gemma] Warning: {e}")
            return None
