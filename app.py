"""Tibbi Səs-Mətn Tətbiqi (Gemini 3.6 Flash)."""

import os
import datetime
from pathlib import Path
import gradio as gr

import config
from gemini_corrector import gemini_transcribe_audio_direct
from medical_lexicon import extract_recognized_medical_terms

SAMPLE_AUDIO_PATH = str(config.SAMPLES_DIR / "konsilium_numune.mp3")


def process_audio(audio_path: str, api_key: str = ""):
    """Processes audio directly via Gemini 3.6 Flash and returns transcript and file."""
    if not audio_path:
        return "⚠️ Zəhmət olmasa səs faylı yükləyin və ya mikrofondan danışın.", None, ""

    if not os.path.exists(audio_path):
        return f"❌ Audio faylı tapılmadı: {audio_path}", None, ""

    key_to_use = api_key.strip() if api_key else None
    result_text, err = gemini_transcribe_audio_direct(audio_path, api_key=key_to_use)

    if err:
        return f"❌ Gemini API Xətası:\n{err}", None, ""

    # Detected terms
    detected_terms = extract_recognized_medical_terms(result_text)
    if detected_terms:
        terms_md = "<div class='terms-container'>"
        terms_md += "<div class='terms-header'>🩺 AŞKARLANAN TİBBİ TERMİNLƏR</div>"
        terms_md += "<div class='terms-chips'>"
        for item in detected_terms:
            terms_md += (
                f"<div class='term-chip'>"
                f"<span class='term-domain'>{item['domain']}</span>"
                f"<span class='term-val'>{item['term']}</span>"
                f"</div>"
            )
        terms_md += "</div></div>"
    else:
        terms_md = ""

    # Write protocol file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"tibbi_qeyd_{timestamp}.txt"
    output_file_path = str(config.OUTPUT_DIR / output_filename)

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("=====================================================\n")
        f.write("TİBBİ SƏS-MƏTN PROTOKOLU\n")
        f.write(f"Tarix / Saat: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write("=====================================================\n\n")
        f.write("TRANSKRİPSİYA MƏTNİ:\n")
        f.write(result_text + "\n\n")
        if detected_terms:
            f.write("AŞKARLANAN TİBBİ TERMİNLƏR:\n")
            for item in detected_terms:
                f.write(f" - [{item['domain']}] : {item['term']}\n")
        f.write("\n=====================================================\n")

    return result_text, output_file_path, terms_md


def save_api_key(key: str):
    """Saves user API key to .env file."""
    key = key.strip()
    if not key:
        return "⚠️ Zəhmət olmasa API açarını daxil edin."
    if len(key) < 25 or key.endswith("..."):
        return "❌ Açar natamamdır. Google AI Studio-dan 39 simvollu açarı daxil edin."

    env_path = config.BASE_DIR / ".env"
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={key}\n")
        os.environ["GEMINI_API_KEY"] = key
        return "✅ API açarı uğurla yadda saxlanıldı!"
    except Exception as exc:
        return f"❌ Xəta baş verdi: {str(exc)}"


CUSTOM_CSS = """
/* ─── Base & Mobile Stabilization ─────────────────────────────────────────── */
html, body {
    overflow-x: hidden !important;
    width: 100% !important;
    max-width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    touch-action: pan-y !important;
    -webkit-overflow-scrolling: touch;
}

*, *::before, *::after {
    box-sizing: border-box !important;
}

.gradio-container {
    max-width: 1000px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 24px 16px !important;
    overflow-x: clip !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, sans-serif !important;
}

/* ─── Premium Header (Theme Adaptive) ────────────────────────────────────── */
.header-premium {
    text-align: center;
    padding: 24px 16px 28px 16px;
    margin-bottom: 24px;
    background: var(--block-background-fill, #ffffff) !important;
    border: 1px solid var(--block-border-color, #e2e8f0) !important;
    border-radius: 20px;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.08);
}

.status-pill {
    display: inline-flex !important;
    align-items: center !important;
    gap: 8px !important;
    padding: 6px 16px !important;
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 9999px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.15) !important;
}

.status-pill-text {
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #f8fafc !important;
    letter-spacing: 0.02em !important;
}

.pulse-indicator {
    width: 8px !important;
    height: 8px !important;
    min-width: 8px !important;
    background: #10b981 !important;
    border-radius: 50% !important;
    box-shadow: 0 0 8px #10b981 !important;
    animation: pulse-ring 2s infinite ease-out !important;
}

@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

.header-title {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--body-text-color, #0f172a) !important;
    margin: 0 0 6px 0 !important;
    letter-spacing: -0.02em !important;
}

.header-desc {
    font-size: 14px !important;
    color: var(--body-text-color-subdued, #64748b) !important;
    margin: 0 !important;
}

/* ─── Explicit Theme Guarantees (Dark & Light) ───────────────────────────── */
.dark .header-premium {
    background: #1e293b !important;
    border-color: #334155 !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.3) !important;
}
.dark .header-title {
    color: #f8fafc !important;
}
.dark .header-desc {
    color: #94a3b8 !important;
}
.dark .terms-container {
    background: #1e293b !important;
    border-color: #334155 !important;
}
.dark .terms-header {
    color: #94a3b8 !important;
}
.dark .term-chip {
    background: #0f172a !important;
    border-color: #334155 !important;
    color: #f1f5f9 !important;
}

:not(.dark) .header-premium {
    background: #ffffff !important;
    border-color: #e2e8f0 !important;
}
:not(.dark) .header-title {
    color: #0f172a !important;
}
:not(.dark) .header-desc {
    color: #64748b !important;
}
:not(.dark) .terms-container {
    background: #ffffff !important;
    border-color: #e2e8f0 !important;
}
:not(.dark) .terms-header {
    color: #64748b !important;
}
:not(.dark) .term-chip {
    background: #f8fafc !important;
    border-color: #e2e8f0 !important;
    color: #1e293b !important;
}

/* ─── Premium Action Button ───────────────────────────────────────────────── */
.premium-btn {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 20px !important;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.25) !important;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    margin-top: 10px !important;
}

.premium-btn:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 24px rgba(2, 132, 199, 0.35) !important;
}

/* ─── WaveSurfer & Audio Anti-Jitter ───────────────────────────────────────── */
audio, 
.audio-container, 
[data-testid="audio"], 
.waveform-container,
.wrap {
    max-width: 100% !important;
    width: 100% !important;
    overflow: hidden !important;
    contain: paint !important;
}

canvas {
    max-width: 100% !important;
    height: auto !important;
    contain: strict !important;
}

.progress-bar, .loading, .status-tracker {
    max-width: 100% !important;
    overflow: hidden !important;
}

/* ─── Term Chips Grid ─────────────────────────────────────────────────────── */
.terms-container {
    margin-top: 16px;
    padding: 16px;
    border-radius: 14px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.terms-header {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.08em;
    margin-bottom: 10px;
    text-transform: uppercase;
}

.terms-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}

.term-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 12px;
    transition: all 0.15s ease;
}

.term-chip:hover {
    border-color: #0284c7;
}

.term-domain {
    font-weight: 700;
    color: #0284c7;
    font-size: 11px;
    text-transform: uppercase;
}

.term-val {
    font-weight: 500;
}

@media (max-width: 768px) {
    .gradio-container {
        padding: 10px !important;
    }
    .header-premium {
        padding: 18px 12px !important;
    }
    .header-title {
        font-size: 21px !important;
    }
}
"""

app_theme = gr.themes.Soft(
    primary_hue="sky",
    secondary_hue="emerald",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "-apple-system", "sans-serif"]
)

