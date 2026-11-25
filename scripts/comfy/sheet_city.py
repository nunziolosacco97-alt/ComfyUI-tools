"""Comparison sheet for the McLaren-with-woman scene: original | 4K | crop on the woman at 100% (orig upscaled | 4K)."""
import os, numpy as np
from PIL import Image, ImageDraw
R = r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\bench\results"
ORIG = {"zimage": "zimage_v10_depth_s101_d0.8_e0.8_l0_0.png", "flux": "flux2dev_v10A_turbo_s101_0.png", "moss": "moss_v10_depth_color_end1_s101_0.png", "ph3": "ph3image_v10A_s101_0.png", "h3": "h3image_v7B_2ref_s101_0.png"}
ms = [("zimage", "Z-Image"), ("flux", "FLUX.2"), ("moss", "MOSS"), ("ph3", "P-H3"), ("h3", "H3")]
m0 = np.asarray(Image.open(r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\inputs\mask_foreground.png").convert("L").resize((3840, 2304))) > 128
ys, xs = np.where(m0); cx, cy = int(xs.mean()), int(ys.mean())   # centre of the pedestrian mask
w, h = 640, 384
S = Image.new("RGB", (w * 4, h * 5), (20, 20, 20))
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 230, 22], fill=(0, 0, 0)); d.text((6, 5), t, fill=(255, 255, 255)); return im
for r, (m, nm) in enumerate(ms):
    old = Image.open(f"{R}\{ORIG[m]}").convert("RGB"); md = "g" if m == "ph3" else "t"
    new = Image.open(f"{R}\HR\hr{md}_city_{m}_W_s101_d40.png").convert("RGB")
    up = old.resize(new.size, Image.LANCZOS)
    bx = (min(max(cx - 320, 0), 3840 - 640), min(max(cy - 192, 0), 2304 - 384)); bx = (bx[0], bx[1], bx[0] + 640, bx[1] + 384)
    cells = [lab(old.resize((w, h), Image.LANCZOS), nm + " originale"), lab(new.resize((w, h), Image.LANCZOS), nm + " 4K (" + ("tile" if md == "t" else "globale") + ")"),
             lab(up.crop(bx), nm + " orig. 100% (donna)"), lab(new.crop(bx), nm + " 4K 100% (donna)")]
    for c, im in enumerate(cells): S.paste(im, (c * w, r * h))
out = f"{R}\HR\confronto_city.png"; S.save(out); print(out)
