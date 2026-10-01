#!/usr/bin/env python3
"""Builds candidates.json from Wikipedia's 2027 animated-film list and finds a
poster for each title on TMDB (English poster when one exists) with the IMDb
suggestion API as a fallback."""
import difflib, json, pathlib, re, subprocess, sys, time, urllib.parse

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from tmdb_search import search as tmdb_search  # noqa: E402

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"


def get(url):
    for attempt in range(5):
        r = subprocess.run(["curl", "-sSfL", "-A", UA, "-H", "Accept-Language: en-US", url], capture_output=True)
        if r.returncode == 0:
            return r.stdout.decode("utf-8", "replace")
        time.sleep(2 ** attempt)
    return ""


def unlink(s):
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{(?:ill|interlanguage link)\|([^|}]*)[^}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^}]*\}\}", "", s)
    return re.sub(r"<br\s*/?>", " · ", s).replace("''", "").strip(" ·")


def rows():
    w = json.loads((HERE / "wiki_2027.json").read_text())["parse"]["wikitext"]
    for r in w.split("\n|-"):
        r = re.sub(r"<ref[^>]*/>", "", r)
        r = re.sub(r"<ref.*?</ref>", "", r, flags=re.S)
        t = re.search(r"''(.+?)''", r)
        if not t or "scheduled for release" in r[:300]:
            continue
        cells = [c.strip() for c in re.split(r"\n\||\|\|", r) if c.strip()]
        title = unlink(t.group(0))
        dates = []
        for y, mo, d, note in re.findall(r"\{\{dts\|(\d{4})\|(\d{1,2})\|(\d{1,2})\}\}\s*(?:\{\{small\|\(([^)]*)\)\}\})?", r):
            note = unlink(note or "")
            if y == "2027" and "estival" not in note:
                dates.append((int(mo), int(d), note))
        yield dict(title=title, countries=unlink(cells[1]) if len(cells) > 1 else "",
                   studio=unlink(cells[3]) if len(cells) > 3 else "", tech=unlink(cells[4]) if len(cells) > 4 else "",
                   date=min(dates) if dates else None)


def sim(a, b):
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()  # noqa: E731
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def tmdb(title):
    for q, year in ((title, 2027), (title, None)):
        for mid, t, date, poster in tmdb_search(q, year)[:5]:
            if poster and sim(title, t) > .72 and (not date or "2027" in date or year):
                page = get(f"https://www.themoviedb.org/movie/{mid}?language=en-US")
                m = re.search(r'property="og:image" content="[^"]*/t/p/[^/]+/([A-Za-z0-9]+\.(?:jpg|png))"', page)
                if m:
                    return dict(source="tmdb", tmdb=int(mid), match=t, poster_url=f"https://image.tmdb.org/t/p/original/{m.group(1)}")
    return None


def imdb(title):
    q = urllib.parse.quote(title.lower()[:60])
    try:
        d = json.loads(get(f"https://v3.sg.media-imdb.com/suggestion/x/{q}.json") or "{}").get("d", [])
    except json.JSONDecodeError:
        return None
    for it in d:
        if it.get("qid") in ("movie", "tvMovie", "video") and it.get("i") and it.get("y", 2027) >= 2026 and sim(title, it["l"]) > .72:
            return dict(source="imdb", imdb=it["id"], match=it["l"], poster_url=it["i"]["imageUrl"])
    return None


seen, out = set(), []
for r in rows():
    if r["title"] in seen:
        continue
    seen.add(r["title"])
    hit = tmdb(r["title"]) or imdb(r["title"])
    r.update(hit or {})
    out.append(r)
    print(f"{'✓' if hit else '·'} {r['title'][:50]:50} {str(r['date']):22} {hit['source'] + ' ' + hit['match'][:30] if hit else ''}", flush=True)
(HERE / "candidates.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
