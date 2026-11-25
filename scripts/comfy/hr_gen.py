"""4K refinement inside the model graph (no post upscaler).  usage: python -I hr_gen.py MODEL SCENE VIEW MODE [denoise] [seed]
MODEL zimage|flux|moss|ph3|h3   SCENE trk|hum   VIEW A|B|C or 1..4   MODE g (global 2nd pass at 3840x2304) | t (overlapping tiles)
The original render (results/<scene>_<model>_<view>_s<seed>_nf_0.png) is only the starting latent; the final pixels are sampled by the same model at 4K (or per 4K tile).
Conditioning (depth / clay / colour) is resized with lanczos to the working size, never taken from another model."""
import sys, os, json, subprocess, math, shutil, time
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import SH, RES, run
model, SCENE, VIEW, MODE = sys.argv[1:5]
DEN = float(sys.argv[5]) if len(sys.argv) > 5 else 0.35
seed = int(sys.argv[6]) if len(sys.argv) > 6 else 101
HERE = os.path.dirname(os.path.abspath(__file__)); PY = sys.executable
INF = "mcl13" if SCENE == "city" else ("trk_" if SCENE == "trk" else "hum_") + VIEW   # city = McLaren with the woman walking past (inputs mcl13)
FW, FH = 3840, 2304
CITY_ORIG = {"zimage": "zimage_v10_depth_s%d_d0.8_e0.8_l0_0.png", "flux": "flux2dev_v10A_turbo_s%d_0.png", "moss": "moss_v10_depth_color_end1_s%d_0.png",
             "ph3": "ph3image_v10A_s%d_0.png", "h3": "h3image_v7B_2ref_s%d_0.png"}   # city scene: v10 recipes; H3 = 2nd ref is Blender beauty_color (no other model's output)
CITY_DUMP = {"zimage": "zimage_v10_depth_s%d_d0.8_e0.8_l0", "flux": "flux2dev_v10A_turbo_s%d", "moss": "moss_v10_depth_color_end1_s%d", "ph3": "ph3image_v10A_s%d", "h3": "h3image_v10A_2ref_s%d"}
ORIG = os.path.join(RES, (CITY_ORIG[model] % seed) if SCENE == "city" else "%s_%s_%s_s%d_nf_0.png" % (SCENE, model, VIEW, seed))
TAGN = "d%02d" % round(DEN * 100)
OUTN = "hr%s_%s_%s_%s_s%d_%s" % (MODE, SCENE, model, VIEW, seed, TAGN)
os.makedirs(os.path.join(RES, "HR"), exist_ok=True)
# 1) original graph of this model/view (dumped, not run)
dd = os.path.join(HERE, "dump"); os.makedirs(dd, exist_ok=True)
if SCENE == "city":   # graphs dumped beforehand from the *_v10.py scripts with INF=mcl13 DUMP_DIR=dump/city
    G0 = json.load(open(os.path.join(dd, "city", (CITY_DUMP[model] % seed) + ".json"), encoding="utf-8"))
else:
    env = dict(os.environ, DUMP_DIR=dd, TAG="_nf")
    subprocess.run([PY, "-I", os.path.join(HERE, "trk_gen.py" if SCENE == "trk" else "hum_gen.py"), model, VIEW, str(seed)], env=env, check=True, capture_output=True)
    G0 = json.load(open(os.path.join(dd, "%s_%s_%s_s%d_nf.json" % (SCENE, model, VIEW, seed)), encoding="utf-8"))
VAE = {"zimage": "3", "moss": "4", "flux": "10", "ph3": "3", "h3": "3"}[model]
DEC = {"zimage": "12", "moss": "9", "flux": "8", "ph3": "15", "h3": "9"}[model]
SAVE = {"zimage": "13", "moss": "85", "flux": "9", "ph3": "16", "h3": "10"}[model]
SRC = os.path.join(SH, "input", INF)
IMGS = {k: Image.open(os.path.join(SRC, k + ".png")).convert("RGB") for k in ("beauty_clay", "beauty_color", "depth")}
INIT = Image.open(ORIG).convert("RGB")
UP = {k: v.resize((FW, FH), Image.LANCZOS) for k, v in IMGS.items()}; UP["init"] = INIT.resize((FW, FH), Image.LANCZOS)
STAGE = os.path.join(SH, "input", "hr_stage"); os.makedirs(STAGE, exist_ok=True)
SIG = {"ph3": {0.25: "0.810083, 0.528718, 0.0", 0.35: "0.881923, 0.810083, 0.528718, 0.0", 0.5: "0.951688, 0.925372, 0.881923, 0.810083, 0.528718, 0.0"}}

