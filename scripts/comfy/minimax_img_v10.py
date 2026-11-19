"""MiniMax H3 *Image* (the model used in the video): reference-conditioned image edit, 6 steps, CFG 1, euler/simple. args: seed [refs: 1|2]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
CAR = 'a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing'
PROMPT = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; nref = int(sys.argv[2]) if len(sys.argv) > 2 else 1; var = sys.argv[3] if len(sys.argv) > 3 else "A"
M = os.path.join(SH, "models")
while not (os.path.exists(os.path.join(M, "diffusion_models", "minimax_h3_image_pruned_int8_convrot.safetensors")) and os.path.exists(os.path.join(M, "vae", "minimax_h3_image_vae_fp16.safetensors"))): time.sleep(10)
W_, H_ = 1920, 1152
EDIT = ("Picture 1 is a grey 3D clay layout of the scene. Turn it into a real photograph. Keep the camera angle, the position and shape of the car, the position of the pedestrian and the direction of the sun shadows. "
        "The pedestrian is a real woman walking in profile, face visible, looking where she walks. The pedestrian walks on the raised sidewalk, her body, feet and face all pointing the same way she walks (toes forward). She wears elegant women's ankle boots with a slim heel, not men's shoes. ")
if var == "C": EDIT += "Keep the car design exactly as in the layout: same headlights, air intakes, wheels and body lines. Real car paint: deep papaya orange metallic with fine flake, crisp natural reflections of the sky and buildings, hard sun contrast. Real photographic micro-texture on asphalt and stone, fine film grain, no smoothing, no plastic look. "
if var == "B": EDIT += "Real photographic micro-texture, fine film grain, natural hard sun contrast, no plastic look. "
if var in ("F","G"): EDIT += "The car must keep its exact design from picture 1: same front grille, same front air intake, same headlights and wheels. "
if var in ("D","E","F","G"): EDIT += "Picture 2 is a real photograph of the same car. Use it as the reference for the car body: copy its paint colour, body surfaces, reflections, wheels and fine details onto the car of picture 1, keeping the position and shape from picture 1. Real photographic micro-texture, fine film grain, natural hard sun contrast, no plastic look. "
if var in ("D","E","F","G"): nref = 2
if nref == 2: EDIT = EDIT.replace("Picture 1 is a grey 3D clay layout of the scene.", "Picture 1 is a grey 3D clay layout of the scene and picture 2 shows the real car colours and parts.")
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_image_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_image_vae_fp16.safetensors"}},
 "4": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "5": {"class_type": "ImageScale", "inputs": {"image": ["4", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}},
 "6": {"class_type": "MiniMaxH3ImageConditioning", "inputs": {"clip": ["2", 0], "prompt": EDIT + PROMPT, "width": W_, "height": H_, "vae": ["3", 0], "images.image_1": ["5", 0]}},
 "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
 "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["6", 1], "seed": seed, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
 "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/h3img"}},
}
if nref == 2:
    g["11"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/" + (("ref_flux_s%d.png" % seed) if var in ("D","F") else ("ref_zimage_s%d.png" % seed) if var in ("E","G") else "beauty_color.png")}}
    g["12"] = {"class_type": "ImageScale", "inputs": {"image": ["11", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}}
    g["6"]["inputs"]["images.image_2"] = ["12", 0]
run(g, "h3image_v10%s_%dref_s%d" % (var, nref, seed))
