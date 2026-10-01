# Working with this user — saved rules and styles

Read this first in every session. It records what the user asked for and liked,
so new work matches earlier work without them repeating themselves.

## Communication & delivery

- The user writes in **Uzbek** (Latin script). Reply in Uzbek.
- **Never send the user to GitHub or Telegram.** Hand over finished files
  **directly in the chat** (SendUserFile). Still commit and push the project to
  the working branch.
- Chat upload limit is **30 MB**. Encode videos for chat as two-pass HEVC 1080p:
  `-c:v libx265 -b:v <kbps> -x265-params pass=1|2 -tag:v hvc1 -c:a aac -b:a 160k -movflags +faststart`.
  Pick `<kbps>` ≈ `28 MB × 8 / duration − 160k` (about 1800k for ~2 min).
  Put the result in `deliver/` (git-ignored).
- **Presentations** are Slides artifacts (claude.ai). Give the link and remind
  the user that a deck is private until they share it from the Share menu.

## Video rules (all YouTube videos)

1. **On-screen text in English**, unless the user asks otherwise.
2. **Always add music and sound effects.** Synthesise them with
   `soundtrack.py` (numpy/scipy), so they are copyright-free. The user complained
   once when a video had no sound.
3. **Use real images** of the actual characters or films, taken from the
   internet. No placeholders, no look-alikes.
4. **Make it dynamic.** Every element animates on the beat: pops, whooshes,
   confetti, odometers, transitions.
5. **Ship a YouTube kit** with every video: `YOUTUBE.md` (titles, description
   with chapters, tags, pinned comment), `out/thumbnail.jpg` (1280×720) and a
   `README.md` in Uzbek.
6. Pick the length from the content. For character timelines, aim for about
   2 minutes and adjust the BPM to get there.

## Video styles

### Style A — "Characters by year" timeline

Projects: `cartoon-timeline/` (50 icons, 1928–2000, 2:02) and `cartoon-2000s/`
(46 icons, 2000–2023, 1:56). **Start a new one by copying `cartoon-2000s/`.**

