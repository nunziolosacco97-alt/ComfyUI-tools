import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
EDIT = ("The woman is seen strictly from the side, her face with nose and chin clearly visible in profile, looking toward the left of the frame, hair falling behind her head; she is not seen from behind. Rich architectural detail: the limestone facade and columns show visible block joints, fine weathering, relief and natural texture; the paving slabs have joints and fine grain; the dark glazing reflects the street. Natural exposure with soft highlight roll-off, no bloom, no glow, no halation, no lens flare. Image 1 is a grey 3D layout, image 2 is the same scene with the real car colours, glossy orange paint and black parts. Transform image 1 into a real photograph. Transform this grey 3D clay render into a real photograph. Keep the exact camera angle, the position and shape of the car, the position of the pedestrian and the direction of the sun shadows. You are free to design the architecture, the facade materials, the paving and all environment details yourself. "
        "The dark mannequin on the right must become a real living woman walking in profile, lit by the warm sun with a visible face, rim light on her hair and coat and natural skin tones, not a mannequin or a silhouette. Glossy paint with strong sky reflections. ")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "qwen_image_2.1_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_8b_int8_convrot.safetensors", "type": "qwen_image", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_2.1_vae_bf16.safetensors"}},
 "4": {"class_type": "QwenImage21Cache", "inputs": {"model": ["1", 0], "device": "auto", "dtype": "default"}},
 "5": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "5b": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
 "6": {"class_type": "TextEncodeQwenImage21", "inputs": {"clip": ["2", 0], "vae": ["3", 0], "prompt": EDIT + PROMPT, "negative_prompt": NEG + ", bloom, glow, haze, overexposed highlights, plain empty walls", "resolution": 1024, "images.image_1": ["5", 0], "images.image_2": ["5b", 0]}},
 "7": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["4", 0], "positive": ["6", 0], "negative": ["6", 0], "latent_image": ["7", 0], "seed": seed, "steps": 25, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
 "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/qwen21"}},
}
run(g, "qwen21_edit_v7_sidewalk_s%d" % seed)
