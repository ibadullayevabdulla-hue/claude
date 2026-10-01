#!/usr/bin/env python3
"""Lists TMDB search candidates for a query: python3 tmdb_search.py "Wildwood" [year]"""
import html, re, subprocess, sys, urllib.parse
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0 Safari/537.36"

def get(url):
    return subprocess.run(["curl", "-sSfL", "-A", UA, "-H", "Accept-Language: en-US", url], capture_output=True, check=True).stdout.decode("utf-8", "replace")

def search(q, year=None):
    url = "https://www.themoviedb.org/search/movie?" + urllib.parse.urlencode({"query": q, **({"year": year} if year else {})})
    page = get(url)
    out = []
    for block in page.split('class="comp:media-card')[1:]:
        href = re.search(r'href="/movie/(\d+)[^"]*"', block)
        title = re.search(r'<h2[^>]*>(?:<span>)?(.*?)<', block, re.S)
        date = re.search(r'release_date[^>]*>([^<]*)<', block)
        poster = re.search(r'/t/p/w94_and_h141_face/([A-Za-z0-9]+\.jpg)', block)
        if href:
            out.append((href.group(1), html.unescape(title.group(1).strip()) if title else "?", date.group(1).strip() if date else "", poster.group(1) if poster else None))
    return out

if __name__ == "__main__":
    for r in search(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)[:6]:
        print(r)
