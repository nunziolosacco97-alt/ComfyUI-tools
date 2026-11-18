import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; cfg = float(sys.argv[2]) if len(sys.argv) > 2 else 3.0
EDIT = ("Rich architectural detail: the limestone facade and columns show visible block joints, fine weathering, relief and natural texture; the paving slabs have joints and fine grain; the dark glazing reflects the street. Natural exposure with soft highlight roll-off, no bloom, no glow, no halation, no lens flare. Picture 1 is a grey 3D layout, picture 2 is the same scene with the real car colours: glossy papaya orange paint, black wheels and carbon parts. Transform picture 1 into a real photograph with vivid glossy paint and strong sky reflections. Keep the exact composition, camera angle, car shape, wheels, shadows and the walking pedestrian pose unchanged. ")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_edit_2511_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_2.5_vl_7b_fp8_scaled.safetensors", "type": "qwen_image", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
 "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.1}},
 "5": {"class_type": "CFGNorm", "inputs": {"model": ["4", 0], "strength": 1.0}},
 "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "7": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["6", 0]}},
 "6b": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
 "7b": {"class_type": "FluxKontextImageScale", "inputs": {"image": ["6b", 0]}},
 "8": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["2", 0], "prompt": EDIT + PROMPT, "vae": ["3", 0], "image1": ["7", 0], "image2": ["7b", 0]}},
 "9": {"class_type": "TextEncodeQwenImageEditPlus", "inputs": {"clip": ["2", 0], "prompt": NEG + ", bloom, glow, haze, overexposed highlights, plain empty walls", "vae": ["3", 0], "image1": ["7", 0], "image2": ["7b", 0]}},
 "10": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["8", 0], "reference_latents_method": "index_timestep_zero"}},
 "11": {"class_type": "FluxKontextMultiReferenceLatentMethod", "inputs": {"conditioning": ["9", 0], "reference_latents_method": "index_timestep_zero"}},
 "12": {"class_type": "VAEEncode", "inputs": {"pixels": ["7", 0], "vae": ["3", 0]}},
 "13": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["10", 0], "negative": ["11", 0], "latent_image": ["12", 0], "seed": seed, "steps": 25, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "14": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["3", 0]}},
 "15": {"class_type": "SaveImage", "inputs": {"images": ["14", 0], "filename_prefix": "mcl/qwenedit"}},
}
run(g, "qwenedit2511_v4_tex_2refs_cfg%g_s%d" % (cfg, seed))
