# 2027 — kelayotgan animatsion filmlar (motion video)

2027-yilda chiqadigan 57 ta animatsion filmning 3:58 lik dinamik videosi (38 tasi aniq sana bilan, 19 tasi „2027 · Date TBA“) (1920×1080, 30 fps), original musiqa va ovoz effektlari bilan.

- **Video:** `out/animated-2027.mp4`
- **Thumbnail:** `out/thumbnail.jpg`
- **Sarlavha, tavsif (sanalar ro'yxati bilan), teglar, boblar:** [`YOUTUBE.md`](YOUTUBE.md)

## Tuzilishi

120 BPM — har bir filmga 2 takt (4 s): intro 4 s + 57 × 4 s + outro 6 s = 238 s. Filmlar soni oʻzgarsa, davomiylik avtomatik moslashadi (`films.json`).

- **Intro:** „2027 · Animated movies coming · 57 new films“ + posterlar yelpigʻichi
- **Har bir film:** rasmiy poster 3D burilish va yaltirash bilan kiradi; fon — shu posterning xiralashtirilgan varianti; kalendar varagʻi (oy, sana, hafta kuni) varaqlanadi; mamlakat bayrogʻi, studiya, uslub (CG / Anime / 2D / Stop-motion), pastda yanvar–dekabr yil chizigʻi
- **Outro:** 57 ta poster setkasi, „Which one are you waiting for?“, Subscribe

Musiqa: A minor / C major, quvnoq elektron-pop (pluck, chelesta, xor, supersaw lead), 4 bosqichda kuchayib boradi, effektlar: poster whoosh, kalendar varagʻi, muhr, uchqunlar, yil chizigʻi tiqlari.

## Maʼlumot manbalari

Sanalar 2026-yil 1-oktabr holatiga koʻra [Wikipedia: List of animated feature films of 2027](https://en.wikipedia.org/wiki/List_of_animated_feature_films_of_2027), TMDB va yangilik saytlaridan tekshirildi. Har bir kartochkadagi mamlakat — film oʻsha sanada chiqadigan davlat. 2027-yil sanalari hali oʻzgarishi mumkin.

## Qayta yaratish

```bash
pip install numpy scipy pillow
npm install
python3 find_posters.py       # Wikipedia ro‘yxati → TMDB/IMDb posterlari (candidates.json)
python3 fetch_posters.py      # films.json dagi posterlar (posters/)
python3 prepare.py            # HD poster, xira fonlar, bayroqlar
node render.cjs               # out/animated-2027.mp4 (ovoz bilan)
node render.cjs --thumb       # out/thumbnail.jpg
node render.cjs --stills=6,40 # tekshirish uchun kadrlar
```

Film qoʻshish/olib tashlash: TMDB id ni `python3 tmdb_search.py "Nomi" 2027` bilan toping, `films.json` ni tahrirlang → `python3 fetch_posters.py <id>` → `python3 prepare.py` → `node render.cjs`.

## Kreditlar

- Shriftlar: Bebas Neue, Outfit (SIL Open Font License)
- Bayroqlar: Wikimedia Commons (public domain)
- Emoji (🔔 👇): Microsoft Fluent Emoji (MIT)
- Posterlar: tegishli studiya va distribyutorlarga tegishli
