# 50 Cartoon Icons by Year — 2 daqiqalik motion

YouTube uchun 2:02 davomiylikdagi dinamik motion-video (1920×1080, 30 fps): 50 ta multfilm qahramoni paydo boʻlgan yili boʻyicha, original musiqa va ovoz effektlari bilan.

- **Video:** [`out/cartoon-icons.mp4`](out/cartoon-icons.mp4)
- **Thumbnail:** [`out/thumbnail.jpg`](out/thumbnail.jpg)
- **Sarlavha, tavsif, teglar, boblar:** [`YOUTUBE.md`](YOUTUBE.md)

## Tuzilishi

126 BPM — har bir qahramonga bitta takt (~1.9 s), hamma narsa ritmga tushadi.

| Vaqt | Qism |
|---|---|
| 0:00 | Intro: „How old is your favorite cartoon?“ + stikerlar kollaji |
| 0:03 | Har bir oʻn yillik: oʻz rangi, sarlavha kartochkasi (slide whistle + zarb) |
| — | Har bir qahramon: rasm (stiker yoki ramka), ismi, yil hisoblagichi (odometr), yoshi, debyuti, pastda 1925–2000 timeline |
| 1:56 | Outro: 50 ta rasm setkasi, „Which one was your childhood?“, Subscribe tugmasi bosiladi |

Musiqa ham davrlar bilan oʻzgaradi: 1920–30-yillar — eski radio (ksilofon, tuba, plastinka shitirlashi), 40–50 — swing, 60 — rok, 70 — funk, 80 — synthwave, 90/2000 — dance (tonallik koʻtariladi).

## Fayllar

| Fayl | Vazifasi |
|---|---|
| `characters.json` | 50 ta qahramon: ism, yil, debyut, rasm fayllari |
| `fetch_images.py` | Rasmlarni Wikipedia'dan yuklaydi (`img/`) |
| `prepare_images.py` | Rasmlarni 1000 px ga keltiradi, shaffof rasmlarga oq stiker kontur + soya qoʻshadi (`img/hd/`) |
| `index.html` | Animatsiyaning oʻzi (deterministik, `window.__seek(t)`) |
| `soundtrack.py` | Musiqa + effektlarni sintez qiladi (`out/soundtrack.wav`) |
| `render.cjs` | Kadrlarni Playwright bilan 4 oqimda render qilib, MP4 + ovoz yigʻadi |
| `thumb.html` | YouTube thumbnail |

## Qayta yaratish

```bash
pip install numpy scipy pillow
npm install
python3 fetch_images.py        # rasmlar (bitta qahramon: python3 fetch_images.py goku)
python3 prepare_images.py
node render.cjs                # out/cartoon-icons.mp4 (ovoz bilan)
node render.cjs --mux          # faqat ovozni qayta yaratish
node render.cjs --thumb        # out/thumbnail.jpg
node render.cjs --stills=5,40  # tekshirish uchun alohida kadrlar
```

Brauzerda koʻrish: `npx serve .` → `http://localhost:3000/index.html` (sahnaga bosing — ovoz bilan boshlanadi; `?t=40` — kadrni muzlatish).

## Mualliflik huquqi haqida

- **Musiqa va effektlar** — toʻliq original, kod bilan yaratilgan: Content ID da'vosi boʻlmaydi.
- **Qahramon rasmlari** — Wikipedia'dan olingan; ularning aksariyati studiyalarga (Disney, Warner Bros., Nintendo, Toei va boshq.) tegishli. Bunday „timeline“ videolar odatda fair use (taʼlimiy, oʻzgartirilgan) sifatida chiqadi, lekin huquq egasi daʼvo qilishi mumkin — kafolat yoʻq.

## Kreditlar

- Shrift: [Fredoka](https://fonts.google.com/specimen/Fredoka) (SIL Open Font License)
- Emoji (🔔 👇): [Microsoft Fluent Emoji](https://github.com/microsoft/fluentui-emoji) (MIT)
