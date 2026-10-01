#!/usr/bin/env python3
"""Downloads the Tabler Icons (MIT) used in the video and writes icons.json:
name -> list of SVG element strings on the 24x24 grid (bounding-box path removed)."""
import concurrent.futures as cf, json, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
VER = "3.34.0"
NAMES = sys.argv[1:] or """school files calendar-event stethoscope writing brain bulb puzzle target user-circle run stretching
stopwatch route messages checklist math-function atom calculator clock shirt bed tools-kitchen-2 soup karate hand-rock
robot certificate language history book feather shield-check building-bank file-certificate award trophy medal
users-group clipboard-check id-badge-2 heart-rate-monitor ruler-measure""".split()

def get(name):
    url = f"https://unpkg.com/@tabler/icons@{VER}/icons/outline/{name}.svg"
    try:
        svg = urllib.request.urlopen(url, timeout=30).read().decode()
    except Exception as e:
        return name, None
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    els = [m.strip() for m in re.findall(r"<(?:path|circle|rect|line|polyline|polygon|ellipse)[^>]*/>", body)]
    els = [e for e in els if 'stroke="none"' not in e]
    return name, els

out = {}
with cf.ThreadPoolExecutor(8) as ex:
    for name, els in ex.map(get, NAMES):
        print(f"{name:<20} {'MISSING' if els is None else len(els)}")
        if els:
            out[name] = els
(HERE / "icons.json").write_text(json.dumps(out, indent=1) + "\n")
