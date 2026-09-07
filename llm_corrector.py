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

# Medical system instructions
SYSTEM_PROMPT_GEMMA = (
    "Sən Azərbaycan dili üzrə tibbi transkripsiya redaktorusan.\n"
    "VƏZİFƏN: Verilmiş xam transkripsiya mətnindəki səs tanıma xətalarını, fonetik təhrifləri, "
    "orfoqrafiya və durğu işarələrini düzəltməkdir.\n\n"
    "CİDDİ QAYDALAR:\n"
    "1. ORİJİNAL MƏTNİ MAKSİMAL QORU: Danışan həkimin cümlə ardıcıllığını, istifadə etdiyi sözləri və fikrini dəqiq saxla.\n"
    "2. QƏTİYYƏN HEÇ BİR ƏLAVƏ ETMƏ: Özündən heç bir başlıq (məs: **Müzakirə**, **Qərar**), bölmə, nömrələmə (1, 2...), şərh və ya mətndə deyilməyən yeni tibbi fikir əlavə etmə!\n"
    "3. HEÇ BİR ŞABLON UYDURMA: YALNIZ deyilən cümlələri qrammatik cəhətdən düzəlt.\n"
    "4. YALNIZ DÜZƏLDİLMİŞ MƏTNİ ÇIXAR: Heç bir giriş, başlıq və ya izahat yazma.\n\n"
    "Nümunə düzəlişlər:\n"
    "- 'çək edilib' -> 'yoxlanılıb'\n"
    "- 'rentmetoloq/renmatoloq' -> 'revmatoloq'\n"
    "- 'neorocarah/niyiracaraq' -> 'neyrocərrah'\n"
    "- 'qanşı kimi/konsiqimet' -> 'konsiliuma'\n"
    "- 'sonarkı müənnələr' -> 'sonrakı müayinələr'\n"
    "- 'müəyyənə-muhaca planı' -> 'müayinə-müalicə planı'"
)

SYSTEM_PROMPT_QWEN = (
    "Sən Azərbaycan dili üzrə tibbi transkripsiya redaktorusan. "
    "Vəzifən: Xam mətndəki fonetik səhvləri ('çək edilib' -> 'yoxlanılıb', "
    "'rentmetoloq' -> 'revmatoloq', 'sonarkı müənnələr' -> 'növbəti müayinələr') düzəltməkdir. "
    "QAYDALAR: Orijinal mətni və cümlə sırasını dəqiq qoru. "
    "Özündən heç bir başlıq, bənd (1, 2) və ya əlavə fikir uydurma. "
    "Yalnız və yalnız düzəldilmiş mətni yaz."
)


def _clean_response(text: str) -> str:
    """Strips thinking/channel tags and unwanted model commentary."""
    text = re.sub(r"<\|channel>[^<]*<channel\|>", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"\n?\*?\(Qeyd:[^)]*\)\*?\s*$", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"\n?\*\([^)]*\)\*\s*$", "", text, flags=re.DOTALL).strip()
    text = re.sub(r"^(?:\*\*)?(?:Protokol|Düzəldilmiş Protokol|Düzəldilmiş mətn)[:\*]*\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"^Xam mətndəki.*?Düzəldilmiş mətn:\s*", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
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
                        {"role": "user", "content": f"Xam transkripsiya:\n\"{raw_text}\"\n\nDüzəldilmiş rəsmi konsilium protokolu:"}
                    ],
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 400}
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
        # Maximum accuracy mode using Gemma-4 12B
        full_prompt = (
            f"{SYSTEM_PROMPT_GEMMA}\n\n"
            f"Xam transkripsiya:\n\"{raw_text}\"\n\n"
            f"Düzəldilmiş rəsmi tibbi protokol:"
        )
        payload = {
            "model": MODEL_GEMMA,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_predict": 500,
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
