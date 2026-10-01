#!/usr/bin/env python3
"""Resizes img/* into img/hd/ (Lanczos + light sharpening), trims transparent
margins, and records in characters.json whether each image is a cut-out."""
import json, pathlib
from PIL import Image, ImageChops, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "img" / "hd"
OUT.mkdir(exist_ok=True)
TARGET = 1000  # longest side, px
OUTLINE = 15    # sticker outline thickness, px at TARGET size
PAD = 44


def sticker(im):
    """White die-cut outline + soft offset shadow, baked into the cut-out."""
    im = _pad(im)
    a = im.getchannel("A")
    grown = a.filter(ImageFilter.GaussianBlur(OUTLINE * 0.55)).point(lambda v: 255 if v > 14 else 0)
    grown = grown.filter(ImageFilter.GaussianBlur(1.2))
    shadow = Image.new("RGBA", im.size, (20, 8, 40, 0))
    shadow.putalpha(ImageChops.offset(grown, 12, 16).point(lambda v: v * 70 // 255).filter(ImageFilter.GaussianBlur(5)))
    white = Image.new("RGBA", im.size, (255, 255, 255, 0))
    white.putalpha(grown)
    out = Image.alpha_composite(shadow, white)
    return Image.alpha_composite(out, im)


def _pad(im):
    canvas = Image.new("RGBA", (im.width + 2 * PAD, im.height + 2 * PAD), (0, 0, 0, 0))
    canvas.paste(im, (PAD, PAD))
    return canvas

def process(name):
    im = Image.open(HERE / "img" / name).convert("RGBA")
    a = im.getchannel("A")
    w, h = im.size
    corners = [a.getpixel(p) for p in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
    # transparent corners, or a large transparent area (e.g. a render standing on a base)
    cutout = sum(corners) / 4 < 20 or sum(a.histogram()[:20]) > 0.15 * w * h
    if cutout:
        box = a.point(lambda v: 255 if v > 10 else 0).getbbox()
        if box:
            im = im.crop(box)
    s = TARGET / max(im.size)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if s > 1:
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=55, threshold=2))
    stem = pathlib.Path(name).stem
    if cutout:
        im = sticker(im)
        dest = OUT / f"{stem}.webp"
        im.save(dest, quality=92, method=6)
    else:
        dest = OUT / f"{stem}.jpg"
        im.convert("RGB").save(dest, quality=92)
    return dest.name, cutout, im.size

chars = json.loads((HERE / "characters.json").read_text())
for c in chars:
    c["hd"], c["cutout"], (c["w"], c["h"]) = process(c["img"])
    if c.get("img2"):
        c["hd2"], _, (c["w2"], c["h2"]) = process(c["img2"])
    print(f'{c["id"]:<12} {"cutout" if c["cutout"] else "framed":<7} {c["w"]}x{c["h"]}')
(HERE / "characters.json").write_text(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
