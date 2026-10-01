# October 2026 — animatsion premyeralar (motion video)

Oktabr 2026 da kinoteatrlarga chiqadigan 17 ta animatsion filmning 1:18 lik dinamik videosi (1920×1080, 30 fps), original musiqa va ovoz effektlari bilan.

- **Video:** `out/october-premieres.mp4`
- **Thumbnail:** `out/thumbnail.jpg`
- **Sarlavha, tavsif (sanalar ro'yxati bilan), teglar, boblar:** [`YOUTUBE.md`](YOUTUBE.md)

## Tuzilishi

120 BPM — har bir filmga 2 takt (4 s): intro 4 s + 17 × 4 s + outro 6 s = 78 s. Filmlar soni oʻzgarsa, davomiylik avtomatik moslashadi (`films.json`).

- **Intro:** „OCTOBER 2026 · Animated movie premieres · 17 new films“ + posterlar yelpigʻichi
- **Har bir film:** rasmiy poster 3D burilish va yaltirash bilan kiradi; fon — shu posterning xiralashtirilgan varianti; kalendar varagʻi (sana + hafta kuni) varaqlanadi; mamlakat bayrogʻi, studiya, uslub (CG / Anime / 2D / Stop-motion), pastda oktabr kalendari
- **Outro:** 17 ta poster setkasi, „Which one will you watch?“, Subscribe

Musiqa: D minor, oktabr/Halloween ruhidagi oʻynoqi kuy (pitsikato, chelesta, organ, xor, teremin), effektlar: poster whoosh, kalendar varagʻi, muhr, uchqunlar, kalendar tiqlari.

## Maʼlumot manbalari

Sanalar 2026-yil 1-oktabr holatiga koʻra [Wikipedia: List of animated feature films of 2026](https://en.wikipedia.org/wiki/List_of_animated_feature_films_of_2026), TMDB va yangilik saytlaridan tekshirildi. Har bir kartochkadagi mamlakat — film oʻsha sanada chiqadigan davlat.

## Qayta yaratish

```bash
pip install numpy scipy pillow
npm install
python3 fetch_posters.py      # posterlar TMDB'dan (posters/)
python3 prepare.py            # HD poster, xira fonlar, bayroqlar
node render.cjs               # out/october-premieres.mp4 (ovoz bilan)
node render.cjs --thumb       # out/thumbnail.jpg
node render.cjs --stills=6,40 # tekshirish uchun kadrlar
```

Film qoʻshish/olib tashlash: TMDB id ni `python3 tmdb_search.py "Nomi" 2026` bilan toping, `films.json` ni tahrirlang → `python3 fetch_posters.py <id>` → `python3 prepare.py` → `node render.cjs`.

## Kreditlar

- Shriftlar: Bebas Neue, Outfit (SIL Open Font License)
- Bayroqlar: Wikimedia Commons (public domain)
- Emoji (🔔 👇): Microsoft Fluent Emoji (MIT)
- Posterlar: tegishli studiya va distribyutorlarga tegishli