with gr.Blocks(title="Tibbi Səs-Mətn") as demo:
    gr.HTML("""
    <div class="header-premium">
        <div class="status-pill">
            <span class="pulse-indicator"></span>
            <span class="status-pill-text" style="color: #f8fafc !important; font-weight: 600;">Süni Zəka Mühərriki Aktivdir</span>
        </div>
        <h1 class="header-title">🩺 Tibbi Səs-Mətn</h1>
        <p class="header-desc">Səs yazısının yüksək dəqiqliklə rəsmi tibbi mətnə çevrilməsi</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="🎙️ Səs Yazısı (Mikrofon və ya Fayl)",
                editable=False,
            )

            with gr.Row():
                sample_btn = gr.Button("🎧 Nümunə Səs", variant="secondary", size="sm")

            transcribe_btn = gr.Button(
                "🚀 Mətnə Çevir",
                variant="primary",
                size="lg",
                elem_classes=["premium-btn"]
            )

            with gr.Accordion("🔑 API Açarı", open=False):
                with gr.Row():
                    api_key_input = gr.Textbox(
                        placeholder="Gemini API açarını daxil edin...",
                        type="password",
                        show_label=False,
                        scale=3,
                    )
                    save_key_btn = gr.Button("💾 Yadda Saxla", variant="secondary", scale=1)
                key_status_msg = gr.Markdown(value="")

        with gr.Column(scale=1):
            text_output = gr.Textbox(
                label="📋 Düzəldilmiş Mətn",
                placeholder="Mətn burada görünəcək...",
                lines=10,
                buttons=["copy"],
            )

            file_output = gr.File(
                label="💾 Mətni Endir (.txt)",
                file_types=[".txt"],
            )

            terms_display = gr.HTML(value="")

    # Event handlers
    save_key_btn.click(
        fn=save_api_key,
        inputs=[api_key_input],
        outputs=[key_status_msg]
    )

    sample_btn.click(
        fn=lambda: SAMPLE_AUDIO_PATH if os.path.exists(SAMPLE_AUDIO_PATH) else None,
        inputs=[],
        outputs=[audio_input]
    )

    transcribe_btn.click(
        fn=process_audio,
        inputs=[audio_input, api_key_input],
        outputs=[text_output, file_output, terms_display]
    )

if __name__ == "__main__":
    is_hf = os.environ.get("SPACE_ID") is not None
    _, local_url, share_url = demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=not is_hf,
        theme=app_theme,
        css=CUSTOM_CSS,
        inbrowser=False
    )
    print(f"LOCAL_URL: {local_url}", flush=True)
    if share_url:
        print(f"SHARE_URL: {share_url}", flush=True)
