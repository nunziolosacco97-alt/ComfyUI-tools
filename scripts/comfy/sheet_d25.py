"""usage: sheet_d25.py SCENE VIEW [models...]  rows = models; cols = original | 4K d0.4 | 4K d0.25 | crop orig | crop d0.4 | crop d0.25 -> results/HR/d25_<scene>_<view>.png"""
import sys, numpy as np
from PIL import Image, ImageDraw
R = r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\bench\results"
sc, v = sys.argv[1], sys.argv[2]; models = sys.argv[3:] or ["zimage", "h3"]
NM = {"zimage": "Z-Image", "h3": "H3"}
CO = {"zimage": "zimage_v10_depth_s101_d0.8_e0.8_l0_0.png", "h3": "h3image_v7B_2ref_s101_0.png"}
w, h = 640, 384
S = Image.new("RGB", (w * 6, h * len(models)), (20, 20, 20))
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 260, 22], fill=(0, 0, 0)); d.text((6, 5), t, fill=(255, 255, 255)); return im
for r, m in enumerate(models):
    old = Image.open(f"{R}\{CO[m] if sc == 'city' else f'{sc}_{m}_{v}_s101_nf_0.png'}").convert("RGB")
    a = Image.open(f"{R}\HR\hrt_{sc}_{m}_{v}_s101_d40.png").convert("RGB"); b = Image.open(f"{R}\HR\hrt_{sc}_{m}_{v}_s101_d25.png").convert("RGB")
    FW, FH = a.size; up = old.resize((FW, FH), Image.LANCZOS)
    if sc == "city":
        mk = np.asarray(Image.open(r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\inputs\mask_foreground.png").convert("L").resize((FW, FH))) > 128
        ys, xs = np.where(mk); x0 = int(xs.mean()) - 320; y0 = int(ys.min()) + 20
    else: x0, y0 = FW // 2 - 320 - 100, int(FH * 0.42)
    bx = (x0, y0, x0 + w, y0 + h); n = NM[m]
    cells = [lab(old.resize((w, h), Image.LANCZOS), n + " originale"), lab(a.resize((w, h), Image.LANCZOS), n + " 4K d0.4"), lab(b.resize((w, h), Image.LANCZOS), n + " 4K d0.25"),
             lab(up.crop(bx), n + " orig. 100%"), lab(a.crop(bx), n + " d0.4 100%"), lab(b.crop(bx), n + " d0.25 100%")]
    for c, im in enumerate(cells): S.paste(im, (c * w, r * h))
out = f"{R}\HR\d25_{sc}_{v}.png"; S.save(out); print(out)
