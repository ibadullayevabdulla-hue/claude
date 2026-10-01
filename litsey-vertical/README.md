# Jaloliddin Manguberdi harbiy-akademik litseyi — vertikal video (9:16)

Bu Reels / Shorts / TikTok uchun 2:00 davomiylikdagi dinamik motion-video: 1080×1920, 30 fps. Musiqa va ovoz effektlari originaldir.

Videoda foydalanuvchining faqat bitta rasmi — **logotip** — ishlatilgan. Infografikalardagi suratlar o‘rniga har bir band uchun **ikonka** qo‘yilgan. Ikonkalar oltin chiziq bilan „chizilib“ chiqadi.

**Video:** [`out/litsey-vertical.mp4`](out/litsey-vertical.mp4)

## Tuzilishi

Temp 100 BPM, ya'ni bir takt = 2,4 soniya. Jami 50 takt = 2:00.

| Vaqt | Sahna |
|---|---|
| 0:00 | Bayroq hilpiraydi, oltin sakkiz qirrali yulduz chizilib chiqadi |
| 0:02 | Logotip zarba bilan tushadi. Tepasida „JALOLIDDIN MANGUBERDI NOMIDAGI / HARBIY-AKADEMIK LITSEYI“ yozuvi. So‘ng logotip yuqoridagi sarlavhaga uchib o‘tadi |
| 0:10 | „QABUL JARAYONI · 8 BOSQICH“ |
| 0:14 | 8 bosqich, har biri 4,8 soniya |
| 0:53 | Yakuniy test: Matematika 93 + Fizika 63 → **60 ta savol — 156 ball** |
| 1:00 | „O‘QUVCHILARGA BERILADIGAN IMTIYOZLAR · 9 IMTIYOZ“ |
| 1:05 | 9 imtiyoz, har biri 4,8 soniya |
| 1:48 | Final: logotip qaytadi, so‘ng „MAQSAD, / HARAKAT – / NATIJA“ (har bir so‘z zarb bilan) |

**Har bir band sahnasida:**
- O‘rtada katta oltin sakkiz qirrali yulduz bor. U har sahna almashganda 45° buriladi va uchlaridan uchqunlar sachraydi.
- Yulduz ichida ikonka chizilib chiqadi.
- Burchakdagi oltin yulduzda band raqami bor.
- Pastda sarlavha, matn va kichik ikonkali yorliqlar chiqadi.
- Eng pastda bosqichlar chizig‘i bor.

**Maxsus sahnalar:**
- To‘garaklar sahnasida 3 ta ikonka navbat bilan almashadi.
- 30% va 15% raqamlari yulduz ichida sanab chiqadi.

**Faqat O‘zbekistonga tegishli elementlar ishlatilgan:**
- bayroq (oy va 12 yulduz bilan, kodda chizilgan);
- oltin sakkiz qirrali yulduzlar;
- girih naqshli fon;
- to‘q yashil va oltin ranglar.

**Musiqa:** epik, o‘zbekona ruhda. Unda quyidagilar bor:
- doira ritmlari (dum, tak va zang ovozi);
- karnayga o‘xshash past mis ovozi;
- surnayga o‘xshash kuy;
- epik barabanlar, torli cholg‘ular, mis karnaylar va xor.

Musiqa re minorda (hijoz ohangi bilan) boshlanadi, imtiyozlar qismida bir pog‘ona ko‘tariladi va Mi majorda tugaydi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `src/logo.png` | Foydalanuvchi bergan logotip (`logo.webp` — video uchun nusxa) |
| `fetch_icons.py` | [Tabler Icons](https://tabler.io/icons) (MIT) ikonkalarini yuklab, `icons.json` ga yozadi |
| `index.html` | Animatsiyaning o‘zi (deterministik, `window.__seek(t)`), matnlar `SCENES` ichida |
| `soundtrack.py` | Musiqa va effektlarni sintez qiladi |
| `render.cjs` | Kadrlarni Playwright bilan render qiladi, keyin MP4 va ovozni birlashtiradi |

## Qayta yaratish

```bash
pip install numpy scipy pillow
python3 fetch_icons.py
NODE_PATH=$(npm root -g) node render.cjs                  # out/litsey-vertical.mp4
NODE_PATH=$(npm root -g) node render.cjs --stills=16,90   # tekshirish uchun kadrlar
```

## Kreditlar

- **Ikonkalar:** Tabler Icons (MIT).
- **Shriftlar:** Saira Condensed, Saira Stencil One, Manrope (SIL Open Font License).
