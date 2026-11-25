"""usage: cmp_den.py MODEL(zimage|h3) d1 d2 ...  -> results/HR/den_<model>_city.png : rows = crops (woman, car body), cols = original(up), 4K at each denoise"""
import sys, numpy as np
from PIL import Image, ImageDraw
R = r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\bench\results"
ORIG = {"zimage": "zimage_v10_depth_s101_d0.8_e0.8_l0_0.png", "h3": "h3image_v7B_2ref_s101_0.png", "moss": "moss_v10_depth_color_end1_s101_0.png", "flux": "flux2dev_v10A_turbo_s101_0.png", "ph3": "ph3image_v10A_s101_0.png"}
m = sys.argv[1]; dens = sys.argv[2:]
old = Image.open(f"{R}\{ORIG[m]}").convert("RGB").resize((3840, 2304), Image.LANCZOS)
ims = [("originale (x3)", old)] + [("4K d%s" % d, Image.open(f"{R}\HR\hr{'g' if m == 'ph3' else 't'}_city_{m}_W_s101_d{round(float(d)*100):02d}.png").convert("RGB")) for d in dens]
m0 = np.asarray(Image.open(r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\inputs\mask_foreground.png").convert("L").resize((3840, 2304))) > 128
ys, xs = np.where(m0)
# crops: upper body of the woman (face/hair), and the car's front quarter
crops = [("donna", (int(xs.mean()) - 280, int(ys.min()) + 20)), ("auto", (330, 1300))]
cw, ch = 560, 420
S = Image.new("RGB", (cw * len(ims), ch * len(crops)), (20, 20, 20))
for r, (cn, (x, y)) in enumerate(crops):
    x = min(max(x, 0), 3840 - cw); y = min(max(y, 0), 2304 - ch)
    for c, (t, im) in enumerate(ims):
        tile = im.crop((x, y, x + cw, y + ch)); d = ImageDraw.Draw(tile); d.rectangle([0, 0, 200, 20], fill=(0, 0, 0)); d.text((5, 4), f"{cn} - {t}", fill=(255, 255, 255)); S.paste(tile, (c * cw, r * ch))
out = f"{R}\HR\den_{m}_city.png"; S.save(out); print(out)
