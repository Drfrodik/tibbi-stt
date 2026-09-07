"""Tibbi Səs-Mətn Tətbiqi (100% Yerli / Oflayn)."""

import os
import datetime
from pathlib import Path
import gradio as gr

import config
from transcriber import transcribe_audio_file
from medical_lexicon import extract_recognized_medical_terms

# ─── AUTO-PATCH GRADIO PREVIEW BANNER (Render & Cloud Support) ───────────────
try:
    import re
    _gradio_dir = Path(gr.__file__).parent / "templates" / "frontend"
    _img_url = "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&auto=format&fit=crop&q=80"
    for _tpl in ["index.html", "share.html"]:
        _tpl_path = _gradio_dir / _tpl
        if _tpl_path.exists():
            _c = _tpl_path.read_text(encoding="utf-8")
            # Replace Gradio 6 Groot header image
            _c = _c.replace(
                "https://raw.githubusercontent.com/gradio-app/gradio/main/js/_website/src/lib/assets/img/header-image.jpg",
                _img_url
            )
            # Replace legacy meta-image.png
            _c = _c.replace(
                "https://gradio.app/assets/img/meta-image.png",
                _img_url
            )
            # Comprehensive regex replacement for any default header image
            _c = re.sub(r"https://raw\.githubusercontent\.com/gradio-app/gradio/[^\"'>\s]+header-image\.jpg", _img_url, _c)
            _c = re.sub(r"https://gradio\.app/assets/img/[^\"'>\s]+", _img_url, _c)
            # Replace default descriptions and titles
            _c = _c.replace("Click to try out the app!", "Səs yazısının rəsmi tibbi mətnə çevrilməsi")
            _c = _c.replace('<meta property="og:title" content="Gradio" />', '<meta property="og:title" content="Tibbi Səs-Mətn" />')
            _c = _c.replace('<meta name="twitter:title" content="Gradio" />', '<meta name="twitter:title" content="Tibbi Səs-Mətn" />')
            _c = _c.replace('<title>Gradio</title>', '<title>Tibbi Səs-Mətn</title>')
            _tpl_path.write_text(_c, encoding="utf-8")
except Exception as _e:
    print(f"[Preview Patch] Note: {_e}", flush=True)

SAMPLE_AUDIO_PATH = str(config.SAMPLES_DIR / "konsilium_numune.mp3")


LATEST_RESULT = {
    "text": "",
    "file": None,
    "terms": "",
}


def process_audio(audio_path: str, model_choice: str = "gemma"):
    """Processes audio 100% locally via Whisper + Ollama (Gemma 4 / Qwen 2.5)."""
    if not audio_path:
        return "⚠️ Zəhmət olmasa səs faylı yükləyin və ya mikrofondan danışın.", None, ""

    if not os.path.exists(audio_path):
        return f"❌ Audio faylı tapılmadı: {audio_path}", None, ""

    try:
        final_text, stage1_text, output_file_path, detected_terms, stage_info = transcribe_audio_file(
            audio_path=audio_path,
            model_name="small",
            llm_mode=model_choice
        )
    except Exception as exc:
        return f"❌ Xəta baş verdi:\n{str(exc)}", None, ""

    # Detected terms
    if detected_terms:
        terms_md = "<div class='terms-container'>"
        terms_md += (
            "<div class='terms-header'>"
            "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#38bdf8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M22 12h-4l-3 9L9 3l-3 9H2'/></svg>"
            "<span>AŞKARLANAN TİBBİ TERMİNLƏR</span>"
            "</div>"
        )
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

    LATEST_RESULT["text"] = final_text
    LATEST_RESULT["file"] = output_file_path
    LATEST_RESULT["terms"] = terms_md

    return final_text, output_file_path, terms_md


