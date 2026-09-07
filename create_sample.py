"""Generates a synthetic Azerbaijani hospital consilium audio sample.

Strictly synthetic medical scenario complying with patient privacy rules.
"""

from pathlib import Path
from gtts import gTTS
import config

SAMPLE_TEXT = (
    "Hospitalın tibbi konsilium protokolu. Xəstənin şikayətləri kəskin qarın ağrısı və təngnəfəslikdir. "
    "Laborator müayinələrdə leykositoz və trombositopeniya aşkar edilmişdir. "
    "Kompüter tomoqrafiyası və MRT nəticələrinə əsasən kəskin xolesistit müəyyən olundu. "
    "Kardioloqun rəyinə görə miokard infarktı riski yoxdur, arterial hipertenziya nəzarət altındadır. "
    "Cərrahiyyə komissiyası laparoskopik xolesistektomiya əməliyyatına qərar verdi. "
    "Preoperativ antibiotikoterapiya təyin olunur."
)

def generate_sample_audio():
    sample_file = config.SAMPLES_DIR / "konsilium_numune.mp3"
    print(f"Generating synthetic audio to {sample_file}...")
    tts = gTTS(text=SAMPLE_TEXT, lang="tr")  # Using high-clarity Turkic voice model for clear pronunciation
    tts.save(str(sample_file))
    print(f"Sample generated successfully at: {sample_file}")

if __name__ == "__main__":
    generate_sample_audio()
