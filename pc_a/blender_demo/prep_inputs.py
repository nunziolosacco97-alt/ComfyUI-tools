"""Turns the Blender passes (out_final, 2560x1536) into the ComfyUI inputs (1280x768) + hi-res masks.
usage: python -I prep_inputs.py [src_dir=out_final] [dst_dir=inputs]"""
import sys, os, numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "out_final"); DST = os.path.join(HERE, sys.argv[2] if len(sys.argv) > 2 else "inputs")
os.makedirs(DST, exist_ok=True); os.makedirs(os.path.join(DST, "hires"), exist_ok=True)
W, H = 1280, 768
def load(n): return Image.open(os.path.join(SRC, n + ".png"))
def small(im, resample=Image.LANCZOS): return im.resize((W, H), resample)
for n in ("beauty_color", "beauty_clay", "depth", "normal"):
    im = load(n).convert("RGB"); small(im).save(os.path.join(DST, n + ".png")); im.save(os.path.join(DST, "hires", n + ".png"))
ident = load("id").convert("RGB"); idn = np.asarray(ident)
small(ident, Image.NEAREST).save(os.path.join(DST, "id.png")); ident.save(os.path.join(DST, "hires", "id.png"))
# car alpha: soft at the edge, from the RGBA pass
rgba = load("car_rgba").convert("RGBA"); rgba.save(os.path.join(DST, "hires", "car_rgba.png")); small(rgba).save(os.path.join(DST, "car_rgba.png"))
a_hi = np.asarray(rgba)[..., 3]; Image.fromarray(a_hi).save(os.path.join(DST, "hires", "car_mask.png")); small(Image.fromarray(a_hi)).save(os.path.join(DST, "car_mask.png"))
# part masks from the flat ID colours (nearest colour, tolerance)
def near(rgb, tol=40):
    d = np.abs(idn.astype(np.int16) - np.array(rgb, np.int16)).max(-1); return (d < tol).astype(np.uint8) * 255
PAL = {"paint": (255, 0, 0), "lamp": (0, 255, 255), "glass": (0, 0, 255), "wheel": (0, 255, 0), "caliper": (255, 0, 255), "other_car": (255, 255, 0)}
ENV = {"ground": (160, 160, 160), "sidewalk": (196, 196, 196), "building": (229, 183, 124), "env_glass": (97, 134, 208), "foreground": (255, 188, 0), "sky": (194, 232, 247)}   # emission colours as written through the Standard transform
# note: ID colours were written through the Standard view transform from linear values, so they come out slightly different; auto-detect by clustering below
cols, counts = np.unique(idn.reshape(-1, 3), axis=0, return_counts=True)
big = [(tuple(int(x) for x in c), int(n)) for c, n in sorted(zip(cols.tolist(), counts.tolist()), key=lambda t: -t[1])[:14]]
print("ID colours (rgb, pixels):", big)
for k, rgb in {**PAL, **ENV}.items():
    m = near(rgb, 36);
    if m.sum() > 0: Image.fromarray(m).save(os.path.join(DST, "hires", "mask_%s.png" % k)); small(Image.fromarray(m), Image.LANCZOS).save(os.path.join(DST, "mask_%s.png" % k))
# canny-like lines from depth + normal + id edges (for ControlNets), hi-res then 1280x768
def edges(arr, thr):
    g = ndi.gaussian_filter(arr.astype(np.float32), 1.0); gx = ndi.sobel(g, 1); gy = ndi.sobel(g, 0); return np.hypot(gx, gy) > thr
d = np.asarray(load("depth").convert("L")).astype(np.float32) / 255; nrm = np.asarray(load("normal").convert("RGB")).astype(np.float32) / 255
e = edges(d, 0.12) | edges(nrm[..., 0], 0.5) | edges(nrm[..., 1], 0.5) | edges(nrm[..., 2], 0.5) | edges(idn.mean(-1), 40)
e = ndi.binary_dilation(e, np.ones((2, 2))) if e.shape[0] > 1000 else e
li = Image.fromarray((e * 255).astype(np.uint8)); li.save(os.path.join(DST, "hires", "lines.png")); small(li).point(lambda v: 255 if v > 90 else 0).save(os.path.join(DST, "lines.png"))
print("written to", DST, sorted(os.listdir(DST)))
