# Jaloliddin Manguberdi harbiy-akademik litseyi — motion video

Litsey uchun harbiy uslubdagi dinamik video: 1:32 davomiylik, 1920×1080, 30 fps. Musiqa va ovoz effektlari originaldir. Video uchta rasm asosida tayyorlangan:
- litsey logotipi;
- „Qabul jarayoni“ infografikasi (8 bosqich);
- „O‘quvchilarga beriladigan imtiyozlar“ infografikasi (9 band).

**Video:** [`out/litsey-video.mp4`](out/litsey-video.mp4)

## Tuzilishi

Temp 120 BPM, ya'ni bir takt = 2 soniya.

| Vaqt | Sahna |
|---|---|
| 0:00 | Logotip: baraban drobi → logotip zarba bilan chiqadi. Tepasida „JALOLIDDIN MANGUBERDI NOMIDAGI / HARBIY-AKADEMIK LITSEYI“ yozuvi, orqada hilpirayotgan O‘zbekiston bayrog‘i |
| 0:06 | „QABUL JARAYONI · 8 bosqich“ (haykal va bino arkasimon ramkada) |
| 0:10 | 8 bosqich, har biri 4 soniya |
| 0:42 | Yakuniy test ballari: Matematika 93 + Fizika 63 = **60 ta savol — 156 ball**. Raqamlar sanab chiqadi |
| 0:46 | „O‘QUVCHILARGA BERILADIGAN IMTIYOZLAR · 9 imtiyoz“ |
| 0:50 | 9 imtiyoz, har biri 4 soniya. +30% va +15% qalqon ichida sanab chiqadi |
| 1:26 | Final: logotip va „MAQSAD, HARAKAT – NATIJA“ (har bir so‘z zarb bilan chiqadi) |

Har bir bosqich yoki imtiyoz sahnasida quyidagilar bor:
- raqamli oltin sakkiz qirrali yulduz;
- sarlavha va matn (infografikadagi so‘zlar aynan saqlangan);
- infografikadan qirqib olingan rasm, oltin ramkada;
- pastda bosqichlar chizig‘i.

Rasm tomoni har sahnada almashib turadi: bir safar o‘ngda, keyingisida chapda.

**Faqat O‘zbekistonga tegishli elementlar ishlatilgan:**
- O‘zbekiston bayrog‘i: ko‘k, oq, yashil, qizil chiziqlar, oy va 12 yulduz;
- sakkiz qirrali yulduz (litsey muhridagi kabi);
- girih naqshli fon;
- arkasimon (peshtoq) ramkalar;
- oltin va to‘q ko‘k ranglar.

**Musiqa:** original harbiy marsh. Unda baraban kadensiyalari, katta baraban, litavralar, mis karnaylar fanfarasi, torli cholg‘ular va xor bor. Re minorda boshlanadi, imtiyozlar qismida bir pog‘ona ko‘tariladi va Mi majorda tugaydi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `src/` | Foydalanuvchi bergan 3 ta asl rasm |
| `crops.json` | Har bir sahna uchun infografikadan qirqiladigan joylar |
| `upscale.py` | Qirqib, EDSR super-resolution bilan 4× kattalashtiradi (`assets/`) |
| `index.html` | Animatsiyaning o‘zi (deterministik, `window.__seek(t)`) |
| `soundtrack.py` | Marsh va effektlarni sintez qiladi |
| `render.cjs` | Kadrlarni Playwright bilan render qiladi, keyin MP4 va ovozni birlashtiradi |

## Qayta yaratish

```bash
pip install numpy scipy pillow opencv-contrib-python-headless
python3 upscale.py
NODE_PATH=$(npm root -g) node render.cjs                 # out/litsey-video.mp4
NODE_PATH=$(npm root -g) node render.cjs --stills=8,50   # tekshirish uchun kadrlar
```
