#!/usr/bin/env python3
"""Cuts each scene image out of the two infographics (crops.json) and
upscales it 4x with the EDSR super-resolution model into assets/.

    pip install opencv-contrib-python-headless
    python3 upscale.py            # all crops (about 40 s each on CPU)
    python3 upscale.py q1 i5a     # just these
"""
import json, pathlib, sys
import cv2

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "assets"; OUT.mkdir(exist_ok=True)
MODEL = HERE / "models" / "EDSR_x4.pb"
if not MODEL.exists():  # 38 MB, not kept in git
    import urllib.request
    MODEL.parent.mkdir(exist_ok=True)
    urllib.request.urlretrieve("https://raw.githubusercontent.com/Saafke/EDSR_Tensorflow/master/models/EDSR_x4.pb", MODEL)
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(str(HERE / "models" / "EDSR_x4.pb")); sr.setModel("edsr", 4)
crops = json.loads((HERE / "crops.json").read_text())
keys = sys.argv[1:] or list(crops)
for k in keys:
    f, (x0, y0, x1, y1) = crops[k]
    img = cv2.imread(str(HERE / "src" / f))[y0:y1, x0:x1]
    up = sr.upsample(img)
    s = min(1.0, 2000 / max(up.shape[:2]))
    if s < 1:
        up = cv2.resize(up, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT / f"{k}.jpg"), up, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print(k, up.shape[1], "x", up.shape[0], flush=True)