def build(files, W, H):
    """patch the dumped graph: working size WxH, input images renamed to files[k], start from files['init'] with partial denoise"""
    g = json.loads(json.dumps(G0))
    for n in g.values():
        i = n["inputs"]
        if n["class_type"] == "LoadImage":
            for k in ("beauty_clay", "beauty_color", "depth"):
                if i["image"].endswith("/" + k + ".png"): i["image"] = files[k]
    g["H1"] = {"class_type": "LoadImage", "inputs": {"image": files["init"]}}
    g["H2"] = {"class_type": "ImageScale", "inputs": {"image": ["H1", 0], "upscale_method": "lanczos", "width": W, "height": H, "crop": "disabled"}}
    g["H3"] = {"class_type": "VAEEncodeTiled", "inputs": {"pixels": ["H2", 0], "vae": [VAE, 0], "tile_size": 1024, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}}
    if model != "ph3": g[DEC] = {"class_type": "VAEDecodeTiled", "inputs": {"samples": g[DEC]["inputs"]["samples"], "vae": [VAE, 0], "tile_size": 1024, "overlap": 64, "temporal_size": 64, "temporal_overlap": 8}}
    def scaled(node, key, nid):
        g[nid] = {"class_type": "ImageScale", "inputs": {"image": [node, 0], "upscale_method": "lanczos", "width": W, "height": H, "crop": "disabled"}}
        return [nid, 0]
    if model == "zimage":
        del g["10"]; g["7"]["inputs"]["image"] = scaled("6", "image", "6s")
        g["11"]["inputs"].update(latent_image=["H3", 0], denoise=DEN)
    elif model == "moss":
        del g["54"]; g["53"]["inputs"]["depth_map"] = scaled("10", "", "10s"); g["53"]["inputs"]["color_map"] = scaled("11", "", "11s")
        g["20"]["inputs"]["latent_image"] = ["H3", 0]; g["22"]["inputs"]["denoise"] = DEN
    elif model == "flux":
        del g["47"]; g["48"]["inputs"].update(width=W, height=H)
        g["SS"] = {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["48", 0], "denoise": DEN}}
        g["13"]["inputs"].update(sigmas=["SS", 1], latent_image=["H3", 0])
    elif model == "ph3":
        g["9"]["inputs"].update(width=W, height=H)
        g["13"]["inputs"]["sigmas"] = SIG["ph3"][0.25 if DEN < 0.3 else 0.35 if DEN < 0.45 else 0.5]
        g["SA"] = {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["9", 1]}}      # P-H3 samples a video+audio latent: keep its empty audio part
        g["CA"] = {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["H3", 0], "audio_latent": ["SA", 1]}}
        g["14"]["inputs"]["latent_image"] = ["CA", 0]
    elif model == "h3":
        g["6"]["inputs"].update(width=W, height=H)
        g["8"]["inputs"].update(latent_image=["H3", 0], denoise=DEN)
    g[SAVE]["inputs"]["filename_prefix"] = "mcl/hr_" + OUTN
    return g

def stage(name, im):
    p = os.path.join(STAGE, "%s_%s.png" % (OUTN, name)); im.save(p); return "hr_stage/" + os.path.basename(p)

t0 = time.time()
if MODE == "g":
    files = {k: stage(k, UP[k]) for k in UP}
    # edit-style refs stay at their normal size (ImageScaleToTotalPixels inside the graph), so pass the original 1280x768 clay/colour for them
    if model in ("flux", "ph3", "h3"):
        files["beauty_clay"] = stage("clay0", IMGS["beauty_clay"]); files["beauty_color"] = stage("color0", IMGS["beauty_color"])
    outs = run(build(files, FW, FH), OUTN)
    shutil.copy(outs[0], os.path.join(RES, "HR", OUTN + ".png"))
else:
    TW, TH, OV = (1920, 1152, 384) if model == "h3" else (1280, 768, 192)
    xs = [int(round(i * (FW - TW) / max(1, math.ceil((FW - OV) / (TW - OV)) - 1))) for i in range(math.ceil((FW - OV) / (TW - OV)))]
    ys = [int(round(i * (FH - TH) / max(1, math.ceil((FH - OV) / (TH - OV)) - 1))) for i in range(math.ceil((FH - OV) / (TH - OV)))]
    acc = np.zeros((FH, FW, 3), np.float32); wsum = np.zeros((FH, FW, 1), np.float32)
    def ramp(n, lo, hi):
        w = np.ones(n, np.float32)
        if lo: w[:OV] = np.linspace(0.02, 1, OV)
        if hi: w[-OV:] = np.minimum(w[-OV:], np.linspace(1, 0.02, OV))
        return w
    for yi, y in enumerate(ys):
        for xi, x in enumerate(xs):
            files = {k: stage("t%d%d_%s" % (yi, xi, k), UP[k].crop((x, y, x + TW, y + TH))) for k in UP}
            outs = run(build(files, TW, TH), OUTN + "_t%d%d" % (yi, xi))
            t = np.asarray(Image.open(outs[0]).convert("RGB").resize((TW, TH), Image.LANCZOS), np.float32)
            w = (ramp(TH, yi > 0, yi < len(ys) - 1)[:, None] * ramp(TW, xi > 0, xi < len(xs) - 1)[None, :])[..., None]
            acc[y:y + TH, x:x + TW] += t * w; wsum[y:y + TH, x:x + TW] += w
    Image.fromarray(np.clip(acc / wsum, 0, 255).astype(np.uint8)).save(os.path.join(RES, "HR", OUTN + ".png"))
print("HRDONE", OUTN, "%.0fs" % (time.time() - t0))
