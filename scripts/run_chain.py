"""Full chain, frames 1-180: LTX 33-frame blocks at 1536x896 (layout from Test_sem4) -> crossfade -> BiRefNet car mask -> panning blur on background -> 1280x768 frames in Desktop\Test_ltx\s3b_full.
python -I run_chain.py   (resumable: skips blocks whose frames exist, skips finished output frames)"""
import av, glob, json, os, shutil, subprocess, sys, time, urllib.request
import numpy as np, torch, torch.nn.functional as F
from PIL import Image
PY = sys.executable
SEM = r"C:\Users\Internet\Desktop\TEST COMFYUI\render\layout\sem_%04d.png"
SH = r"C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared"; IN = SH + r"\input"; OUT = SH + r"\output\ltx"
FIN = r"C:\Users\Internet\Desktop\TEST COMFYUI\render\video\s3b_full"; RAW = r"C:\Users\Internet\Desktop\TEST COMFYUI\render\video\s3b_raw"
B = "http://127.0.0.1:8188"
W, H, N, TOTAL = 1536, 896, 33, 180
LS = [12, 26, 55]
P = ("A cinematic photograph of a real Formula 1 race car at full speed on a city street circuit at golden hour sunset, three-quarter front view, shot on a 400mm anamorphic telephoto lens at 1/60 second shutter while panning with the car, shallow depth of field. "
 "The car is tack sharp, while everything behind it is smeared by horizontal panning motion blur, soft horizontal streaks: dense crowds of spectators in colourful clothes packed in the stepped grandstands, colourful advertising hoardings along the barrier, the catch fence, the lamp posts, the footbridge and tall modern skyscrapers with reflective facades and rich window detail. "
 "The track is dark worn racing asphalt with thick black rubber tyre marks and skid streaks clearly visible along the polished racing line, with painted white edge lines and red and white kerbs. "
 "The car is painted in one single flat uniform deep red, smooth glossy clear-coat, with crisp specular highlights and warm orange sunset reflections running along the smooth bodywork. "
 "The front wing, the rear wing with both of its endplates, the floor and the splitter are black carbon fibre, entirely black, while only the nose, the engine cover and the sidepods are painted red. The wheels have plain black rims and smooth black rubber tyres. "
 "The open cockpit has a slim black halo arch above a plain solid matte black helmet with a simple dark tinted visor. "
 "Strong warm low backlit golden sun, long hard shadows on the asphalt, subtle atmospheric haze and sun flare, vivid saturated colours, a glowing orange and magenta sunset sky, warm golden light flooding the whole scene, rich cinematic colour grading, fine film grain. "
 "Professional motorsport cinema footage, ultra realistic, high dynamic range.")
def plan(n):
    s, starts = 1, []
    while True:
        starts.append(s)
        if s + n - 1 >= TOTAL: break
        s += n - 7
        if s + n - 1 > TOTAL: s = TOTAL - n + 1
    return starts
def layout(name, s, n):
    c = av.open(IN + "\\" + name, "w"); st = c.add_stream("libx264", rate=24); st.width, st.height, st.pix_fmt = W, H, "yuv420p"; st.options = {"crf": "8"}
    for i in range(s, s + n):
        for p in st.encode(av.VideoFrame.from_image(Image.open(SEM % i).convert("RGB").resize((W, H), Image.LANCZOS))): c.mux(p)
    for p in st.encode(): c.mux(p)
    c.close()
starts = plan(N); print("blocks", starts, flush=True); tags = []
for k, s in enumerate(starts, 1):
    tag = "s8_%d" % k
    if len(glob.glob(OUT + "\%s_*.png" % tag)) != N:
        for f in glob.glob(OUT + "\%s_*.png" % tag): os.remove(f)
        for attempt in range(3):
            layout("layout_%s.mp4" % tag, s, N)
            subprocess.run([PY, "-I", "run_ltx_l2r.py", "--style", "0", "--layout", "layout_%s.mp4" % tag, "--w", str(W), "--h", str(H), "--n", str(N), "--seed", "7", "--prompt", P, "--tag", tag])
            if len(glob.glob(OUT + "\%s_*.png" % tag)) == N: break
            print("block failed", tag, flush=True)
            for f in glob.glob(OUT + "\%s_*.png" % tag): os.remove(f)
            time.sleep(120)
        else: sys.exit("block %s failed 3 times" % tag)
    tags.append(tag); print("block ok", tag, flush=True)
os.makedirs(FIN, exist_ok=True); os.makedirs(RAW, exist_ok=True)
def get(i, f): return Image.open(OUT + "\%s_%05d_.png" % (tags[i], f - starts[i] + 1)).convert("RGB")
def post(p, d): return json.load(urllib.request.urlopen(urllib.request.Request(B + p, json.dumps(d).encode(), {"Content-Type": "application/json"}), timeout=60))
def carmask(img):
    img.save(IN + r"\ch_in.png")
    wm = {"1": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
          "2": {"class_type": "LoadImage", "inputs": {"image": "ch_in.png"}},
          "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["1", 0], "image": ["2", 0]}},
          "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "chain/mask"}}}
    pid = post("/prompt", {"prompt": wm})["prompt_id"]
    while pid not in json.load(urllib.request.urlopen(B + "/history/" + pid, timeout=30)): time.sleep(1)
    mp = max(glob.glob(SH + r"\output\chain\mask_*.png"), key=os.path.getmtime)
    return torch.from_numpy(np.asarray(Image.open(mp).convert("L").resize(img.size, Image.LANCZOS)).astype(np.float32) / 255)[None, None]
def hb(x, L):
    k = torch.ones(x.shape[1], 1, 1, L) / L
    return F.conv2d(F.pad(x, (L // 2, L - 1 - L // 2, 0, 0), mode="replicate"), k, groups=x.shape[1])
def panblur(img, car):
    Wd, Ht = img.size; p = torch.from_numpy(np.asarray(img).astype(np.float32) / 255).permute(2, 0, 1)[None]
    w = 1 - F.max_pool2d((car > 0.5).float(), 9, 1, 4)
    bl = [hb(p * w, L) / hb(w, L).clamp(min=1e-4) for L in LS]
    y = torch.linspace(0, 1, Ht).view(1, 1, Ht, 1).expand(1, 1, Ht, Wd)
    wm_ = ((y - 0.10) / 0.18).clamp(0, 1); wn_ = ((y - 0.32) / 0.20).clamp(0, 1)
    bg = bl[0] * (1 - wm_) + bl[1] * wm_; bg = bg * (1 - wn_) + bl[2] * wn_
    soft = F.avg_pool2d(car, 5, 1, 2); res = p * soft + bg * (1 - soft)
    return Image.fromarray((res[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + .5).astype(np.uint8))
for f in range(1, TOTAL + 1):
    out = FIN + "\f%04d.png" % f
    if os.path.exists(out): continue
    cov = [i for i, s in enumerate(starts) if s <= f <= s + N - 1]
    if len(cov) == 1: im = get(cov[0], f)
    else:
        a, b = cov[0], cov[-1]; t = (f - starts[b] + 1) / float(starts[a] + N - starts[b] + 1)
        im = Image.blend(get(a, f), get(b, f), t)
    im.save(RAW + "\f%04d.png" % f)
    res = panblur(im, carmask(im)).resize((1280, 768), Image.LANCZOS); res.save(out)
    if f % 10 == 0: print("frame", f, flush=True)
print("DONE", flush=True)
