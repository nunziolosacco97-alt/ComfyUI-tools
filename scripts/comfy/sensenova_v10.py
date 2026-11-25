"""SenseNova U1.6 8B-MoT image edit (official ComfyUI template graph, simple path). args: seed variant(L=8-step LoRA cfg1 | N=no LoRA 30 steps cfg4) [refs 1|2]
refs: clay (+ Blender beauty_color as 2nd ref, no other model's output). Output size 1280x768."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101; var = sys.argv[2] if len(sys.argv) > 2 else "L"; nref = int(sys.argv[3]) if len(sys.argv) > 3 else 2
CAR = 'a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing'
P = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)
EDIT = ("Picture 1 is a grey 3D clay layout of the scene" + (" and picture 2 shows the real car colours and parts" if nref == 2 else "") + ". Turn it into a real photograph. Keep the camera angle, the position and shape of the car, the position of the pedestrian and the direction of the sun shadows. "
        "The pedestrian is a real woman walking in profile, face visible, looking where she walks. The pedestrian walks on the raised sidewalk, her body, feet and face all pointing the same way she walks (toes forward). She wears elegant women's ankle boots with a slim heel, not men's shoes. ")
W_, H_ = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (1280, 768); TX = len(sys.argv) > 6 and sys.argv[6] == "tex"
if TX: EDIT += "Real photographic micro-texture everywhere: car paint with fine metallic flake, orange clearcoat with crisp specular reflections of the sky and buildings and slight orange peel, rubber tyre sidewall detail, brake calipers, carbon fibre, visible weave in the wool coat, fine film grain, sharp focus on the car, no smoothing, no plastic or clay look. "
lora = var == "L"
g = {
 "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sensenova_u1.6_8b_mot_bf16.safetensors"}},
 "4": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": EDIT + P}},
 "5": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": ""}},
 "10": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "11": {"class_type": "ImageScale", "inputs": {"image": ["10", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}},
 "29": {"class_type": "HiDreamO1ReferenceImages", "inputs": {"positive": ["4", 0], "negative": ["5", 0], "images.image_1": ["11", 0]}},
 "85": {"class_type": "SenseNovaConditioning", "inputs": {"conditioning": ["29", 0], "clip": ["1", 1], "negative": ["29", 1], "task": "image", "max_tokens": 1024}},
 "6": {"class_type": "EmptyHiDreamO1LatentImage", "inputs": {"width": W_, "height": H_, "batch_size": 1}},
 "67": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["85", 0], "negative": ["85", 2], "latent_image": ["6", 0], "seed": seed,
        "steps": 8 if lora else 30, "cfg": 1.0 if lora else 4.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
 "69": {"class_type": "VAEDecode", "inputs": {"samples": ["67", 0], "vae": ["1", 2]}},
 "24": {"class_type": "SaveImage", "inputs": {"images": ["69", 0], "filename_prefix": "mcl/sensenova"}},
}
if lora:
    g["27"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "sensenova_u1.6_8b_mot_8step_lora_bf16.safetensors", "strength_model": 1.0}}
    g["67"]["inputs"]["model"] = ["27", 0]
if nref == 2:
    g["12"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}}
    g["13"] = {"class_type": "ImageScale", "inputs": {"image": ["12", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}}
    g["29"]["inputs"]["images.image_2"] = ["13", 0]
run(g, "sensenova_v10%s_%dref_%dx%d%s_s%d" % (var, nref, W_, H_, "tex" if TX else "", seed))
