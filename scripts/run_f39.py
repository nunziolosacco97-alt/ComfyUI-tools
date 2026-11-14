"""Frame 39: circuit environment layout (auto sharp, environment as soft massing) + automotive-photography mood prompt.
usage: python -I run_f39.py <tag> <start_frame> <pick_index> <blur_radius>"""
import av, glob, json, os, subprocess, sys, time, urllib.request
from PIL import Image, ImageFilter
PY = sys.executable
SH = r"C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared"; IN = SH + r"\input"; OUT = SH + r"\output\ltx"
SEM = os.environ.get("SEMDIR", r"C:\Users\Internet\Desktop\TEST COMFYUI\render\layout") + "\\sem_%04d.png"; B = "http://127.0.0.1:8188"
W, H, N = int(os.environ.get("LTX_W", "1536")), int(os.environ.get("LTX_H", "896")), 9
tag, S0, PICK, RAD = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
P = ("A cinematic magazine cover photograph of a Formula 1 car at full speed on a real race circuit, low wide-angle three-quarter front view from track level. "
     "A deep rich blue sky, dark saturated blue at the top fading to a lighter soft blue near the horizon, never green or turquoise, with soft white cumulus clouds with grey undersides, including large clouds floating higher in the sky with a band of clear blue sky between them and the distant hills, strong bright sunlight and crisp contrast fills the upper half of the frame. Sunlit vivid fresh green grassy hills with one single solid very dark green mass of dense forest forming a low continuous treeline along the distant ridge on the left side, no individual trees, no cypress, no isolated round trees or bushes, while the whole right half of the image is smooth open green meadow with absolutely no trees, no tree rows and no bushes, the farthest ridges fading into a light blue mist that blends them softly into the sky, open green meadows elsewhere, leaving most of the frame to the dramatic sky, with tyre barriers along the track and no fence. The car is tack sharp while the background is a detailed horizontal panning shot: crisp structure with directional horizontal motion streaks, the kerbs and asphalt streak sideways like a real panning photograph, never a soft lens blur. The car is painted in one single flat uniform vivid deep red with smooth glossy clear-coat and crisp reflections of the sky. "
     "The front wing, the rear wing with its endplates, the floor and the splitter are black carbon fibre, the wheels have plain black rims and smooth black rubber tyres. "
     "The driver wears a plain solid matte black helmet with a simple dark tinted visor. "
     "Cinematic cool blue colour grading with a very deep saturated blue sky, rich contrasty clouds, a strong sun that lights the asphalt and the car with crisp hard shadows, while the grass, hills and trees stay natural fresh green, like a premium automotive advertising photograph, high contrast, rich saturated colours, dramatic rim light, fine film grain, ultra realistic, high dynamic range.")
for f in glob.glob(OUT + "\\%s_*.png" % tag): os.remove(f)


# HMOTION: directional (horizontal) panning blur of the environment instead of an isotropic lens blur
import numpy as np, torch, torch.nn.functional as F
def hmotion(img, L):
    x = torch.from_numpy(np.asarray(img).astype(np.float32) / 255).permute(2, 0, 1)[None]
    k = torch.ones(3, 1, 1, L) / L
    y = F.conv2d(F.pad(x, (L // 2, L - 1 - L // 2, 0, 0), mode="replicate"), k, groups=3)
    return Image.fromarray((y[0].permute(1, 2, 0).clamp(0, 1).numpy() * 255 + .5).astype(np.uint8))


def post(p, d): return json.load(urllib.request.urlopen(urllib.request.Request(B + p, json.dumps(d).encode(), {"Content-Type": "application/json"}), timeout=60))


def carmask(img):
    img.save(IN + r"\f39_in.png")
    wm = {"1": {"class_type": "LoadBackgroundRemovalModel", "inputs": {"bg_removal_name": "birefnet.safetensors"}},
          "2": {"class_type": "LoadImage", "inputs": {"image": "f39_in.png"}},
          "3": {"class_type": "RemoveBackground", "inputs": {"bg_removal_model": ["1", 0], "image": ["2", 0]}},
          "4": {"class_type": "MaskToImage", "inputs": {"mask": ["3", 0]}},
          "5": {"class_type": "SaveImage", "inputs": {"images": ["4", 0], "filename_prefix": "chain/f39mask"}}}
    pid = post("/prompt", {"prompt": wm})["prompt_id"]
    while pid not in json.load(urllib.request.urlopen(B + "/history/" + pid, timeout=30)): time.sleep(1)
    return Image.open(max(glob.glob(SH + r"\output\chain\f39mask_*.png"), key=os.path.getmtime)).convert("L").resize(img.size, Image.LANCZOS)


c = av.open(IN + "\\layout_%s.mp4" % tag, "w"); st = c.add_stream("libx264", rate=24); st.width, st.height, st.pix_fmt = W, H, "yuv420p"; st.options = {"crf": "8"}
for k, i in enumerate(range(S0, S0 + N)):
    im = Image.open(SEM % i).convert("RGB").resize((W, H), Image.LANCZOS)
    m = carmask(im).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(4))
    # GROUNDSHARP: low blur on the ground (asphalt, kerbs), strong blur above the kerb line (stands, walls)
    import numpy as np
    xx = np.linspace(0, 1, W)[None, :]; yy = np.linspace(0, 1, H)[:, None]
    t = yy - (0.25 + 0.30 * xx)
    ramp = Image.fromarray((np.clip((t + 0.04) / 0.10, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
    far = hmotion(im, int(os.environ.get("L_FAR", "16"))).filter(ImageFilter.GaussianBlur(1.5)); near = hmotion(im, int(os.environ.get("L_NEAR", "40")))
    env = Image.composite(near, far, ramp)
    out = Image.composite(im, env, m)
    if k == PICK - 1: out.save(r"C:\Users\Internet\Desktop\TEST COMFYUI\frames\%s_layout.png" % tag)
    for p in st.encode(av.VideoFrame.from_image(out)): c.mux(p)
for p in st.encode(): c.mux(p)
c.close()
subprocess.run([PY, "-I", "run_ltx_l2r.py", "--style", "0", "--layout", "layout_%s.mp4" % tag, "--w", str(W), "--h", str(H), "--n", str(N), "--seed", __import__("os").environ.get("LTX_SEED", "7"), "--prompt", P, "--tag", tag])
Image.open(OUT + "\\%s_%05d_.png" % (tag, PICK)).save(r"C:\Users\Internet\Desktop\TEST COMFYUI\frames\%s_raw_%d.png" % (tag, PICK)); print("DONE")
