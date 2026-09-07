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
            return text_part, latest_file, "<div class='terms-container'><div class='terms-header'>✅ Serverdən Bərpa Edildi</div></div>"
        except Exception:
            pass
    return "⚠️ Hələ heç bir nəticə qeydə alınmayıb.", None, ""


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

.secondary-btn {
    background: #f1f5f9 !important;
    color: #334155 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    margin-top: 10px !important;
    transition: all 0.2s ease !important;
}
.dark .secondary-btn {
    background: #1e293b !important;
    color: #f1f5f9 !important;
    border-color: #334155 !important;
}
.secondary-btn:hover {
    background: #e2e8f0 !important;
}
.dark .secondary-btn:hover {
    background: #334155 !important;
}

.wakelock-banner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.25);
    border-radius: 10px;
    margin-top: 10px;
    font-size: 12px;
    color: var(--body-text-color-subdued, #64748b);
    line-height: 1.4;
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
            <span class="status-pill-text" style="color: #f8fafc !important; font-weight: 600;">🟢 100% Yerli & Oflayn AI Aktivdir</span>
        </div>
        <h1 class="header-title">🩺 Tibbi Səs-Mətn</h1>
        <p class="header-desc">Səs yazısının yerli kompüterdə tam məxfi rəsmi tibbi mətnə çevrilməsi</p>
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

            model_selector = gr.Radio(
                choices=[
                    ("🩺 Gemma 4 (12B) — Rəsmi Tibbi Protokol & Epikriz", "gemma"),
                    ("🗣️ Gemma 4 (12B) — Sərbəst Danışıq & Nitq", "gemma_general"),
                    ("⚡ Qwen 2.5 (3B) — Ultra Sürətli", "qwen"),
                    ("🎙️ Yalnız Whisper — LLM-siz Xam Mətn", "none"),
                ],
                value="gemma",
                label="🤖 Süni Zəka Redaktə Rejimi",
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
                    "🔄 Son Nəticəni Bərpa Et",
                    variant="secondary",
                    size="lg",
                    scale=2,
                    elem_classes=["secondary-btn"]
                )

            gr.HTML("""
            <div class="wakelock-banner">
                <span style="font-size: 16px;">📱</span>
                <span><b>Mobil Ekran Qoruyucusu Aktivdir:</b> Səs emalı zamanı telefon ekranının sönməsinin və əlaqənin kəsilməsinin qarşısı avtomatik alınır. Ekran sönsə belə, "Son Nəticəni Bərpa Et" düyməsi ilə tamamlanmış mətni dərhal geri qaytara bilərsiniz.</span>
            </div>
            """)

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
            if (btn.innerText && (btn.innerText.includes('Mətnə Çevir') || btn.innerText.includes('Transcribe'))) {
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
