"""LTX-2.5 Layout-to-Render test. python -I run_ltx_l2r.py [--seed N] [--style 1] [--ic 1.0] [--tag name]"""
import json, sys, time, urllib.request

BASE = "http://127.0.0.1:8188"
a = sys.argv[1:]
def opt(n, d, c=str):
    return c(a[a.index(n) + 1]) if n in a else d
seed = opt("--seed", 42, int); use_style = opt("--style", 1, int); ic = opt("--ic", 1.0, float); tag = opt("--tag", "ltx")
W, H, N = opt("--w", 768, int), opt("--h", 448, int), opt("--n", 65, int)
LAY = opt("--layout", "layout_%d_%d.mp4" % (N, W))

PROMPT_DEFAULT = ("A photorealistic Formula 1 racing car, Ferrari red and white livery with number 44, panning shot "
          "at speed on a real asphalt track, sharp car with strong horizontal motion blur on the grass and background, "
          "natural sunlight, soft realistic shadow under the car, realistic tyres and carbon fibre, "
          "professional motorsport photography, cinematic, high detail.")
PROMPT = opt("--prompt", PROMPT_DEFAULT)
NEG = "text, letters, numbers, logos, sponsor decals, lettering, writing, graphics, cartoon, cgi, plastic, low quality, jitter, flicker, deformed car, text, watermark, extra wheels"

g = {
 "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "ltx-2.5-22b-distilled-Q4_K_M.gguf"}},
 "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "ltx-2.5-22b-ic-lora-layout-to-render-1.0.safetensors", "strength_model": opt("--lora", 1.0, float)}},
 "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "gemma4-12b-with-proj-ltx-2.5-bf16.safetensors", "type": "ltxv", "device": "default"}},
 "4": {"class_type": "VAELoader", "inputs": {"vae_name": "ltx-2.5-video-vae-conv-bf16.safetensors"}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": PROMPT}},
 "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["3", 0], "text": NEG}},
 "7": {"class_type": "LTXVConditioning", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "frame_rate": 24.0}},
 "8": {"class_type": "LoadVideo", "inputs": {"file": LAY}},
 "9": {"class_type": "GetVideoComponents", "inputs": {"video": ["8", 0]}},
 "10": {"class_type": "EmptyLTXVLatentVideo", "inputs": {"width": W, "height": H, "length": N, "batch_size": 1}},
 "11": {"class_type": "GetICLoRAParameters", "inputs": {"iclora_model": ["2", 0]}},
 "12": {"class_type": "LTXVAddGuide", "inputs": {"positive": ["7", 0], "negative": ["7", 1], "vae": ["4", 0], "latent": ["10", 0],
        "image": ["9", 0], "frame_idx": 0, "strength": ic, "iclora_parameters": ["11", 0]}},
 "13": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
 "14": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
 "15": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0"}},
 "16": {"class_type": "CFGGuider", "inputs": {"model": ["2", 0], "positive": ["12", 0], "negative": ["12", 1], "cfg": 1.0}},
 "17": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["13", 0], "guider": ["16", 0], "sampler": ["14", 0], "sigmas": ["15", 0], "latent_image": ["12", 2]}},
 "18": {"class_type": "LTXVCropGuides", "inputs": {"positive": ["12", 0], "negative": ["12", 1], "latent": ["17", 0]}},
 "19": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["18", 2], "vae": ["4", 0], "tile_size": 512, "overlap": 64, "temporal_size": 32, "temporal_overlap": 8}},
 "20": {"class_type": "SaveImage", "inputs": {"images": ["19", 0], "filename_prefix": "ltx/%s" % tag}},
}
if use_style:
    g["21"] = {"class_type": "LoadImage", "inputs": {"image": opt("--styleimg", "style_85.png")}}
    g["22"] = {"class_type": "LTXVImgToVideoInplace", "inputs": {"vae": ["4", 0], "image": ["21", 0], "latent": ["10", 0], "strength": 0.9, "bypass": False}}
    g["12"]["inputs"]["latent"] = ["22", 0]


def post(p, d):
    r = urllib.request.Request(BASE + p, json.dumps(d).encode(), {"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(r, timeout=60))
    except urllib.error.HTTPError as e:
        print(e.read().decode()[:3000]); sys.exit(1)

pid = post("/prompt", {"prompt": g, "client_id": "ltx"})["prompt_id"]
t0 = time.time(); print("queued", pid, flush=True)
while True:
    h = json.load(urllib.request.urlopen(BASE + "/history/" + pid, timeout=30))
    if pid in h:
        st = h[pid]["status"]
        print(st["status_str"], "%.0fs" % (time.time() - t0))
        if st["status_str"] != "success":
            for m in st["messages"]:
                if m[0] == "execution_error": print(json.dumps(m[1])[:2500])
        break
    time.sleep(5)
