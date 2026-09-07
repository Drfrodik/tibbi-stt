"""Tibbi Səs-Mətn Tətbiqi (Gemini 3.6 Flash).

Bu tətbiq yerli Whisper və ya Ollama modelləri TƏLƏB ETMİR:
- 100% Google Gemini 3.6 Flash ilə işləyir.
- İstənilən ən zəif kompüterdə (hətta 4GB RAM, RTX-siz, sadə prosessorlar) dərhal işə düşür.
- Səs faylı Google Cloud-a yüklənir, tibbi mətn çıxarılır və səs dərhal Google-dan silinir (0 retention).
"""

import os
import datetime
from pathlib import Path
import gradio as gr

import config
from gemini_corrector import gemini_transcribe_audio_direct, validate_gemini_key
from medical_lexicon import extract_recognized_medical_terms

SAMPLE_AUDIO_PATH = str(config.SAMPLES_DIR / "konsilium_numune.mp3")


def process_audio_gemini(audio_path: str, api_key: str = ""):
    """Transcribes audio directly via Gemini 3.6 Flash and deletes cloud file."""
    if not audio_path:
        return "⚠️ Zəhmət olmasa səs faylı yükləyin və ya mikrofondan danışın.", None, "", ""

    if not os.path.exists(audio_path):
        return f"❌ Audio faylı tapılmadı: {audio_path}", None, "", ""

    key_to_use = api_key.strip() if api_key else None
    result_text, err = gemini_transcribe_audio_direct(audio_path, api_key=key_to_use)

    if err:
        return f"❌ Gemini API Xətası:\n{err}", None, "", "❌ Xəta baş verdi"

    # Extract detected medical terms
    detected_terms = extract_recognized_medical_terms(result_text)
    if detected_terms:
        terms_md = "### 🩺 Mətndə Aşkarlanan Tibbi Terminlər:\n\n"
        terms_md += "| Tibbi Sahə | Tanınan Termin |\n| :--- | :--- |\n"
        for item in detected_terms:
            terms_md += f"| **{item['domain']}** | `{item['term']}` |\n"
    else:
        terms_md = "ℹ️ Spesifik tibbi termin qeydə alınmadı."

    # Write protocol file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"tibbi_qeyd_{timestamp}.txt"
    output_file_path = str(config.OUTPUT_DIR / output_filename)

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write("=====================================================\n")
        f.write("TİBBİ SƏS-MƏTN PROTOKOLU (GEMINI API)\n")
        f.write(f"Tarix / Saat: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write("Mühərrik: Google Gemini 3.6 Flash (Direct Audio / Efemer)\n")
        f.write("=====================================================\n\n")
        f.write("TRANSKRİPSİYA MƏTNİ:\n")
        f.write(result_text + "\n\n")
        if detected_terms:
            f.write("AŞKARLANAN TİBBİ TERMİNLƏR VƏ SAHƏLƏR:\n")
            for item in detected_terms:
                f.write(f" - [{item['domain']}] : {item['term']}\n")
        f.write("\n=====================================================\n")

    stage_info = "⚡ Gemini 3.6 Flash Direct Audio (Səs tanındı və dərhal buluddan silindi)"
    return result_text, output_file_path, terms_md, stage_info


def save_key(key: str):
    """Saves API key to .env."""
    key = key.strip()
    if not key:
        return "⚠️ Zəhmət olmasa API açarını daxil edin."
    if len(key) < 25 or key.endswith("..."):
        return "❌ Açar natamamdır. Google AI Studio-dan 39 simvollu açarı yapışdırın."
    env_path = config.BASE_DIR / ".env"
    try:
        with open(env_path, "w", encoding="utf-8") as f:
            f.write(f"GEMINI_API_KEY={key}\n")
        os.environ["GEMINI_API_KEY"] = key
        return "✅ API açarı uğurla yadda saxlanıldı!"
    except Exception as exc:
        return f"❌ Xəta: {str(exc)}"


CUSTOM_CSS = """
.gradio-container {
    max-width: 1000px !important;
    margin: 0 auto !important;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
}
.main-header {
    text-align: center;
    padding: 24px 12px;
    background: linear-gradient(135deg, #0284c7, #0f766e);
    color: white;
    border-radius: 12px;
    margin-bottom: 20px;
}
.main-header h1 { font-size: 26px; font-weight: 700; margin: 0 0 8px 0; }
.main-header p { font-size: 14px; opacity: 0.95; margin: 0; }
.action-btn { font-weight: 600 !important; font-size: 16px !important; }
.privacy-badge {
    background-color: #ecfdf5;
    border: 1px solid #6ee7b7;
    color: #065f46;
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 13px;
    margin-bottom: 16px;
}
"""

with gr.Blocks(title="Tibbi Səs-Mətn") as demo:
    gr.HTML("""
    <div class="main-header">
        <h1>⚡ Tibbi Səs-Mətn Sistemi</h1>
        <p>Səs yazısının dəqiq mətnə çevrilməsi (Gemini 3.6 Flash)</p>
    </div>
    <div class="privacy-badge">
        🔒 <b>0 Saxlanma Zəmanəti:</b> Səs yazısı dinlənilərək mətnə çevrilən kimi Google serverlərindən 
        avtomatik və dərhal birdəfəlik silinir.
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                sources=["upload", "microphone"],
                type="filepath",
                label="🎙️ Səs Yazısı (Mikrofon və ya Fayl)"
            )

            with gr.Row():
                sample_btn = gr.Button("🎧 Nümunə Səsi Yüklə", variant="secondary", size="sm")

            with gr.Accordion("🔑 Gemini API Açarınız", open=True):
                with gr.Row():
                    api_key_box = gr.Textbox(
                        label="Google Gemini API Açarı",
                        placeholder="AIzaSy... açarınızı daxil edin",
                        type="password",
                        scale=3
                    )
                    save_btn = gr.Button("💾 Yadda Saxla", variant="secondary", scale=1)
                key_status = gr.Markdown(value="")

            run_btn = gr.Button(
                "🚀 Səsi Mətnə Çevir",
                variant="primary",
                size="lg",
                elem_classes=["action-btn"]
            )

        with gr.Column(scale=1):
            text_out = gr.Textbox(
                label="📋 Düzəldilmiş Mətn",
                placeholder="Mətn burada görünəcək...",
                lines=8
            )
            pipeline_info = gr.Markdown(value="")
            file_out = gr.File(label="💾 Mətni Endir (.txt)", file_types=[".txt"])
            terms_out = gr.Markdown(label="Aşkarlanan Terminlər", value="")

    save_btn.click(fn=save_key, inputs=[api_key_box], outputs=[key_status])
    sample_btn.click(
        fn=lambda: SAMPLE_AUDIO_PATH if os.path.exists(SAMPLE_AUDIO_PATH) else None,
        inputs=[],
        outputs=[audio_input]
    )
    run_btn.click(
        fn=process_audio_gemini,
        inputs=[audio_input, api_key_box],
        outputs=[text_out, file_out, terms_out, pipeline_info]
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7861, css=CUSTOM_CSS, inbrowser=False)
