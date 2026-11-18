import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; cfg = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
EDIT = ("Transform this grey 3D clay render into a real photograph. Keep the exact composition, camera angle, car shape, wheels, shadows and the walking pedestrian pose unchanged. ")
g = {
 "1": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_4b_int8_convrot.safetensors", "type": "flux3", "device": "default"}},
 "2": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
 "3": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux3-image-klein-base-int8-convrot.safetensors", "weight_dtype": "default"}},
 "4": {"class_type": "CLIPTextEncode", "inputs": {"text": EDIT + PROMPT, "clip": ["1", 0]}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 0]}},
 "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "7": {"class_type": "ReferenceMultiLatent", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "vae": ["2", 0], "resolution": "resize", "resolution.megapixels": 0.9375, "images.image0": ["6", 0]}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["3", 0], "positive": ["7", 0], "negative": ["7", 1], "latent_image": ["7", 2], "seed": seed, "steps": 50, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["2", 0]}},
 "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/klein"}},
}
run(g, "klein_v3_cfg%g_s%d" % (cfg, seed))
