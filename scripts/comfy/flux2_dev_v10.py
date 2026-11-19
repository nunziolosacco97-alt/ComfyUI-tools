"""FLUX.2 [dev] image edit (template image_flux2_fp8): clay as reference image, Turbo LoRA 8 steps. args: seed [turbo 1|0]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
CAR = 'a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing'
PROMPT = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; turbo = int(sys.argv[2]) if len(sys.argv) > 2 else 1; var = sys.argv[3] if len(sys.argv) > 3 else 'A'
M = os.path.join(SH, "models")
while turbo and not os.path.exists(os.path.join(M, "loras", "Flux2TurboComfyv2.safetensors")): time.sleep(10)
EDIT = ("Edit the reference image: it is a grey 3D clay layout; turn it into a real photograph. Keep the exact camera angle, the position and shape of the car, the road, the raised sidewalk with its continuous kerb, "
        "the three stone columns, the pedestrian position and the direction of the sun shadows. The pedestrian is a real woman walking to the right in profile, wearing a long dark wool coat and elegant women's ankle boots with a slim heel. "
        "The shopfronts are plain dark glass with warm lit interiors and nothing displayed in them: no mannequins, no signs, no text, no logos, no brand names anywhere. The road is one single dark asphalt surface without extra strips. ")
if var == "B": EDIT += "A second reference image shows the real car with its true colour and parts: copy the paint colour, the front grille, the air intake and all car parts exactly from it. "
model = ["12", 0]
g = {
 "12": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux2_dev_fp8mixed.safetensors", "weight_dtype": "default"}},
 "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": "mistral_3_small_flux2_fp8.safetensors", "type": "flux2", "device": "default"}},
 "10": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
 "45": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "41": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["45", 0], "upscale_method": "area", "megapixels": 1.0, "resolution_steps": 1}},
 "40": {"class_type": "VAEEncode", "inputs": {"pixels": ["41", 0], "vae": ["10", 0]}},
 "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["38", 0], "text": EDIT + PROMPT}},
 "26": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["6", 0], "guidance": 4.0}},
 "39": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["26", 0], "latent": ["40", 0]}},
 "47": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
 "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
}
cond = ["39", 0]
if var == "B":
    g["45b"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}}
    g["41b"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["45b", 0], "upscale_method": "area", "megapixels": 1.0, "resolution_steps": 1}}
    g["40b"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["41b", 0], "vae": ["10", 0]}}
    g["39b"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["39", 0], "latent": ["40b", 0]}}; cond = ["39b", 0]
if turbo:
    g["88"] = {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["12", 0], "lora_name": "Flux2TurboComfyv2.safetensors", "strength_model": 1.0}}; model = ["88", 0]
g["22"] = {"class_type": "BasicGuider", "inputs": {"model": model, "conditioning": cond}}
g["48"] = {"class_type": "Flux2Scheduler", "inputs": {"steps": 8 if turbo else 20, "width": 1280, "height": 768}}
g["13"] = {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["25", 0], "guider": ["22", 0], "sampler": ["16", 0], "sigmas": ["48", 0], "latent_image": ["47", 0]}}
g["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["10", 0]}}
g["9"] = {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mcl/flux2dev"}}
run(g, "flux2dev_v10%s_%s_s%d" % (var, "turbo" if turbo else "full", seed))
