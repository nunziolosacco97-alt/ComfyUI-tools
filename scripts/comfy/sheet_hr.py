import sys, os
from PIL import Image, ImageDraw
sc, v = sys.argv[1], sys.argv[2]
R = r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\bench\results"
ms = [("zimage", "Z-Image"), ("flux", "FLUX.2"), ("moss", "MOSS"), ("ph3", "P-H3"), ("h3", "H3")]
w, h = 640, 384; cw, ch = 640, 384
S = Image.new("RGB", (w * 4, h * 5), (20, 20, 20))
def lab(im, t):
    d = ImageDraw.Draw(im); d.rectangle([0, 0, 230, 22], fill=(0, 0, 0)); d.text((6, 5), t, fill=(255, 255, 255)); return im
for r, (m, nm) in enumerate(ms):
    old = Image.open(f"{R}\{sc}_{m}_{v}_s101_nf_0.png").convert("RGB")
    md = "g" if m == "ph3" else "t"
    new = Image.open(f"{R}\HR\hr{md}_{sc}_{m}_{v}_s101_d40.png").convert("RGB")
    FW, FH = new.size; up = old.resize((FW, FH), Image.LANCZOS)
    bx = (FW // 2 - cw // 2 - 100, int(FH * 0.42), FW // 2 + cw // 2 - 100, int(FH * 0.42) + ch)
    cells = [lab(old.resize((w, h), Image.LANCZOS), nm + " originale"), lab(new.resize((w, h), Image.LANCZOS), nm + " 4K (" + ("tile" if md == "t" else "globale") + ")"),
             lab(up.crop(bx), nm + " orig. 100%"), lab(new.crop(bx), nm + " 4K 100%")]
    for c, im in enumerate(cells): S.paste(im, (c * w, r * h))
out = f"{R}\HR\confronto_{sc}_{v}.png"; S.save(out); print(out)
