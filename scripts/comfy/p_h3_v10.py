"""Pruna P-H3-Image, richer environment prompt (template image_p_h3_image_edit). Prompt upsampler skipped. args: seed"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
CAR = 'a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing'
PROMPT = PROMPT.replace("a papaya orange McLaren 765LT supercar", CAR)
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; var = sys.argv[2] if len(sys.argv) > 2 else 'A'
M = os.path.join(SH, "models")
need = [os.path.join(M, "text_encoders", "p-h3-image_text_encoder_int8_convrot.safetensors"), os.path.join(M, "vae", "p-h3-image_vae_int8_convrot.safetensors"), os.path.join(M, "loras", "p-h3-image_lora_bf16.safetensors")]
while not all(os.path.exists(p) for p in need): time.sleep(10)
REQ = ("Aspect ratio: 5:3\nRequest: Turn this grey 3D layout into a real photograph, keeping the exact composition and the same three columns. Make the environment naturally rich without adding more columns: "
       "the travertine facade has varied slabs and carved cornice shadows, the dark glazed shopfronts show warm lit interiors and slim metal mullions and reflect trees from across the street, "
       "a stone bench and a large planter with an olive tree stand between the columns, a few distant out-of-focus pedestrians are inside the arcade, the paving is worn with expansion joints and a drain, "
       "a few dry leaves lie in the kerb gutter, there are faint road markings and a slim street lamp. A " + CAR + " is parked on the dark asphalt road, warm low sun with long shadows, "
       "and a real woman in a long dark wool coat and heeled ankle boots walks to the right in profile on the raised light stone sidewalk.")
if var == "B": REQ = "Edit Picture 1: " + REQ + " Picture 2 is a real photograph of the same car: copy its paint colour, body surfaces, reflections, grille, air intake and wheels onto the car of picture 1, keeping position and shape from picture 1."
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
 "19": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "p-h3-image_lora_bf16.safetensors", "strength_model": 1.0}},
 "18": {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["19", 0], "shift_video": 1.0, "shift_audio": 1.0}},
 "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "p-h3-image_text_encoder_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
 "3": {"class_type": "VAELoader", "inputs": {"vae_name": "p-h3-image_vae_int8_convrot.safetensors"}},
 "26": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
 "6": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["26", 0], "upscale_method": "lanczos", "megapixels": 0.95, "resolution_steps": 32}},
 "9": {"class_type": "PH3ImageConditioning", "inputs": {"clip": ["2", 0], "prompt": REQ, "width": 0, "height": 0, "vae": ["3", 0], "images.image_1": ["6", 0]}},
 "10": {"class_type": "BasicGuider", "inputs": {"model": ["18", 0], "conditioning": ["9", 0]}},
 "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "er_sde"}},
 "12": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
 "13": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.984753, 0.967905, 0.951688, 0.925372, 0.881923, 0.810083, 0.528718, 0.0"}},
 "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["12", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["13", 0], "latent_image": ["9", 1]}},
 "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["3", 0]}},
 "16": {"class_type": "SaveImage", "inputs": {"images": ["15", 0], "filename_prefix": "mcl/ph3"}},
}
if var == "B":
    g["27"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/ref_flux_s%d.png" % seed}}
    g["28"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["27", 0], "upscale_method": "lanczos", "megapixels": 0.95, "resolution_steps": 32}}
    g["9"]["inputs"]["images.image_2"] = ["28", 0]
run(g, "ph3image_v10%s_s%d" % (var, seed))
