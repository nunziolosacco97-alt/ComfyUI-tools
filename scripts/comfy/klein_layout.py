"""Klein with layout boxes: the pedestrian and the car are tied to boxes (<obj_1>, <obj_2>) so the model redraws the dark mannequin as a real woman."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
import json, numpy as np
from PIL import Image
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; cfg = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
MC = os.path.dirname(HERE)
def bbox(name):
    m = np.asarray(Image.open(os.path.join(MC, "inputs", name)).convert("L")) > 128; ys, xs = np.where(m)
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min()), int(ys.max() - ys.min())
px, py_, pw, ph = bbox("mask_foreground.png"); cx_, cy_, cw, ch = bbox("car_mask.png")
boxes = [{"x": px, "y": py_, "width": pw, "height": ph, "metadata": {"type": "obj", "text": "", "desc": "a real woman with natural brown hair walking in profile, wearing a long dark wool coat, dark trousers and leather boots, photographic skin and fabric, slightly motion blurred, not a mannequin", "palette": []}},
         {"x": cx_, "y": cy_, "width": cw, "height": ch, "metadata": {"type": "obj", "text": "", "desc": "papaya orange McLaren 765LT supercar, glossy paint, glass headlights with LED signature", "palette": []}}]
EDIT = ("Transform this grey 3D clay render into a real photograph. Keep the exact composition, camera angle, car shape, wheels and shadows. "
        "The dark mannequin <obj_1> must become a real living woman, not a mannequin or a silhouette. ")
def grid(v, size): return max(0, min(1000, round(v * 1000 / size)))
rows = []
for i, b in enumerate(boxes):   # same table the FLUX 3 Layout Prompt node appends: bbox = [ymin, xmin, ymax, xmax] on a 0-1000 grid
    rows.append({"id": "obj_%d" % (i + 1), "bbox": [grid(b["y"], 768), grid(b["x"], 1280), grid(b["y"] + b["height"], 768), grid(b["x"] + b["width"], 1280)], "desc": b["metadata"]["desc"]})
FULLP = (EDIT + PROMPT).rstrip() + " " + json.dumps(rows, ensure_ascii=False); print(FULLP[-700:])
g = {
 "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_int8_convrot.safetensors", "type": "flux3", "device": "default"}},
 "2": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
 "3": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux3-image-klein-base-int8-convrot.safetensors", "weight_dtype": "default"}},
 "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "4": {"class_type": "CLIPTextEncode", "inputs": {"text": FULLP, "clip": ["1", 0]}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 0]}},
 "7": {"class_type": "ReferenceMultiLatent", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "vae": ["2", 0], "resolution": "resize", "resolution.megapixels": 0.9375, "images.image0": ["6", 0]}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["7", 2], "seed": seed, "steps": 50, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["2", 0]}},
 "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/klein_layout"}},
}
run(g, "klein_layout_v7_sidewalk_cfg%g_s%d" % (cfg, seed))
