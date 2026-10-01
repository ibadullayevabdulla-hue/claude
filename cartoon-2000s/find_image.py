#!/usr/bin/env python3
"""Searches a Fandom wiki's files by name and lists the largest matches, to
pick a better image for a character (e.g. a transparent "render").

    python3 find_image.py disney "Stitch render"
    python3 find_image.py pixar "McQueen png"

Put the chosen file into characters.json as "src": {"wiki": ..., "file": "File:..."}.
"""
import json, sys, urllib.parse, urllib.request

wiki, q = sys.argv[1], sys.argv[2]
u = f"https://{wiki}.fandom.com/api.php?" + urllib.parse.urlencode({"format": "json", "action": "query", "generator": "search", "gsrsearch": q,
                                                                    "gsrnamespace": 6, "gsrlimit": 40, "prop": "imageinfo", "iiprop": "size"})
d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=30))
rows = [(p.get("imageinfo", [{}])[0].get("width", 0), p.get("imageinfo", [{}])[0].get("height", 0), p["title"]) for p in d.get("query", {}).get("pages", {}).values()]
for w, h, t in sorted(rows, reverse=True)[:20]:
    print(f"{w:>5}x{h:<5} {t}")
