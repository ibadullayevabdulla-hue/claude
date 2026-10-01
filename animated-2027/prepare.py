#!/usr/bin/env python3
"""Builds render-ready assets from posters/:
  posters/hd/<id>.jpg  poster at 1300 px tall
  posters/bg/<id>.jpg  blurred, darkened 1920x1080 backdrop
  flags/<CC>.png       country flags (public-domain SVGs from Wikimedia Commons)"""
import json, pathlib, subprocess, time, urllib.parse
from PIL import Image, ImageEnhance, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
UA = "AnimatedMovies2027/1.0 (https://github.com/ibadullayevabdulla-hue/claude; educational video)"
FLAGS = {"US": "Flag of the United States.svg", "JP": "Flag of Japan.svg", "FR": "Flag of France.svg",
         "RU": "Flag of Russia.svg", "AU": "Flag of Australia (converted).svg", "IN": "Flag of India.svg",
         "DE": "Flag of Germany.svg", "CN": "Flag of the People's Republic of China.svg", "KR": "Flag of South Korea.svg",
         "MY": "Flag of Malaysia.svg", "ES": "Flag of Spain.svg", "EE": "Flag of Estonia.svg", "SG": "Flag of Singapore.svg"}


def curl(url, dest=None):
    for attempt in range(8):
        r = subprocess.run(["curl", "-sSfL", "-A", UA] + (["-o", str(dest)] if dest else []) + [url], capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(2 ** attempt)
    raise RuntimeError(url)


films = json.loads((HERE / "films.json").read_text())
(HERE / "posters" / "hd").mkdir(exist_ok=True)
(HERE / "posters" / "bg").mkdir(exist_ok=True)
for f in films:
    im = Image.open(HERE / "posters" / f["poster"]).convert("RGB")
    s = 1300 / im.height
    hd = im.resize((round(im.width * s), 1300), Image.LANCZOS)
    hd.save(HERE / "posters" / "hd" / f"{f['id']}.jpg", quality=90)
    f["w"], f["h"] = hd.size
    # backdrop: cover-crop to 16:9, blur, darken
    W, H = 1920, 1080
    s = max(W / im.width, H / im.height) * 1.15
    bg = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    left, top = (bg.width - W) // 2, int((bg.height - H) * 0.3)
    bg = bg.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(38))
    bg = ImageEnhance.Brightness(ImageEnhance.Color(bg).enhance(1.25)).enhance(0.62)
    bg.save(HERE / "posters" / "bg" / f"{f['id']}.jpg", quality=85)
    print(f["id"], f["w"], f["h"])

(HERE / "films.json").write_text(json.dumps(films, indent=2, ensure_ascii=False) + "\n")

(HERE / "flags").mkdir(exist_ok=True)
for cc, name in FLAGS.items():
    if (HERE / "flags" / f"{cc}.png").exists():
        continue
    q = urllib.parse.urlencode({"action": "query", "format": "json", "formatversion": 2, "prop": "imageinfo",
                                "iiprop": "url", "iiurlwidth": 240, "titles": "File:" + name})
    info = json.loads(curl("https://en.wikipedia.org/w/api.php?" + q))
    curl(info["query"]["pages"][0]["imageinfo"][0]["thumburl"], HERE / "flags" / f"{cc}.png")
    time.sleep(3)