- **Look:**
  - Fredoka font: bold white text with a thick dark-ink (#1b1036) stroke and a drop shadow.
  - Each decade has its own diagonal gradient, rotating rays, confetti and a dot pattern.
  - Characters are die-cut stickers (white outline and shadow, made by `prepare_images.py`) or white-framed photos.
- **Intro (2 bars):**
  - The hook "HOW OLD IS YOUR / FAVORITE CARTOON?" over a collage of 12 stickers.
  - Under it, a pill "N ICONS · first year – last year".
- **Decade card (1 bar):**
  - A circle wipe reveals a huge "2000s" label, the era line and an "N ICONS" pill.
  - Sound: slide whistle → impact → tom fill.
- **Character (1 bar each):**
  - The image swipes in with a squash, a ring and a confetti burst.
  - The name pops in letter by letter, and a 4-digit year odometer ticks once per year.
  - Left panel: the decade, its era line and progress dots.
  - Right panel: "#n/N", a star badge "X YEARS OLD" (counted to 2026) and the DEBUT title.
  - Bottom: a timeline with a marker.
- **Outro (3 bars):**
  - A grid of all characters as tiles, each with its year.
  - "WHICH ONE WAS YOUR CHILDHOOD?" and "Tell us in the comments 👇".
  - A cursor clicks SUBSCRIBE, which turns into SUBSCRIBED.
- **Music:** one I–V–vi–IV progression and melody. The genre follows the decade; the key rises one step for the last era.
- **Images:**
  - Fandom wikis (MediaWiki API, `fetch_images.py`, search with `find_image.py`) give large, transparent renders.
  - Wikipedia returns HTTP 429 from this container, and its non-free images are only about 250 px wide.
  - Prefer transparent renders. Remove plain white backgrounds with `"knockout": true`.
- **Steps for a new list:**
  1. Edit `characters.json` (id, name, year, debut, src).
  2. In `index.html`, edit `DECADES`, `Y0`/`Y1`/`FROM` and `INTRO_IDS`.
  3. In `soundtrack.py`, edit `DECADES` and the per-decade `style_bar`.
  4. Set `BPM` in both files. Total length = (2 + decades + characters + 3) bars × 4 beats.

### Style B — "Upcoming movies" with official posters

Projects: `october-premieres/` (17 films, 1:18) and `animated-2027/` (57 films, 3:58).

- **Look:**
  - Bebas Neue and Outfit fonts.
  - Each film gets 2 bars (4 s) at 120 BPM.
  - The official poster flies in with a 3D turn and a shine. The background is a blurred copy of the same poster.
  - A calendar page flips to the date. Films without a known date show "COMING · 2027 · DATE TBA".
  - The card shows the country flag, the studio and the style (CG / Anime / 2D / Stop-motion), with a month or year strip at the bottom.
- **Intro:** a fan of posters with "N new films".
- **Outro:** a poster grid, "Which one will you watch?" and Subscribe.
- **Data and posters:**
  - Film list: Wikipedia "List of animated feature films of YEAR".
  - Posters: TMDB HTML (search cards, `og:image`, originals under `image.tmdb.org/t/p/original/`) and the IMDb suggestion API.
  - Reject live-action or wrong-film matches.
  - Length scales with the number of films.

### Style C — military promo from the user's own images (Uzbek text)

Project: `litsey-motion/` (Jaloliddin Manguberdi lyceum, 1:32). Use this style when the user sends a logo and infographics and asks for a "harbiycha" (military) video.

- **Text:** Uzbek. Keep the infographic wording exactly, with o‘/g‘ written ‘ and ta’lim written ’.
- **Only Uzbek symbols:**
  - the Uzbek flag, drawn in code and waving;
  - the eight-pointed star;
  - girih pattern;
  - arch (peshtoq) frames;
  - navy and gold colours.
  - No foreign stars or emblems.
- **Structure:**
  - The logo slams in, with the lyceum name above it.
  - A section card for each infographic.
  - One scene (2 bars) per numbered panel. Each scene has an octagram number badge, the title, the text and the cropped photo in a gold frame; the photo side alternates.
  - Counters for numbers (ball, %).
  - Outro with the logo and the slogan.
- **Images:**
  - Cut panels out of the infographics (`crops.json`).
  - Upscale them 4× with OpenCV EDSR (`upscale.py`), which is much sharper than Lanczos.
- **Music:** an original military march (snare cadences, timpani, brass fanfare, strings, choir), 120 BPM.

(`motion/` is a separate 30-second Claude Code promo, not a series style.)

## Presentation styles (Slides artifacts)

- **Language:** Uzbek source documents are turned into **Russian** decks. "Har bir sahifasidan" means at least one slide per page of the document.
- **Deck 1 — official order** (`Приказ`): navy and gold, Oswald with IBM Plex Sans, a classic look with infographics.
- **Deck 2 — lyceum info** (the one the user liked after feedback):
  - Every item has a **matching picture**: a robot for robotics, a horse rider for horse riding, and so on.
  - **All pictures are in one consistent style.** Use Microsoft Fluent 3D emoji (MIT), downloaded from `raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/<Name>/3D/<name>_3d.png`.
  - Pictures sit on soft pastel tiles. Fonts: Unbounded with Manrope (both support Cyrillic).
  - Colours: deep indigo with orange, on cream and lavender backgrounds.
  - Infographics: stat cards, bars and progress strips.
  - The user asked for "colours people like": bright, friendly and clean.
- Never invent statistics. Values computed from the document (shares, differences) are fine; mention them in the reply.

## Pipeline notes

- **Rendering:**
  - `render.cjs` loads Playwright with `NODE_PATH=$(npm root -g)` and runs parallel workers.
  - Take JPEG screenshots: they are about 2× faster than PNG.
  - Each worker encodes with ffmpeg, then the parts are joined with concat and the soundtrack is muxed in.
- **Check stills before the full render** with `node render.cjs --stills=…`.
- **Stopping Chromium:** kill it by PID, never `pkill -f`, which also kills the calling shell.
