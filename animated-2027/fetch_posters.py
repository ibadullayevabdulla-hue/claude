#!/usr/bin/env python3
"""Downloads each film's main poster (TMDB original size, en-US) into posters/."""
import json, pathlib, re, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"
OUT = HERE / "posters"
OUT.mkdir(exist_ok=True)


def get(url, dest=None):
    for attempt in range(5):
        r = subprocess.run(["curl", "-sSfL", "-A", UA, "-H", "Accept-Language: en-US"] + (["-o", str(dest)] if dest else []) + [url], capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(2 ** attempt)
    raise RuntimeError(f"failed: {url}")


films = json.loads((HERE / "films.json").read_text())
only = set(sys.argv[1:])
for f in films:
    if only and f["id"] not in only:
        continue
    url = f.get("poster_url")
    if not url:
        page = get(f"https://www.themoviedb.org/movie/{f['tmdb']}?language=en-US").decode("utf-8", "replace")
        m = re.search(r'property="og:image" content="[^"]*/t/p/[^/]+/([A-Za-z0-9]+\.(?:jpg|png))"', page)
        url = f"https://image.tmdb.org/t/p/original/{m.group(1)}"
    ext = pathlib.Path(url).suffix.lower()
    dest = OUT / f"{f['id']}{ext}"
    get(url, dest)
    f["poster"] = dest.name
    print(f"{f['id']:<12} {url}")
    time.sleep(0.5)
(HERE / "films.json").write_text(json.dumps(films, indent=2, ensure_ascii=False) + "\n")
