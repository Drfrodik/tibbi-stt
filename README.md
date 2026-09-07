---
title: Tibbi Səs-Mətn
emoji: 🩺
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.26.0
app_file: app.py
pinned: false
---

# 🩺 Tibbi Səs-Mətn Sistemi (Gemini 3.6 Flash)

Səs yazılarının yüksək dəqiqliklə rəsmi tibbi mətnə çevrilməsi üçün hazırlanmış sistem.

---

## 🌟 Əsas Üstünlükləri

1. **🔒 100% Offline Məxfilik (Zero-Cloud):**
   - Heç bir səs və ya mətn xəstəxana binasından və ya kompüterdən kənara çıxmır.
   - İnternet bağlantısı olmadan (Wi-Fi sönülü və ya şəbəkə kabeli çıxarılmış halda) tam funksional işləyir.

2. **🩺 Çoxsahəli Tibbi Terminologiya:**
   - Konsiliumda iştirak edən bütün ixtisaslar üzrə terminləri dəqiq tanıyır:
     - **Cərrahiyyə:** *laparoskopiya, xolesistektomiya, rezeksiya, preoperativ, postoperativ...*
     - **Kardiologiya:** *miokard infarktı, arterial hipertenziya, taxikardiya, kardiomiopatiya...*
     - **Onkologiya & Hematologiya:** *trombositopeniya, leykositoz, adenokarsinoma, metastaz...*
     - **Qastroenterologiya:** *kəskin xolesistit, pankreatit, sirroz...*
     - **Radiologiya:** *kompüter tomoqrafiyası (KT), maqnit-rezonans tomoqrafiya (MRT), USM...*
     - **Farmakologiya:** *antibiotikoterapiya, infuzion terapiya, antikoaqulyant...*

3. **🎯 Sadə İstifadəçi Axını:**
   - Səs faylını yüklə (və ya mikrofondan danış).
   - "Mətnə Çevir" düyməsini bas.
   - Nəticəni ekranda gör və bir kliklə `.txt` faylı kimi yaddaşa saxla.

---

## 🚀 Tətbiqi İşə Salmaq

Masaüstündəki `BAŞLAT.bat` faylına iki dəfə klik edin və ya terminalda aşağıdakı əmri icra edin:

```bash
python app.py
```

Brauzerinizdə avtomatik olaraq bu ünvan açılacaq:
👉 **`http://127.0.0.1:7860`**

---

## 📁 Layihə Strukturu

- `app.py` — Sadə və müasir Gradio veb interfeysi.
- `transcriber.py` — 100% offline Whisper STT transkripsiya modulu.
- `medical_lexicon.py` — Çoxsahəli tibbi termin lüğəti və fonetik düzəliş mexanizmi.
- `config.py` — Yerli FFmpeg və model parametrləri.
- `samples/` — Sifarişçiyə dərhal nümayiş etdirmək üçün hazır sintetik konsilium audio nümunəsi.
- `outputs/` — Əldə edilən bütün konsilium protokolları (`.txt`).
- `BAŞLAT.bat` — Windows-da tək kliklə açılış skripti.
