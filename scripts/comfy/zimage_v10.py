import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
CAR = 'a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing'
PROMPT = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; ctl = sys.argv[2] if len(sys.argv) > 2 else "depth"; sd = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8; en = float(sys.argv[4]) if len(sys.argv) > 4 else 0.8; sl = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
 "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
 "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"}},
 "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/%s.png" % ("depth" if ctl == "depth" else "lines")}},
 "7": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["4", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": sd, "image": ["6", 0], "start_percent": 0.0, "end_percent": en}},
 "20": {"class_type": "LoadImage", "inputs": {"image": INF + "/lines.png"}},
 "21": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["7", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": max(sl, 0.01), "image": ["20", 0], "start_percent": 0.0, "end_percent": en}},
 "8": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
 "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["8", 0]}},
 "10": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "11": {"class_type": "KSampler", "inputs": {"model": ["21", 0] if sl > 0 else ["7", 0], "positive": ["8", 0], "negative": ["9", 0], "latent_image": ["10", 0], "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
 "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": "mcl/zimage"}},
}
run(g, "zimage_v10_%s_s%d_d%g_e%g_l%g" % (ctl, seed, sd, en, sl))
