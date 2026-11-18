"""Hybrid step on Z-Image Turbo: paste the Blender car (RGBA) on the AI plate, then harmonise with a low-denoise img2img pass (depth ControlNet keeps the geometry).
usage: hybrid_z.py <plate.png> <tag> [denoise=0.35] [seed=7]"""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
import numpy as np
from PIL import Image
plate, tag = sys.argv[1], sys.argv[2]; den = float(sys.argv[3]) if len(sys.argv) > 3 else 0.35; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
MC = os.path.dirname(HERE)
ai = Image.open(plate).convert("RGBA").resize((1280, 768)); car = Image.open(os.path.join(MC, "inputs", "car_rgba.png")).convert("RGBA")
# gentle colour match: bring the Blender car's mean luminance/warmth towards the plate's car region (from the ID paint mask)
m = np.asarray(Image.open(os.path.join(MC, "inputs", "mask_paint.png")).convert("L")) > 128
a = np.asarray(ai.convert("RGB")).astype(np.float32); c = np.asarray(car.convert("RGB")).astype(np.float32)
gain = (a[m].mean(0) / np.maximum(c[m].mean(0), 1.0)); gain = np.clip(gain, 0.6, 1.8); print("colour gain", gain)
al = np.asarray(car)[..., 3:4].astype(np.float32) / 255
c2 = np.clip(c * (0.5 + 0.5 * gain), 0, 255); car2 = np.concatenate([c2, al * 255], -1).astype(np.uint8)
comp = Image.alpha_composite(ai, Image.fromarray(car2, "RGBA")).convert("RGB")
name = "hy_%s_in.png" % tag; comp.save(os.path.join(HERE, "results", name)); shutil.copy(os.path.join(HERE, "results", name), os.path.join(SH, "input", "mcl", name))
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
 "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
 "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"}},
 "6": {"class_type": "LoadImage", "inputs": {"image": "mcl/depth.png"}},
 "7": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["4", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": 0.8, "image": ["6", 0], "start_percent": 0.0, "end_percent": 0.8}},
 "8": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
 "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["8", 0]}},
 "10": {"class_type": "LoadImage", "inputs": {"image": "mcl/" + name}},
 "11": {"class_type": "VAEEncode", "inputs": {"pixels": ["10", 0], "vae": ["3", 0]}},
 "12": {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["8", 0], "negative": ["9", 0], "latent_image": ["11", 0], "seed": seed, "steps": 10, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": den}},
 "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["3", 0]}},
 "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "mcl/hy_%s" % tag}},
}
run(g, "hy_%s_d%02d_s%d" % (tag, int(den * 100), seed))
