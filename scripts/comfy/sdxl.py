import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
g = {
 "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "RealVisXL_V5.0_fp16.safetensors"}},
 "2": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["1", 1]}},
 "3": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["1", 1]}},
 "4": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-union-sdxl-1.0_promax.safetensors"}},
 "5": {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["4", 0], "type": "depth"}},
 "6": {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["4", 0], "type": "canny/lineart/anime_lineart/mlsd"}},
 "7": {"class_type": "LoadImage", "inputs": {"image": INF + "/depth.png"}},
 "8": {"class_type": "LoadImage", "inputs": {"image": INF + "/lines.png"}},
 "9": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["2", 0], "negative": ["3", 0], "control_net": ["5", 0], "image": ["7", 0], "strength": 0.85, "start_percent": 0.0, "end_percent": 0.8, "vae": ["1", 2]}},
 "10": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["9", 0], "negative": ["9", 1], "control_net": ["6", 0], "image": ["8", 0], "strength": 0.6, "start_percent": 0.0, "end_percent": 0.7, "vae": ["1", 2]}},
 "11": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "12": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["10", 0], "negative": ["10", 1], "latent_image": ["11", 0], "seed": seed, "steps": 32, "cfg": 5.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
 "13": {"class_type": "VAEDecode", "inputs": {"samples": ["12", 0], "vae": ["1", 2]}},
 "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "mcl/sdxl"}},
}
run(g, "sdxl_v3_s%d" % seed)
