"""Finish one raw 1536x896 frame: (1) Kontext cleanup of the car (remove lettering/logos, black wings), (2) panning blur on background,
(3) 1280x768, (4) cinematic grade + warm sunset sky.  usage: python -I finish_frame.py <raw.png> <out.png>"""
import glob, json, os, sys, time, urllib.request
import numpy as np, torch, torch.nn.functional as F
from PIL import Image, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade import grade, sky
B = "http://127.0.0.1:8188"; SH = r"C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared"; IN = SH + r"\input"
import os as _os
LS = [12, 26, 55] if _os.environ.get("FF_SIMPLE") else ([2, 3, 4] if _os.environ.get("FF_LOWDOF") else [8, 16, 34])


def post(p, d): return json.load(urllib.request.urlopen(urllib.request.Request(B + p, json.dumps(d).encode(), {"Content-Type": "application/json"}), timeout=60))


def wait(pid):
    while pid not in json.load(urllib.request.urlopen(B + "/history/" + pid, timeout=30)): time.sleep(2)


def carmask(img):
    img.save(IN + r"\ff_in.png")
    wm = {"1": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
          "2": {"class_type": "LoadImage", "inputs": {"image": "ff_in.png"}},
          "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["1", 0], "image": ["2", 0]}},
          "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "chain/ffmask"}}}
    wait(post("/prompt", {"prompt": wm})["prompt_id"])
    mp = max(glob.glob(SH + r"\output\chain\ffmask_*.png"), key=os.path.getmtime)
    return Image.open(mp).convert("L").resize(img.size, Image.LANCZOS)


def kontext(crop, size, prompt, tag, seed=7):
    name = "ff_%s.png" % tag; crop.resize(size, Image.LANCZOS).save(IN + "\\" + name)
    wf = json.load(open(r"C:\Users\Internet\Desktop\TEST COMFYUI\scripts\kontext_refine_still.json", encoding="utf-8-sig"))
    wf["4"]["inputs"]["image"] = name; wf["5"]["inputs"].update(width=size[0], height=size[1])
    wf["16"]["inputs"]["seed"] = seed; wf["18"]["inputs"]["filename_prefix"] = "retouch/" + tag; wf["10"]["inputs"]["text"] = prompt
    wait(post("/prompt", {"prompt": wf, "client_id": "ff"})["prompt_id"])
    f = max(glob.glob(SH + r"\output\retouch\%s_*.png" % tag), key=os.path.getmtime)
    return Image.open(f).convert("RGB").resize(crop.size, Image.LANCZOS)


def hb(x, L):
    k = torch.ones(x.shape[1], 1, 1, L) / L
    return F.conv2d(F.pad(x, (L // 2, L - 1 - L // 2, 0, 0), mode="replicate"), k, groups=x.shape[1])


def panblur(img, car):
    Wd, Ht = img.size; p = torch.from_numpy(np.asarray(img).astype(np.float32) / 255).permute(2, 0, 1)[None]
    c = torch.from_numpy(np.asarray(car).astype(np.float32) / 255)[None, None]
    w = 1 - F.max_pool2d((c > 0.5).float(), 9, 1, 4)
    bl = [torch.where(hb(w, L) > 0.08, hb(p * w, L) / hb(w, L).clamp(min=1e-4), p) for L in LS]
    y = torch.linspace(0, 1, Ht).view(1, 1, Ht, 1).expand(1, 1, Ht, Wd)
    wm_ = ((y - 0.10) / 0.18).clamp(0, 1); wn_ = ((y - 0.32) / 0.20).clamp(0, 1)
    bg = bl[0] * (1 - wm_) + bl[1] * wm_; bg = bg * (1 - wn_) + bl[2] * wn_
    ER = int(_os.environ.get("FF_ERODE", "3"))   # shrink the car mask so the contour ring (model halo) is replaced by clean background
    ce = 1 - F.max_pool2d(1 - (c > 0.5).float(), 2 * ER + 1, 1, ER) if ER > 0 else c
    soft = F.avg_pool2d(ce, 3, 1, 1); res = p * soft + bg * (1 - soft)
    return Image.fromarray((res[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + .5).astype(np.uint8))



from PIL import ImageDraw
def skydeep(res, car_m):
    # SKYDEEP: deep cobalt blue sky + contrasty clouds (BMW reference); only the upper sky region, white clouds keep their whiteness
    a = np.asarray(res).astype(np.float32) / 255; Ht, Wd = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a.mean(2)
    yy = np.linspace(0, 1, Ht)[:, None] * np.ones((1, Wd), np.float32); xx = np.linspace(0, 1, Wd)[None, :] * np.ones((Ht, 1), np.float32)
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-4)
    skyish = ((b > r * 0.97) & (b > g * 0.95) & (lum > 0.40)).astype(np.float32)
    zone = np.clip((0.62 - yy) / 0.08, 0, 1)
    sm = np.asarray(Image.fromarray((skyish * zone * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32) / 255
    blue = np.clip(sat * 3.0, 0, 1) * sm                       # blue sky (not white cloud)
    deep = (lum[..., None] ** 1.35) * np.array([0.52, 0.80, 1.28], np.float32) * 1.05
    out = a * (1 - 0.65 * blue[..., None]) + deep * 0.65 * blue[..., None]
    cl = sm * (1 - blue)                                        # clouds: more contrast (darker undersides, bright tops)
    lum2 = out.mean(2, keepdims=True); c2 = np.clip(0.5 + (lum2 - 0.55) * 1.45 + 0.05, 0, 1)
    out = out * (1 - 0.8 * cl[..., None]) + out * (c2 / np.maximum(lum2, 1e-3)) * 0.8 * cl[..., None]
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))


def skyfix(res):
    # SKYFIX: remove the green cast from clouds / sky and add the reference gradient (darker saturated blue at the top, lighter at the horizon)
    a = np.asarray(res).astype(np.float32) / 255; Ht, Wd = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]; lum = a.mean(2)
    yy = np.linspace(0, 1, Ht)[:, None] * np.ones((1, Wd), np.float32)
    xx = np.linspace(0, 1, Wd)[None, :] * np.ones((Ht, 1), np.float32)
    skyz = np.clip(((0.60 + 0.02 * xx) - yy) / 0.10, 0, 1)                      # above the hills
    notveg = np.clip((b * 1.30 - g) / 0.05, 0, 1) * np.clip((lum - 0.40) / 0.10, 0, 1)   # sky/cloud pixels (green not dominant)
    m = np.asarray(Image.fromarray((skyz * notveg * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32) / 255
    cast = np.clip(g - (r + b) / 2, 0, 1)
    g2 = g - 1.0 * cast * m
    a = np.stack([r, g2, b], -1)
    blue = np.clip(((b - np.maximum(r, g2)) * 4.0), 0, 1) * m                    # blue sky pixels only (clouds stay white)
    t = np.clip(1.0 - yy / 0.34, 0, 1) ** 1.1
    k = (blue * t)[..., None]
    a = a * (1 - 0.30 * k) * (1 + k * np.array([-0.12, -0.02, 0.10], np.float32))
    return Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8))


def haze(res):  # HAZE
    # atmospheric perspective like the BMW photos: sunlit light-green hills, pale blue haze growing with distance
    a = np.asarray(res).astype(np.float32) / 255; Ht, Wd = a.shape[:2]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = np.clip((g - np.maximum(r, b) * 1.0) * 8 + 0.15, 0, 1) * (g > b * 0.9)
    dark = np.clip((0.82 - a.mean(2)) * 6, 0, 1)
    yy = np.linspace(0, 1, Ht)[:, None] * np.ones((1, Wd), np.float32); xx = np.linspace(0, 1, Wd)[None, :] * np.ones((Ht, 1), np.float32)
    zone = np.clip(((0.55 + 0.02 * xx) - yy) / 0.10, 0, 1)
    hill = np.asarray(Image.fromarray((np.clip(green * dark * zone, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    lum = a.mean(2, keepdims=True)
    # 1) sunlit light green: lift brightness and saturation on the hills
    hk = hill[..., None]
    lit = np.clip((lum + (a - lum) * 1.7) * np.array([1.03, 1.12, 0.86], np.float32) * 1.28 + 0.02, 0, 1)
    a = a * (1 - hk * 0.75) + lit * hk * 0.75
    a[..., 2] = a[..., 2] * (1 - 0.30 * hk[..., 0])
    # 2) blue haze, stronger far (higher on screen / right); very dark pixels (trees) keep their own dark green
    far = np.clip(1.0 - yy / 0.50, 0, 1) * 0.85 + 0.30 * xx + 0.25
    tree = np.clip((0.20 - a.mean(2)) / 0.10, 0, 1)
    k = np.clip(hill * far * (1 - 0.55 * tree), 0, 0.92)[..., None]
    hc = np.array([0.70, 0.80, 0.90], np.float32); lum = a.mean(2, keepdims=True); flat = lum + (a - lum) * 0.70
    out = a * (1 - k) + (flat * 0.45 + hc * 0.55 + 0.04) * k
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
raw = Image.open(sys.argv[1]).convert("RGB"); out = sys.argv[2]
m = carmask(raw)
def region(box, feather=9):
    r = Image.new("L", raw.size, 0); ImageDraw.Draw(r).rectangle(box, fill=255)
    r = Image.fromarray(np.minimum(np.asarray(r), np.asarray(m.filter(ImageFilter.MaxFilter(25)))))
    return r.filter(ImageFilter.GaussianBlur(feather))
def retouch(img, box, scale, prompt, tag, feather=9):
    w = int(round((box[2] - box[0]) * scale / 16)) * 16; h = int(round((box[3] - box[1]) * scale / 16)) * 16
    patch = kontext(img.crop(box), (w, h), prompt, tag)
    full = img.copy(); full.paste(patch, box[:2])
    return Image.composite(full, img, region(box, feather))
KEEP = "Keep the car shape, the red nose cone and red bodywork, the driver, the tyres, the shadows, the camera angle and everything else exactly the same."
xs = np.nonzero(np.asarray(m).max(0) > 128)[0]; ys = np.nonzero(np.asarray(m).max(1) > 128)[0]
CB = (int(max(xs.min() - 40, 0)), int(max(ys.min() - 40, 0)), int(min(xs.max() + 40, raw.width)), int(min(ys.max() + 40, raw.height)))
im = retouch(raw, CB, 1.6, "Remove every letter, number, logo, sticker, decal and marking from the car so the bodywork is perfectly smooth uniform glossy red paint. Keep the driver, helmet, halo, tyres, rims, wings, shadows, camera angle and everything else exactly the same.", "ffclean", 12)
# BLACKFIX: any reddish pixel inside wing / halo boxes becomes carbon black (keeps luminance texture)
def blackfix(img, boxes, feather=6):
    a = np.asarray(img).astype(np.float32) / 255; r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = np.clip((r - np.maximum(g, b) * 1.15) * 6.0, 0, 1)
    reg = Image.new("L", img.size, 0); d = ImageDraw.Draw(reg)
    for bx in boxes: d.rectangle(bx, fill=255)
    reg = np.asarray(reg.filter(ImageFilter.GaussianBlur(feather))).astype(np.float32) / 255
    w = (red * reg * (np.asarray(m.filter(ImageFilter.MaxFilter(9))).astype(np.float32) / 255))[..., None]
    lum = (0.3 * r + 0.59 * g + 0.11 * b)[..., None]
    dark = np.repeat(np.clip(lum * 0.55, 0.02, 0.22), 3, axis=2) * np.array([1.0, 1.0, 1.06])
    return Image.fromarray((np.clip(a * (1 - w) + dark * w, 0, 1) * 255 + .5).astype(np.uint8))

PARTS = _os.environ["FF_PARTS"]            # path of the Blender part-ID render (1920x1080) for this frame
pm = np.asarray(Image.open(PARTS).convert("RGB").resize(raw.size, Image.LANCZOS)).astype(np.float32) / 255
carm = np.asarray(m.filter(ImageFilter.MaxFilter(9))).astype(np.float32) / 255
carm_t = np.asarray(m.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255   # tight mask: no black bleed onto the asphalt
def pmask(ch, others, grow=3, feather=2.0):
    v = (pm[..., ch] - pm[..., others].max(-1) > 0.35).astype(np.uint8) * 255 if others else (pm[..., ch] > 0.5).astype(np.uint8) * 255
    im_ = Image.fromarray(v).filter(ImageFilter.MaxFilter(grow * 2 + 1)).filter(ImageFilter.GaussianBlur(feather))
    return np.asarray(im_).astype(np.float32) / 255 * (carm_t if ch in (1, 2) else carm)
wing = pmask(2, [0, 1], grow=2, feather=3.0); halo = pmask(1, [0, 2], grow=2, feather=3.0); paint = pmask(0, [1, 2], grow=1, feather=1.5)
a_ = np.asarray(im).astype(np.float32) / 255; r_, g_, b_ = a_[..., 0], a_[..., 1], a_[..., 2]
lum = 0.3 * r_ + 0.59 * g_ + 0.11 * b_
carbon = np.clip(lum ** 1.5 * 0.75, 0.015, 0.30)[..., None] * np.array([1.0, 1.0, 1.05])
halo = halo * np.clip((0.40 - lum) / 0.14, 0, 1)   # only where already dark: mask misalignment must not smudge the red body
w = np.maximum(wing, halo)[..., None]
a_ = a_ * (1 - w) + carbon * w
# FRINGE: red edge left on the wing/halo border -> carbon, only where it is red (no black bleed on asphalt)
def _wide(ch, others):
    v = (pm[..., ch] - pm[..., others].max(-1) > 0.35).astype(np.uint8) * 255
    return np.asarray(Image.fromarray(v).filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(2.0))).astype(np.float32) / 255 * carm
wide = np.maximum(_wide(2, [0, 1]), _wide(1, [0, 2]) * np.clip((0.40 - lum) / 0.14, 0, 1))
fr = (np.clip((a_[..., 0] - np.maximum(a_[..., 1], a_[..., 2]) * 1.12) * 6, 0, 1) * wide)[..., None]
a_ = a_ * (1 - fr) + carbon * fr
# FRINGE2: red fringe on mirror and halo/roll-hoop borders (boxes in 1536x896 coords): non-paint red -> carbon
_pt = ((pm[..., 0] - pm[..., [1, 2]].max(-1)) > 0.35).astype(np.uint8) * 255
_pt = np.asarray(Image.fromarray(_pt).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255
_bx = np.zeros(_pt.shape, np.float32)
for (y0, y1, x0, x1) in ((430, 505, 640, 745), (455, 545, 870, 975)): _bx[y0:y1, x0:x1] = 1
_bx = np.asarray(Image.fromarray((_bx * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
_red = np.clip((a_[..., 0] - np.maximum(a_[..., 1], a_[..., 2]) * 1.10) * 5, 0, 1)
f2 = (_red * (1 - _pt) * _bx * carm)[..., None] * (0.0 if _os.environ.get("FF_NOFR2") else 1.0)
a_ = a_ * (1 - f2) + carbon * f2
# COCKPIT: non-paint parts (helmet, cockpit, floor) must not stay red around the driver
oth = (pm.max(-1) < 0.25).astype(np.uint8) * 255
oth = np.asarray(Image.fromarray(oth).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32) / 255 * carm
bx = np.zeros(oth.shape, np.float32); bx[455:525, 800:905] = 1; bx[675:750, 640:770] = 1
redn = np.clip((a_[..., 0] - np.maximum(a_[..., 1], a_[..., 2]) * 1.1) * 5, 0, 1)
wc = (oth * bx * redn)[..., None] * (0.0 if _os.environ.get("FF_NOCOCK") else 1.0)
l0 = (0.3 * a_[..., 0] + 0.59 * a_[..., 1] + 0.11 * a_[..., 2])[..., None]
a_ = a_ * (1 - wc) + np.clip(l0 * 0.5, 0.02, 0.25) * np.array([1.0, 1.0, 1.05]) * wc
# body paint: lift black / grey fade patches back to glossy red, keep bright reflections
mx_, mn_ = a_.max(-1), a_.min(-1); sat_ = (mx_ - mn_) / np.maximum(mx_, 1e-4); l2 = (0.3 * a_[..., 0] + 0.59 * a_[..., 1] + 0.11 * a_[..., 2])
fade = np.clip((0.45 - sat_) / 0.25, 0, 1) * np.clip((0.55 - l2) / 0.25, 0, 1) * paint
red = np.clip((l2 * 1.5 + 0.10), 0, 1)[..., None] * np.array([0.95, 0.10, 0.08])
pass
im = Image.fromarray((np.clip(a_, 0, 1) * 255 + .5).astype(np.uint8))
im.save(out.replace(".png", "_clean.png"))
res = panblur(im, m.filter(ImageFilter.GaussianBlur(1.5))).resize((1280, 768), Image.LANCZOS)
# ASPHALT: transfer rubber marks + grain from a real asphalt photo (high-pass, luminance only), motion-blurred along travel
def asphalt(res, cm):
    ref = Image.open(r"C:\Users\Internet\Desktop\TEST COMFYUI\ref\asphalt2.webp").convert("L"); rw, rh = ref.size
    ref = ref.crop((int(rw * 0.35), int(rh * 0.62), rw, rh)).resize(res.size, Image.LANCZOS)
    g = np.asarray(ref.filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255; gb = np.asarray(ref.filter(ImageFilter.GaussianBlur(40))).astype(np.float32) / 255
    hp = (g - gb); hp = hp / (np.abs(hp).std() + 1e-4)
    hp = torch.from_numpy(hp)[None, None]; hp = hb(hp, 30)[0, 0].numpy() * 1.6
    a = np.asarray(res).astype(np.float32) / 255; H_, W_ = a.shape[:2]
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-4); lum = a.mean(2)
    yy = np.linspace(0, 1, H_)[:, None]
    gm = ((sat < 0.40) & (lum < 0.40) & (lum > 0.02)).astype(np.uint8) * 255
    gm = np.asarray(Image.fromarray(gm).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    cmm = 1 - np.asarray(cm.resize(res.size).filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    w = gm * np.clip((yy - 0.38) / 0.12, 0, 1) * cmm
    amp = 0.05
    out = a * (1 + (hp * amp * w)[..., None])
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
# RUBBER: subtle procedural tyre marks along the direction of travel (soft, broken, low contrast)
def rubber(res, cm):
    import random
    rnd = random.Random(5); Wd, Ht = res.size
    cv = Image.new("L", (Wd, Ht), 0); d = ImageDraw.Draw(cv)
    for k in range(26):
        y0 = rnd.uniform(0.28, 1.25) * Ht; sl = 0.30 * Ht / Wd * rnd.uniform(0.92, 1.12); ph = rnd.uniform(0, 6); am = rnd.uniform(4, 16)
        wd = max(2, int(5 + 14 * (y0 / Ht) * rnd.uniform(0.6, 1.2))); al = rnd.uniform(40, 120)
        x = -20; pts = []
        while x < Wd + 20:
            pts.append((x, y0 + sl * x + am * np.sin(x / Wd * 3.0 + ph))); x += 12
        i = 0
        while i < len(pts) - 1:
            n = rnd.randint(6, 40)
            if rnd.random() < 0.7: d.line(pts[i:i + n + 1], fill=int(al * rnd.uniform(0.5, 1.0)), width=wd)
            i += n + rnd.randint(2, 14)
    cv = cv.filter(ImageFilter.GaussianBlur(3.0))
    mk = np.asarray(cv).astype(np.float32) / 255
    a = np.asarray(res).astype(np.float32) / 255
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-4); lum = a.mean(2)
    gm = ((sat < 0.45) & (lum < 0.42) & (lum > 0.02)).astype(np.uint8) * 255
    gm = np.asarray(Image.fromarray(gm).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    cmm = 1 - np.asarray(cm.resize(res.size).filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    yy = np.linspace(0, 1, Ht)[:, None]; xx = np.linspace(0, 1, Wd)[None, :]
    reg = np.clip((yy - (0.30 + 0.30 * xx) - 0.02) / 0.06, 0, 1)
    w = mk * gm * cmm * reg
    out = a * (1 - 0.55 * w[..., None])
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
# ASPHTEX: procedural asphalt grain + horizontal motion streaks on the ground (kills the plastic-flat look)
def asphtex(res, cm):
    rng = np.random.RandomState(3); Wd, Ht = res.size
    g = rng.randn(Ht, Wd).astype(np.float32)
    st = torch.from_numpy(rng.randn(Ht, Wd).astype(np.float32))[None, None]
    st = hb(st, 90)[0, 0].numpy(); st = st / (st.std() + 1e-4)
    gr = torch.from_numpy(g)[None, None]; gr = F.avg_pool2d(gr, 2, 1, 1)[0, 0][:Ht, :Wd].numpy(); gr = gr / (gr.std() + 1e-4)
    a = np.asarray(res).astype(np.float32) / 255
    mx, mn = a.max(2), a.min(2); sat = (mx - mn) / np.maximum(mx, 1e-4); lum = a.mean(2)
    gm = ((sat < 0.45) & (lum < 0.42) & (lum > 0.02)).astype(np.uint8) * 255
    gm = np.asarray(Image.fromarray(gm).filter(ImageFilter.MinFilter(7)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32) / 255
    cmm = 1 - np.asarray(cm.resize(res.size).filter(ImageFilter.MaxFilter(21)).filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255
    yy = np.linspace(0, 1, Ht)[:, None]; xx = np.linspace(0, 1, Wd)[None, :]
    reg = np.clip((yy - (0.30 + 0.30 * xx) - 0.02) / 0.06, 0, 1)
    w = gm * cmm * reg * (0.35 + 0.65 * yy)
    out = a * (1 + ((0.016 * st + 0.014 * gr) * w)[..., None] + (0.20 * gm * cmm * reg)[..., None])   # strong sun: brighter sunlit asphalt
    o8 = Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
    bl = np.asarray(o8.filter(ImageFilter.GaussianBlur(2.2))).astype(np.float32) / 255
    wsh = (gm * cmm * reg)[..., None]
    dl = ((out - bl).mean(2, keepdims=True)); out = np.clip(out + dl * 0.9 * wsh, 0, 1)   # sharpen only the asphalt
    return Image.fromarray((np.clip(out, 0, 1) * 255 + .5).astype(np.uint8))
res = asphtex(res, m)
if not _os.environ.get("FF_NOASPH"): res = rubber(res, m)
res = (grade(res, 1.12, 1.05) if _os.environ.get("FF_SIMPLE") else (grade(res, float(_os.environ.get("FF_SAT", "1.18")), float(_os.environ.get("FF_CON", "1.08"))) if _os.environ.get("FF_NOSKY") else sky(grade(res)))); res = haze(res) if not _os.environ.get("FF_NOHAZE") else res
res = skydeep(res, m) if _os.environ.get("FF_NOSKYDEEP", "0") != "1" else res
res = skyfix(res) if not _os.environ.get("FF_NOSKYFIX") else res
res.save(out); print("saved", out)
