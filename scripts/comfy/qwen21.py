import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
EDIT = ("Transform this grey 3D clay render into a real photograph. Keep the exact composition, camera angle, car shape, wheels, columns and shadows unchanged. "
        "The dark mannequin on the right must become a real living woman walking in profile, not a mannequin or a silhouette. ")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
 "4": {"class_type": "QwenImage21Cache", "inputs": {"model": ["1", 0], "device": "auto", "dtype": "default"}},
 "5": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "6": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": EDIT + PROMPT, "negative_prompt": NEG, "resolution": 1024, "images.image_1": ["5", 0]}},
 "7": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["6", 0], "latent_image": ["7", 0], "seed": seed, "steps": 25, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
 "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/qwen21"}},
}
run(g, "qwen21_edit_v3_s%d" % seed)
