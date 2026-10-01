#!/usr/bin/env python3
"""Downloads each character's image into img/ from the source recorded in
characters.json ("src": a direct URL, or a Fandom wiki + File: title).
Characters marked "knockout" are on a plain white background: it is removed
so they become die-cut stickers like the transparent renders.

    python3 fetch_images.py            # all characters
    python3 fetch_images.py elsa olaf  # just these ids
"""
import io, json, pathlib, sys, time, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 CartoonTimeline/1.0 (educational video)"}


def get(url):
    for attempt in range(6):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except Exception:
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {url}")


def file_url(wiki, title):
    q = urllib.parse.urlencode({"format": "json", "action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url"})
    page = next(iter(json.loads(get(f"https://{wiki}.fandom.com/api.php?{q}"))["query"]["pages"].values()))
    return page["imageinfo"][0]["url"]


def knockout(im):
    """Clear the white background connected to the image border."""
    a = np.asarray(im).astype(int)
    lab, _ = ndimage.label(a[..., :3].min(axis=2) > 232)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    alpha = Image.fromarray(np.where(np.isin(lab, list(border)), 0, 255).astype("uint8"))
    im.putalpha(alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2)))
    return im


chars = json.loads((HERE / "characters.json").read_text())
only = set(sys.argv[1:])
(HERE / "img").mkdir(exist_ok=True)
for c in chars:
    if only and c["id"] not in only:
        continue
    src = c["src"]
    data = get(src["url"] if "url" in src else file_url(src["wiki"], src["file"]))
    for old in (HERE / "img").glob(c["id"] + ".*"):
        old.unlink()
    if c.get("knockout"):
        dest = HERE / "img" / f"{c['id']}.png"
        knockout(Image.open(io.BytesIO(data)).convert("RGBA")).save(dest)
    else:  # Fandom's CDN may serve WebP whatever the file name says
        ext = ".png" if data[:4] == b"\x89PNG" else ".webp" if data[8:12] == b"WEBP" else ".jpg"
        dest = HERE / "img" / f"{c['id']}{ext}"
        dest.write_bytes(data)
    c["img"] = dest.name
    print(f"{c['id']:<10} {dest.name}")
(HERE / "characters.json").write_text(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
