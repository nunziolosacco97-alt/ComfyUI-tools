"""Dedicated pedestrian pass: Z-Image Turbo inpaints only the person mask on a finished plate (depth ControlNet keeps the pose), then pastes it back with a feathered mask.
usage: person_pass.py <plate.png> <tag> [inputs_folder=mcl2] [seed=7]"""
import sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
plate, tag = sys.argv[1], sys.argv[2]; inf = sys.argv[3] if len(sys.argv) > 3 else "mcl2"; seed = int(sys.argv[4]) if len(sys.argv) > 4 else 7
MC = os.path.dirname(HERE)
m = np.asarray(Image.open(os.path.join(MC, "inputs", "mask_foreground.png")).convert("L")) > 128
md = ndi.binary_dilation(m, iterations=14); mimg = Image.fromarray((md * 255).astype(np.uint8))
pl = Image.open(plate).convert("RGB").resize((1280, 768))
pn, mn = "pp_%s_plate.png" % tag, "pp_%s_mask.png" % tag
pl.save(os.path.join(SH, "input", inf, pn)); mimg.save(os.path.join(SH, "input", inf, mn))
PERSON = (PROMPT + ". In the right foreground a real woman walks past in profile, wearing a long dark wool coat and dark trousers with leather boots, natural brown hair, sunlit rim light on her coat, "
          "slight motion blur, photographic skin and fabric texture")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
 "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
 "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"}},
 "6": {"class_type": "LoadImage", "inputs": {"image": inf + "/depth.png"}},
 "7": {"class_type": "LoadImage", "inputs": {"image": inf + "/" + pn}},
 "8": {"class_type": "LoadImageMask", "inputs": {"image": inf + "/" + mn, "channel": "red"}},
 "9": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["4", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": 0.7, "image": ["6", 0], "inpaint_image": ["7", 0], "mask": ["8", 0], "start_percent": 0.0, "end_percent": 0.8}},
 "10": {"class_type": "CLIPTextEncode", "inputs": {"text": PERSON, "clip": ["2", 0]}},
 "11": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["10", 0]}},
 "12": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "13": {"class_type": "KSampler", "inputs": {"model": ["9", 0], "positive": ["10", 0], "negative": ["11", 0], "latent_image": ["12", 0], "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["3", 0]}},
 "15": {"class_type": "SaveImage", "inputs": {"images": ["14", 0], "filename_prefix": "mcl/pp_" + tag}},
}
out = run(g, "pp_%s_raw_s%d" % (tag, seed))[0]
gen = np.asarray(Image.open(out).convert("RGB").resize((1280, 768))).astype(np.float32); base = np.asarray(pl).astype(np.float32)
w = np.asarray(Image.fromarray((ndi.binary_dilation(m, iterations=8) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))).astype(np.float32)[..., None] / 255
res = Image.fromarray((base * (1 - w) + gen * w + .5).astype(np.uint8)); dst = os.path.join(RES, "pp_%s_s%d.png" % (tag, seed)); res.save(dst); print("RESULT", dst)
