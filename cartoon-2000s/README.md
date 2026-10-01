# 46 Cartoon Icons by Year (2000–2023) — motion video

Bu YouTube uchun 1:56 davomiylikdagi motion-video (1920×1080, 30 fps). Unda 46 ta multfilm qahramoni paydo boʻlgan yili boʻyicha koʻrsatiladi. Musiqa va ovoz effektlari originaldir. Video birinchi [`cartoon-timeline`](../cartoon-timeline) videosi bilan bir xil uslubda («Style A», qarang: [`CLAUDE.md`](../CLAUDE.md)).

- **Video:** [`out/cartoon-icons-2000s.mp4`](out/cartoon-icons-2000s.mp4)
- **Thumbnail:** [`out/thumbnail.jpg`](out/thumbnail.jpg)
- **YouTube uchun matnlar** (sarlavha, tavsif, teglar, boblar): [`YOUTUBE.md`](YOUTUBE.md)

## Tuzilishi

Temp 112 BPM. Har bir qahramonga bitta takt ajratilgan (~2.1 s), shuning uchun hamma narsa ritmga tushadi.

| Vaqt | Qism |
|---|---|
| 0:00 | Intro: „How old is your favorite cartoon?“ savoli va stikerlar kollaji |
| 0:04 | **2000s** (12 qahramon): „Ogres, monsters & cars“ |
| 0:32 | **2010s** (26 qahramon): „Dragons, heroes & snow“ |
| 1:30 | **2020s** (8 qahramon): „The new generation“ |
| 1:49 | Outro: 46 ta rasm setkasi, „Which one was your childhood?“ va Subscribe tugmasi |

Har bir qahramon kartasida quyidagilar bor:
- rasm (stiker yoki ramkadagi rasm);
- ismi;
- yil hisoblagichi (odometr);
- yoshi (2026 yilga nisbatan);
- debyuti;
- pastda 2000–2025 timeline.

Musiqa oʻn yilliklar bilan birga oʻzgaradi:
- **2000s:** pop-punk (distorted power chord, toʻgʻri 8-lik ritm);
- **2010s:** tropical house, oʻrtasidan big-room EDM'ga oʻtadi;
- **2020s:** future bass (half-time, 808, „chop“ qilingan akkordlar), tonallik bir pogʻona koʻtariladi.

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `characters.json` | 46 ta qahramon: ism, yil, debyut, rasm manbasi (`src`) |
| `fetch_images.py` | Rasmlarni Fandom wiki'lardan yuklaydi (`img/`). Oq fonli rasmlarning (`knockout`) fonini olib tashlaydi |
| `find_image.py` | Fandom wiki'da yaxshiroq rasm qidirish uchun yordamchi skript |
| `prepare_images.py` | Rasmlarni 1000 px ga keltiradi va shaffof rasmlarga oq stiker kontur + soya qoʻshadi (`img/hd/`) |
| `index.html` | Animatsiyaning oʻzi (deterministik, `window.__seek(t)`) |
| `soundtrack.py` | Musiqa va effektlarni sintez qiladi (`out/soundtrack.wav`) |
| `render.cjs` | Kadrlarni Playwright bilan parallel render qiladi (JPEG kadrlar), keyin MP4 va ovozni birlashtiradi |
| `thumb.html` | YouTube thumbnail |

## Qayta yaratish

```bash
pip install numpy scipy pillow
python3 fetch_images.py          # rasmlar (bitta qahramon: python3 fetch_images.py elsa)
python3 prepare_images.py
NODE_PATH=$(npm root -g) node render.cjs            # out/cartoon-icons-2000s.mp4 (ovoz bilan)
NODE_PATH=$(npm root -g) node render.cjs --mux      # faqat ovozni qayta yaratish
NODE_PATH=$(npm root -g) node render.cjs --thumb    # out/thumbnail.jpg
NODE_PATH=$(npm root -g) node render.cjs --stills=5,40   # tekshirish uchun alohida kadrlar
```

Chatga yuborish uchun (30 MB chegarasi) HEVC nusxasi:

```bash
ffmpeg -i out/cartoon-icons-2000s.mp4 -c:v libx265 -b:v 1800k -x265-params pass=1 -tag:v hvc1 -an -f mp4 /dev/null
ffmpeg -i out/cartoon-icons-2000s.mp4 -c:v libx265 -b:v 1800k -x265-params pass=2 -tag:v hvc1 -c:a aac -b:a 160k -movflags +faststart ../deliver/Cartoon-Icons-2000-2023-1080p.mp4
```

## Mualliflik huquqi haqida

- **Musiqa va effektlar** toʻliq original, kod bilan yaratilgan. Shuning uchun Content ID daʼvosi boʻlmaydi.
- **Qahramon rasmlari** Fandom wiki'lardan (Disney, Pixar, DreamWorks, Shrek, Despicable Me, Adventure Time, Miraculous, Bluey, Peppa Pig, Ben 10, Dora, Spider-Man Films, Hotel Transylvania) olingan. Ular studiyalarga tegishli. Bunday „timeline“ videolar odatda fair use (taʼlimiy, oʻzgartirilgan) sifatida chiqadi, lekin huquq egasi daʼvo qilishi mumkin — buning kafolati yoʻq.

## Kreditlar

- **Shrift:** [Fredoka](https://fonts.google.com/specimen/Fredoka) (SIL Open Font License).
- **Emoji (🔔 👇):** [Microsoft Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (MIT).
