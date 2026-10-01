# Claude Code — 30 soniyalik motion

Claude Code haqida 30 soniyalik dinamik motion-grafika (1920×1080, 30 fps), musiqa va ovoz effektlari bilan.

**Tayyor video:** [`out/claude-code-uz.mp4`](out/claude-code-uz.mp4)

## Sahnalar

| Vaqt | Sahna |
|---|---|
| 0–4 s | Intro: uchqun (spark) logotip va "Claude Code" sarlavhasi |
| 4–17 s | Terminal demo: `claude` → prompt → Read / Search / Update (diff) → `npm test` → `git commit`, chap tomonda "Qanday ishlaydi" bosqichlari |
| 17–22 s | Kinetik tipografiya: Oʻqiydi. Yozadi. Tuzatadi. Sinaydi. Yetkazadi. |
| 22–26 s | "Siz ishlaydigan joyda": Terminal, VS Code, JetBrains, Desktop, Web, GitHub |
| 26–30 s | Outro: logotip, oʻrnatish buyrugʻi, claude.ai/code |

## Brauzerda koʻrish

```bash
npx serve .            # yoki: python3 -m http.server
# http://localhost:3000/index.html          — oʻzbekcha
# http://localhost:3000/index.html?lang=en  — inglizcha
# http://localhost:3000/index.html?t=12.5   — bitta kadrni muzlatish
```

Boshqaruv: sahnaga bosish — ovoz bilan boshidan, `Space` — pauza, `←/→` — 2 soniya oldinga/orqaga.

## MP4 ga render qilish

Talab: Node 18+, `ffmpeg`.

```bash
npm install
node render.cjs                 # out/claude-code-uz.mp4
node render.cjs --lang=en       # out/claude-code-en.mp4
node render.cjs --fps=60        # silliqroq harakat
node render.cjs --stills=3,12.5 # faqat PNG kadrlar
```

Animatsiya toʻliq deterministik: har bir kadr `window.__seek(t)` orqali chiziladi, shuning uchun render natijasi har safar bir xil boʻladi.

## Ovoz

`soundtrack.py` musiqa va effektlarni kod orqali sintez qiladi (Python 3, `pip install numpy scipy`) va ularni animatsiya vaqtiga aniq bogʻlaydi:

- **Musiqa:** 126 BPM, Am–F–C–G. Intro — pad va riser; 3.7 s da zarb (toʻq sariq flash); terminal sahnasida yengil groove; 15–17 s da build-up; 17.0 s da drop (soʻzlar sahnasi); 26.5 s da yakuniy akkord.
- **Effektlar:** klaviatura bosishlari (`claude`, prompt, oʻrnatish buyrugʻi), Enter, tool-call signallari, diff qatorlari, test hisoblagichi, „test oʻtdi“ chime, chip pop, har bir soʻz oʻtishidagi whoosh va zarb, kartochkalar pop.

`node render.cjs` videoni ovoz bilan birga chiqaradi. Faqat ovozni qayta yaratish uchun: `node render.cjs --mux`.