def restore_last_result():
    """Restores the most recent transcription result if phone was locked or disconnected."""
    if LATEST_RESULT["text"]:
        return LATEST_RESULT["text"], LATEST_RESULT["file"], LATEST_RESULT["terms"]

    out_files = sorted(config.OUTPUT_DIR.glob("tibbi_qeyd_*.txt"), key=os.path.getmtime, reverse=True)
    if out_files:
        latest_file = str(out_files[0])
        try:
            content = Path(latest_file).read_text(encoding="utf-8")
            text_part = content
            if "TRANSKRİPSİYA MƏTNİ:" in content:
                text_part = content.split("TRANSKRİPSİYA MƏTNİ:")[1].split("=====================================================")[0].strip()
            restored_html = (
                "<div class='terms-container'>"
                "<div class='terms-header' style='color: #10b981;'>"
                "<svg width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='#10b981' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><polyline points='20 6 9 17 4 12'></polyline></svg>"
                "<span>NƏTİCƏ SERVERDƏN UĞURLA BƏRPA EDİLDİ</span>"
                "</div></div>"
            )
            return text_part, latest_file, restored_html
        except Exception:
            pass
    return "⚠️ Hələ heç bir nəticə qeydə alınmayıb.", None, ""


CUSTOM_CSS = """
/* ─── Typography Import (Plus Jakarta Sans, Outfit, JetBrains Mono) ────────── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ─── Global & Mobile Stabilization ─────────────────────────────────────────── */
html, body {
    overflow-x: hidden !important;
    width: 100% !important;
    max-width: 100vw !important;
    margin: 0 !important;
    padding: 0 !important;
    touch-action: pan-y !important;
    -webkit-overflow-scrolling: touch;
    background: #080c16 !important;
    color: #f1f5f9 !important;
}

*, *::before, *::after {
    box-sizing: border-box !important;
}

.gradio-container {
    max-width: 1040px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 24px 16px !important;
    overflow-x: clip !important;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    background: #080c16 !important;
    background-image: 
        radial-gradient(ellipse at 50% -10%, rgba(2, 132, 199, 0.16) 0%, transparent 60%),
        radial-gradient(circle at 5% 30%, rgba(16, 185, 129, 0.08) 0%, transparent 45%),
        radial-gradient(circle at 95% 75%, rgba(99, 102, 241, 0.09) 0%, transparent 50%) !important;
    background-attachment: fixed !important;
}

/* ─── Glassmorphism Panels & Containers ──────────────────────────────────── */
.gradio-container .block,
.gradio-container .panel,
.gradio-container fieldset,
div[data-testid="column"] > div:has(> .block) {
    background: rgba(15, 23, 42, 0.65) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(148, 163, 184, 0.14) !important;
    border-radius: 18px !important;
    box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.4) !important;
}

/* ─── Minimal Luxury Header ─────────────────────────────────────────────── */
.luxury-hero {
    text-align: center;
    padding: 18px 16px;
    margin-bottom: 20px;
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.8) 0%, rgba(15, 23, 42, 0.45) 100%) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(56, 189, 248, 0.18) !important;
    border-radius: 18px !important;
    box-shadow: 0 8px 25px -5px rgba(0, 0, 0, 0.4) !important;
}

.hero-brand {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}

.brand-icon-box {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    min-width: 40px;
    border-radius: 12px;
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.22) 0%, rgba(16, 185, 129, 0.18) 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38bdf8;
}

.hero-title {
    font-family: 'Outfit', sans-serif !important;
    font-size: 24px !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #ffffff 40%, #e2e8f0 70%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 !important;
    letter-spacing: -0.02em !important;
}

.pulse-emerald {
    display: inline-block;
    width: 8px;
    height: 8px;
    min-width: 8px;
    background: #10b981;
    border-radius: 50%;
    box-shadow: 0 0 10px #10b981;
    animation: pulse-emerald-ring 2.2s infinite ease-out;
}

@keyframes pulse-emerald-ring {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.8); }
    70% { box-shadow: 0 0 0 9px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* ─── Radio Selector Cards (Gemma 4 Modes) ────────────────────────────────── */
div[data-testid="radio-group"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 10px !important;
    margin-top: 8px !important;
}

div[data-testid="radio-group"] label {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    padding: 14px 18px !important;
    background: rgba(30, 41, 59, 0.45) !important;
    border: 1.5px solid rgba(148, 163, 184, 0.16) !important;
    border-radius: 14px !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    color: #f1f5f9 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

div[data-testid="radio-group"] label:hover {
    background: rgba(30, 41, 59, 0.8) !important;
    border-color: rgba(56, 189, 248, 0.45) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(2, 132, 199, 0.18) !important;
}

div[data-testid="radio-group"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.2) 0%, rgba(16, 185, 129, 0.1) 100%) !important;
    border-color: #0284c7 !important;
    color: #ffffff !important;
    box-shadow: 0 0 24px rgba(2, 132, 199, 0.25), inset 0 0 12px rgba(2, 132, 199, 0.12) !important;
}

div[data-testid="radio-group"] input[type="radio"] {
    accent-color: #0284c7 !important;
    width: 17px !important;
    height: 17px !important;
}

/* ─── Premium Action Buttons ──────────────────────────────────────────────── */
.premium-btn {
    background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 45%, #059669 100%) !important;
    background-size: 200% 200% !important;
    color: #ffffff !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 16.5px !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 16px 22px !important;
    box-shadow: 0 8px 24px -4px rgba(2, 132, 199, 0.45) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
}

.premium-btn:hover {
    background-position: right center !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 30px -4px rgba(16, 185, 129, 0.5) !important;
}

.secondary-btn {
    background: rgba(30, 41, 59, 0.6) !important;
    backdrop-filter: blur(10px) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(148, 163, 184, 0.22) !important;
    border-radius: 14px !important;
    padding: 15px 18px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14.5px !important;
    transition: all 0.25s ease !important;
    cursor: pointer !important;
}

.secondary-btn:hover {
    background: rgba(51, 65, 85, 0.8) !important;
    color: #ffffff !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* ─── Mobile Screen WakeLock Status ────────────────────────────────────────── */
.wakelock-banner {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(16, 185, 129, 0.08) !important;
    border: 1px solid rgba(16, 185, 129, 0.22) !important;
    border-radius: 9999px !important;
    margin-top: 14px !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
    line-height: 1.4 !important;
}

/* ─── Textarea & Result Output ────────────────────────────────────────────── */
textarea {
    background: rgba(11, 17, 32, 0.85) !important;
    border: 1px solid rgba(148, 163, 184, 0.18) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 15px !important;
    line-height: 1.75 !important;
    padding: 16px !important;
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.25) !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

textarea:focus {
    border-color: #0284c7 !important;
    box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.25), inset 0 2px 8px rgba(0, 0, 0, 0.25) !important;
}

.label-text, span[data-testid="block-label"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    color: #e2e8f0 !important;
}

/* ─── Term Chips Grid ─────────────────────────────────────────────────────── */
.terms-container {
    margin-top: 18px;
    padding: 18px 20px;
    background: rgba(15, 23, 42, 0.75) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(56, 189, 248, 0.22) !important;
    border-radius: 16px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.terms-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: 'Outfit', sans-serif;
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #38bdf8;
    margin-bottom: 14px;
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
    gap: 8px;
    padding: 6px 14px;
    background: rgba(30, 41, 59, 0.65);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 9999px;
    font-size: 12.5px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.term-chip:hover {
    border-color: #38bdf8;
    background: rgba(30, 41, 59, 0.9);
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(56, 189, 248, 0.25);
}

.term-domain {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    font-weight: 700;
    color: #38bdf8;
    background: rgba(2, 132, 199, 0.2);
    padding: 2px 7px;
    border-radius: 6px;
    letter-spacing: 0.04em;
}

.term-val {
    font-weight: 600;
    color: #f1f5f9;
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

@media (max-width: 768px) {
    .gradio-container {
        padding: 10px !important;
    }
    .luxury-hero {
        padding: 14px 12px !important;
    }
    .hero-title {
        font-size: 20px !important;
    }
}
"""

