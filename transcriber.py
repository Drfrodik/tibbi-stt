"""Offline Speech-to-Text transcription engine using faster-whisper.

Two-stage pipeline:
  Stage 1 — faster-whisper: raw Azerbaijani transcript (phonetically noisy)
  Stage 2 — Local Ollama LLM (Gemma-4 12B): semantic medical correction

100% offline. No data leaves the local machine.
"""

import datetime
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from faster_whisper import WhisperModel

import config
from medical_lexicon import extract_recognized_medical_terms, normalize_medical_text
from llm_corrector import is_ollama_available, llm_correct_transcript

# Global model cache to avoid reloading weights
_MODEL_CACHE: Dict[str, WhisperModel] = {}


def get_whisper_model(model_name: str = config.DEFAULT_MODEL_NAME) -> WhisperModel:
    """Loads and caches the faster-whisper model.

    Args:
        model_name: Model identifier (e.g. 'small', 'turbo', 'base').

    Returns:
        Loaded WhisperModel instance.
    """
    global _MODEL_CACHE
    if model_name not in _MODEL_CACHE:
        print(f"[Offline STT] Loading faster-whisper model '{model_name}' on {config.DEVICE} ({config.COMPUTE_TYPE})...")
        model = WhisperModel(
            model_name,
            device=config.DEVICE,
            compute_type=config.COMPUTE_TYPE,
        )
        _MODEL_CACHE[model_name] = model
        print(f"[Offline STT] Model '{model_name}' loaded successfully!")
    return _MODEL_CACHE[model_name]


