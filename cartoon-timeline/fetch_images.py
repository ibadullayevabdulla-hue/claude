#!/usr/bin/env python3
"""Downloads each character's main Wikipedia image into img/ (see characters.json)."""
import json, pathlib, subprocess, sys, time, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
UA = "CartoonTimeline/1.0 (https://github.com/ibadullayevabdulla-hue/claude; educational video)"
chars = json.loads((HERE / "characters.json").read_text())

def get(url, dest=None):
    """curl with retries — Wikimedia rate-limits bursts of requests."""
    for attempt in range(7):
        cmd = ["curl", "-sSfL", "-A", UA] + (["-o", str(dest)] if dest else []) + [url]
        out = subprocess.run(cmd, capture_output=True)
        if out.returncode == 0:
            return out.stdout
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {url}\n{out.stderr.decode()}")

def api(params):
    q = urllib.parse.urlencode({"format": "json", "formatversion": 2, **params})
    return json.loads(get(f"https://en.wikipedia.org/w/api.php?{q}"))

def file_url(name):
    """Original URL of a File: page (used when a character pins a specific file)."""
    r = api({"action": "query", "prop": "imageinfo", "iiprop": "url|size", "iiurlwidth": THUMB, "titles": "File:" + name})
    ii = r["query"]["pages"][0]["imageinfo"][0]
    return ii.get("thumburl", ii["url"]), ii["width"], ii["height"]

THUMB = 1000  # cached thumbnails; originals get rate-limited (429)
only = set(sys.argv[1:])
for c in chars:
    if only and c["id"] not in only:
        continue
    if c.get("file"):
        url, w, h = file_url(c["file"])
    else:
        r = api({"action": "query", "prop": "pageimages", "piprop": "original|thumbnail", "pithumbsize": THUMB, "pilicense": "any", "redirects": 1, "titles": c["wiki"]})
        page = r["query"]["pages"][0]
        if "original" not in page:
            print(f"!! {c['id']}: no page image for {c['wiki']}")
            continue
        url, w, h = page["thumbnail"]["source"], page["original"]["width"], page["original"]["height"]
    url = url.split("?")[0]
    ext = pathlib.Path(urllib.parse.unquote(url)).suffix.lower()
    for old in [*(HERE / "img").glob(c["id"] + ".*"), *(HERE / "img").glob(c["id"] + "-2.*")]:
        old.unlink()
    dest = HERE / "img" / (c["id"] + ext)
    get(url, dest)
    time.sleep(1.5)
    c["img"] = dest.name
    if c.get("file2"):  # second image shown beside the first (e.g. Tom & Jerry)
        url2 = file_url(c["file2"])[0].split("?")[0]
        dest2 = HERE / "img" / (c["id"] + "-2" + pathlib.Path(urllib.parse.unquote(url2)).suffix.lower())
        get(url2, dest2)
        c["img2"] = dest2.name
    print(f"{c['id']:<14} {w}x{h}  {urllib.parse.unquote(url.rsplit('/', 1)[-1])}")
(HERE / "characters.json").write_text(json.dumps(chars, indent=2, ensure_ascii=False) + "\n")