app_theme = gr.themes.Soft(
    primary_hue="sky",
    secondary_hue="emerald",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Plus Jakarta Sans"), gr.themes.GoogleFont("Outfit"), "system-ui", "sans-serif"],
    font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "monospace"]
).set(
    body_background_fill="#080c16",
    body_background_fill_dark="#080c16",
    body_text_color="#f1f5f9",
    body_text_color_dark="#f1f5f9",
    block_background_fill="rgba(15, 23, 42, 0.7)",
    block_background_fill_dark="rgba(15, 23, 42, 0.7)",
    block_border_color="rgba(148, 163, 184, 0.15)",
    block_border_color_dark="rgba(148, 163, 184, 0.15)",
    block_radius="16px",
    input_background_fill="rgba(11, 17, 32, 0.85)",
    input_background_fill_dark="rgba(11, 17, 32, 0.85)",
    input_border_color="rgba(148, 163, 184, 0.2)",
    input_border_color_dark="rgba(148, 163, 184, 0.2)",
    button_primary_background_fill="linear-gradient(135deg, #0284c7 0%, #0ea5e9 50%, #10b981 100%)",
    button_primary_background_fill_dark="linear-gradient(135deg, #0284c7 0%, #0ea5e9 50%, #10b981 100%)",
    button_primary_text_color="#ffffff",
    button_primary_text_color_dark="#ffffff",
    button_secondary_background_fill="rgba(30, 41, 59, 0.7)",
    button_secondary_background_fill_dark="rgba(30, 41, 59, 0.7)",
    button_secondary_text_color="#f1f5f9",
    button_secondary_text_color_dark="#f1f5f9",
    button_secondary_border_color="rgba(148, 163, 184, 0.2)",
    button_secondary_border_color_dark="rgba(148, 163, 184, 0.2)",
)