def transcribe_audio_file(
    audio_path: str,
    model_name: str = config.DEFAULT_MODEL_NAME,
    llm_mode: str = "gemma",
    gemini_api_key: Optional[str] = None
) -> Tuple[str, str, str, list, str]:
    """Transcribes an audio file offline or via private Gemini into clean Azerbaijani medical text.

    Args:
        audio_path: Path to the input audio file (MP3, WAV, M4A, etc.)
        model_name: faster-whisper model identifier ('medium', 'small', 'base')
        llm_mode: "gemma", "qwen", "gemini_hybrid", "gemini_direct", or "none".
        gemini_api_key: Optional Gemini API key if not set in .env.

    Returns:
        Tuple of (final_text, stage1_text, output_file_path, detected_terms, stage_info).
    """
    # ── SPECIAL: Pure Gemini Direct Audio (Whisper bypassed completely) ──
    if llm_mode == "gemini_direct":
        from gemini_corrector import gemini_transcribe_audio_direct
        print("[Gemini Direct] Birbaşa Gemini 3.6 Flash ilə səs tanıma (Whisper istifadə olunmur)...")
        gem_direct, err = gemini_transcribe_audio_direct(audio_path, api_key=gemini_api_key)
        if gem_direct:
            final_text = gem_direct
            stage_info = "⚡ Yalnız Gemini 3.6 Flash (100% Cloud / Whisper-siz / Efemer)"
            stage1_text = "(Səs birbaşa Gemini 3.6 Flash ilə tanındı - Whisper yüklənmədi)"
        else:
            stage_info = f"❌ Gemini API Xətası: {err}"
            final_text = f"⚠️ Gemini API Xətası Baş Verdi:\n{err}"
            stage1_text = ""

        detected_terms = extract_recognized_medical_terms(final_text)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tibbi_qeyd_{timestamp}.txt"
        output_file_path = str(config.OUTPUT_DIR / output_filename)
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write("=====================================================\n")
            f.write("TİBBİ SƏS-MƏTN PROTOKOLU\n")
            f.write(f"Tarix / Saat: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
            f.write(f"Mühərrik: {stage_info}\n")
            f.write("=====================================================\n\n")
            f.write("TRANSKRİPSİYA MƏTNİ:\n")
            f.write(final_text + "\n\n")
            if detected_terms:
                f.write("AŞKARLANAN TİBBİ TERMİNLƏR:\n")
                for item in detected_terms:
                    f.write(f" - [{item['domain']}] : {item['term']}\n")
            f.write("\n=====================================================\n")
        return final_text, stage1_text, output_file_path, detected_terms, stage_info

    model = get_whisper_model(model_name)

    # ── STAGE 1: faster-whisper raw transcription ────────────────────────────
    print(f"[Stage 1] faster-whisper ({model_name}) transkripsiya edir...")
    segments, info = model.transcribe(
        audio_path,
        language=config.TARGET_LANGUAGE,
        task=config.TASK,
        initial_prompt=config.MEDICAL_SEED_PROMPT,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
        repetition_penalty=1.2,
        no_repeat_ngram_size=3,
        condition_on_previous_text=False,
    )

    raw_segments = [seg.text.strip() for seg in segments]
    raw_text = " ".join(raw_segments)
    # Apply regex-based medical normalization (phonetic corrections + repetition removal)
    stage1_text = normalize_medical_text(raw_text)
    print(f"[Stage 1] Xam mətn: {stage1_text[:120]}...")

    # ── STAGE 2: LLM semantic correction ────────────────────────────────────
    final_text = stage1_text
    stage_info = f"Whisper ({model_name}) | Yalnız ASR"

    if llm_mode == "gemini_hybrid":
        from gemini_corrector import gemini_correct_transcript
        print("[Gemini Hybrid] Whisper + Lokal PII Anonimləşdirmə + Gemini 3.6 Flash...")
        gem_hybrid, err = gemini_correct_transcript(stage1_text, api_key=gemini_api_key, apply_anonymization=True)
        if gem_hybrid:
            final_text = gem_hybrid
            stage_info = f"Whisper ({model_name}) → 🔒 PII Maskalanma → ⚡ Gemini 3.6 Flash"
        else:
            stage_info = f"❌ Gemini API Xətası: {err}"
            final_text = f"⚠️ Gemini API Xətası Baş Verdi:\n{err}\n\n─── Whisper Xam Mətni (Müqayisə üçün) ───\n{stage1_text}"

    elif llm_mode in ("gemma", "gemma_medical", "gemma_general", "qwen"):
        ollama_ok = is_ollama_available()
        if ollama_ok:
            if llm_mode in ("gemma", "gemma_medical"):
                model_label = "Gemma-4 12B (Rəsmi Tibbi Protokol)"
            elif llm_mode == "gemma_general":
                model_label = "Gemma-4 12B (Sərbəst Nitq Redaktəsi)"
            else:
                model_label = "Qwen 2.5 3B (Ultra Sürətli)"
            print(f"[Stage 2] Ollama {model_label} redaktəsi başladı...")
            llm_result = llm_correct_transcript(stage1_text, model_choice=llm_mode, timeout=120)
            if llm_result:
                final_text = llm_result
                stage_info = f"Whisper ({model_name}) → {model_label} | 100% Offline"
                print(f"[Stage 2] {model_label} redaktəsi tamamlandı.")
            else:
                stage_info = f"Whisper ({model_name}) | LLM cavab vermədi → Xam nəticə"
        else:
            stage_info = f"Whisper ({model_name}) | Ollama aktiv deyil → Xam nəticə"

    # Detect recognized medical terms across domains (on final text)
    detected_terms = extract_recognized_medical_terms(final_text)

    # ── Write protocol file ──────────────────────────────────────────────────
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"tibbi_qeyd_{timestamp}.txt"
    output_file_path = str(config.OUTPUT_DIR / output_filename)

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("=====================================================\n")
        f.write("TİBBİ SƏS-MƏTN PROTOKOLU\n")
        f.write(f"Tarix / Saat: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"Mühərrik: {stage_info}\n")
        f.write("=====================================================\n\n")
        f.write("TRANSKRİPSİYA MƏTNİ:\n")
        f.write(final_text + "\n\n")
        if detected_terms:
            f.write("AŞKARLANAN TİBBİ TERMİNLƏR:\n")
            for item in detected_terms:
                f.write(f" - [{item['domain']}] : {item['term']}\n")
        f.write("\n=====================================================\n")

    return final_text, stage1_text, output_file_path, detected_terms, stage_info