with gr.Blocks(title="Tibbi Səs-Mətn") as demo:
    gr.HTML("""
    <div class="luxury-hero">
        <div class="hero-brand">
            <div class="brand-icon-box">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"/>
                    <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"/>
                    <circle cx="20" cy="10" r="2"/>
                </svg>
            </div>
            <h1 class="hero-title">Tibbi Səs-Mətn</h1>
        </div>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="Səs Yazısı",
                editable=False,
            )

            with gr.Row():
                sample_btn = gr.Button("🎧 Nümunə Səs", variant="secondary", size="sm")

            model_selector = gr.Radio(
                choices=[
                    ("🩺 Tibbi Protokol & Epikriz", "gemma"),
                    ("🗣️ Sərbəst Danışıq", "gemma_general"),
                ],
                value="gemma",
                label="Redaktə Rejimi",
            )

            with gr.Row():
                transcribe_btn = gr.Button(
                    "🚀 Mətnə Çevir",
                    variant="primary",
                    size="lg",
                    scale=3,
                    elem_classes=["premium-btn"]
                )
                restore_btn = gr.Button(
                    "🔄 Bərpa Et",
                    variant="secondary",
                    size="lg",
                    scale=2,
                    elem_classes=["secondary-btn"]
                )

            gr.HTML("""
            <div class="wakelock-banner">
                <span class="pulse-emerald"></span>
                <span>Mobil ekran qoruyucusu aktivdir</span>
            </div>
            """)

        with gr.Column(scale=1):
            text_output = gr.Textbox(
                label="Mətn",
                placeholder="Mətn burada görünəcək...",
                lines=12,
                buttons=["copy"],
            )

            file_output = gr.File(
                label="Faylı Endir (.txt)",
                file_types=[".txt"],
            )

            terms_display = gr.HTML(value="")

    # Event handlers
    sample_btn.click(
        fn=lambda: SAMPLE_AUDIO_PATH if os.path.exists(SAMPLE_AUDIO_PATH) else None,
        inputs=[],
        outputs=[audio_input]
    )

    transcribe_btn.click(
        fn=process_audio,
        inputs=[audio_input, model_selector],
        outputs=[text_output, file_output, terms_display]
    )

    restore_btn.click(
        fn=restore_last_result,
        inputs=[],
        outputs=[text_output, file_output, terms_display]
    )

HEAD_TAGS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<meta property="og:title" content="Tibbi Səs-Mətn" />
<meta property="og:description" content="Səs yazısının rəsmi tibbi mətnə çevrilməsi" />
<meta property="og:image" content="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&auto=format&fit=crop&q=80" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Tibbi Səs-Mətn" />
<meta name="twitter:description" content="Səs yazısının rəsmi tibbi mətnə çevrilməsi" />
<meta name="twitter:image" content="https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1200&auto=format&fit=crop&q=80" />
<script>
// ─── Mobile Screen WakeLock & Background Resilience ─────────────────────────
let wakeLock = null;
let keepAliveAudio = null;

function getSilentAudio() {
    if (!keepAliveAudio) {
        keepAliveAudio = new Audio("data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA");
        keepAliveAudio.loop = true;
        keepAliveAudio.volume = 0.01;
    }
    return keepAliveAudio;
}

async function requestScreenLock() {
    try {
        if ('wakeLock' in navigator && !wakeLock) {
            wakeLock = await navigator.wakeLock.request('screen');
            console.log('[Mobile] Screen WakeLock ugurla aktiv edildi.');
            wakeLock.addEventListener('release', () => {
                console.log('[Mobile] Screen WakeLock dayandirildi.');
                wakeLock = null;
            });
        }
    } catch (err) {
        console.warn('[Mobile] WakeLock qeyri-aktiv:', err);
    }
    try {
        const audio = getSilentAudio();
        audio.play().then(() => {
            console.log('[Mobile] Fon aktivliyi ucun sessiz audio ise salindi.');
        }).catch(e => console.log('[Mobile] Audio defer:', e));
    } catch (e) {
        console.warn(e);
    }
}

function releaseScreenLock() {
    if (wakeLock) {
        try { wakeLock.release(); } catch(e) {}
        wakeLock = null;
    }
    if (keepAliveAudio) {
        try { keepAliveAudio.pause(); } catch(e) {}
    }
    console.log('[Mobile] WakeLock azad edildi.');
}

document.addEventListener('DOMContentLoaded', () => {
    function attachListeners() {
        const buttons = document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText && (btn.innerText.includes('Mətnə Çevir') || btn.innerText.includes('Transkripsiya') || btn.innerText.includes('Transcribe'))) {
                if (!btn.dataset.wakelockAttached) {
                    btn.dataset.wakelockAttached = 'true';
                    btn.addEventListener('click', () => {
                        requestScreenLock();
                        setTimeout(releaseScreenLock, 600000);
                    });
                }
            }
        });
    }

    attachListeners();
    setInterval(attachListeners, 2000);

    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            console.log('[Mobile] Ekran aktivlesdi.');
            const loadingIndicator = document.querySelector('.loading, .progress-bar, [aria-busy="true"]');
            if (loadingIndicator) {
                requestScreenLock();
            }
        }
    });
});
</script>
"""

if __name__ == "__main__":
    is_hf = os.environ.get("SPACE_ID") is not None
    is_cloud = is_hf or os.environ.get("RENDER") is not None
    port = int(os.environ.get("PORT", 7860))
    demo.queue(default_concurrency_limit=3)
    _, local_url, share_url = demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=not is_cloud,
        theme=app_theme,
        css=CUSTOM_CSS,
        head=HEAD_TAGS,
        inbrowser=False
    )
    print(f"LOCAL_URL: {local_url}", flush=True)
    if share_url:
        print(f"SHARE_URL: {share_url}", flush=True)
