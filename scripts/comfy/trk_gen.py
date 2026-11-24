"""Race-track scene, 3 views x 5 finalist models. usage: python -I trk_gen.py MODEL VIEW [seed]
MODEL: zimage | flux | moss | ph3 | h3      VIEW: A (low kerb 3/4 front) | B (high wide front 3/4) | C (rear 3/4 panning)
Inputs: ComfyUI-Shared/input/trk_<VIEW>/{beauty_clay,beauty_color,depth,lines}.png.
Edit-style models (flux, ph3, h3) get the panned clay/colour; control models (zimage, moss) get the sharp depth/lines.
ph3 and h3 take the FLUX render of the same view as 2nd reference (same geometry as FLUX, as asked) - run flux first."""
import sys, os, time, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
model_name, VIEW = sys.argv[1], sys.argv[2]; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 101
INF = "trk_" + VIEW; M = os.path.join(SH, "models")
FRONT = "a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same front grille, the same front air intake, headlights, splitter, wheels and rear wing"
REAR = "a McLaren 765LT supercar in deep saturated glossy papaya orange (a rich orange, not yellow) with polished clearcoat, exactly as the reference: the same rear lights, the same diffuser, wheels and the same rear wing"
SCENE = {
 "A": ("low three-quarter front view from beside the kerb, slightly tilted horizon: the red and white kerb in the foreground is streaked by motion blur, the dark asphalt and the grass and trees behind are smeared by horizontal panning blur, the car itself razor sharp",
       FRONT),
 "B": ("high wide-angle three-quarter front view looking down at the car on a wide track that bends only gently to the left, strongly tilted horizon, the car in the left-centre of the frame, the asphalt streaked by motion blur, a long hard shadow behind the car, a long barrier wall running along the top of the frame, the car razor sharp",
       FRONT),
 "C": ("rear three-quarter panning shot from the infield side of the track, the car heads towards the LEFT of the image, so its nose points left and its tail with the rear wing and tail lights is on the RIGHT side of the image; COMPOSITION: the car is large and low in the frame, it spans about 70 percent of the image width and its wheels sit near the bottom edge, with only a thin strip of kerb and grass below it; behind it a long white pit wall and a grandstand at the right, the background smeared by strong horizontal motion blur, the car razor sharp",
       REAR),
}[VIEW]
CAR = SCENE[1]
PROMPT = ("Photorealistic motorsport photograph, " + CAR + " racing at full speed on a race circuit: " + SCENE[0] + ". Dark worn asphalt with dark rubber tyre marks that run strictly parallel to the direction of the track along the racing line, long straight or gently curving streaks that follow the road and its bend, never circles, never arcs across the road, never skid marks that cross the lane, red and white kerbs, grass run-off, concrete barriers, a line of trees and low hills in the distance, "
          "a moody dramatic cloudy sky with the sun breaking through, cinematic professional automotive photography, natural reflections in the paint and glass, subtle film grain, high detail")
NEG = ("parked car, static, sharp background, cgi, 3d render, cartoon, illustration, oversaturated, blurry car, deformed car, extra wheels, text, watermark, logo, low quality, "
       "yellow car, matte paint, different front bumper, redesigned grille, people, driver face, sponsor decals")
def need(*p):
    while not all(os.path.exists(x) for x in p): time.sleep(10)
OUT = "trk_%s_%s_s%d%s" % (model_name, VIEW, seed, os.environ.get("TAG", ""))

if model_name == "zimage":
    g = {
     "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "z_image_turbo_int8_convrot.safetensors", "weight_dtype": "default"}},
     "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b_fp8_mixed.safetensors", "type": "lumina2", "device": "default"}},
     "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
     "4": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["1", 0], "shift": 3.0}},
     "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "Z-Image-Turbo-Fun-Controlnet-Union.safetensors"}},
     "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/depth.png"}},
     "7": {"class_type": "ZImageFunControlnet", "inputs": {"model": ["4", 0], "model_patch": ["5", 0], "vae": ["3", 0], "strength": 0.8, "image": ["6", 0], "start_percent": 0.0, "end_percent": 0.8}},
     "8": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["2", 0]}},
     "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["8", 0]}},
     "10": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
     "11": {"class_type": "KSampler", "inputs": {"model": ["7", 0], "positive": ["8", 0], "negative": ["9", 0], "latent_image": ["10", 0], "seed": seed, "steps": 8, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
     "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
     "13": {"class_type": "SaveImage", "inputs": {"images": ["12", 0], "filename_prefix": "mcl/trk_zimage"}},
    }
elif model_name == "moss":
    g = {
     "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "moss_image_sft_int8_convrot.safetensors", "weight_dtype": "default"}},
     "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3.5_9b_int8_convrot.safetensors", "type": "moss_image", "device": "default"}},
     "4": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae_small.safetensors"}},
     "49": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "moss_image_color_depth_control.safetensors", "strength_model": 1.0}},
     "16": {"class_type": "TemporalScoreRescaling", "inputs": {"model": ["49", 0], "tsr_k": 0.95, "tsr_sigma": 1.0}},
     "36": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["16", 0], "shift": 5.0, "sampling": "flow"}},
     "2": {"class_type": "SkipLayerGuidanceDiTSimple", "inputs": {"model": ["36", 0], "double_layers": "", "single_layers": "24", "start_percent": 0.0, "end_percent": 1.0}},
     "5": {"class_type": "CLIPTextEncode", "inputs": {"text": PROMPT, "clip": ["3", 0]}},
     "6": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["3", 0]}},
     "10": {"class_type": "LoadImage", "inputs": {"image": INF + "/depth.png"}},
     "11": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
     "53": {"class_type": "MOSSImageControl", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "vae": ["4", 0], "strength": 1.0, "start_percent": 0.0, "end_percent": 1.0, "depth_map": ["10", 0], "color_map": ["11", 0]}},
     "54": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
     "21": {"class_type": "SamplerER_SDE", "inputs": {"solver_type": "ER-SDE", "max_stage": 3, "eta": 1.0, "s_noise": 1.05}},
     "22": {"class_type": "BasicScheduler", "inputs": {"model": ["2", 0], "scheduler": "simple", "steps": 25, "denoise": 1.0}},
     "20": {"class_type": "SamplerCustom", "inputs": {"model": ["2", 0], "add_noise": True, "noise_seed": seed, "cfg": 3.0, "positive": ["53", 0], "negative": ["53", 1], "sampler": ["21", 0], "sigmas": ["22", 0], "latent_image": ["54", 0]}},
     "9": {"class_type": "VAEDecode", "inputs": {"samples": ["20", 0], "vae": ["4", 0]}},
     "85": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/trk_moss"}},
    }
elif model_name == "flux":
    EDIT = ("Edit the reference image: it is a grey 3D clay layout; turn it into a real photograph. Keep the exact camera angle, the position and shape of the car, the track, the kerbs, the barriers and the direction of the sun shadows, and keep the motion blur of the background. "
            "A second reference image shows the real car with its true colour and parts: copy the paint colour, the car parts and all details exactly from it. No text, no logos, no brand names anywhere. ")
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
     "45b": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
     "41b": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["45b", 0], "upscale_method": "area", "megapixels": 1.0, "resolution_steps": 1}},
     "40b": {"class_type": "VAEEncode", "inputs": {"pixels": ["41b", 0], "vae": ["10", 0]}},
     "39b": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["39", 0], "latent": ["40b", 0]}},
     "47": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
     "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
     "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
     "88": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["12", 0], "lora_name": "Flux2TurboComfyv2.safetensors", "strength_model": 1.0}},
     "22": {"class_type": "BasicGuider", "inputs": {"model": ["88", 0], "conditioning": ["39b", 0]}},
     "48": {"class_type": "Flux2Scheduler", "inputs": {"steps": 8, "width": 1280, "height": 768}},
     "13": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["25", 0], "guider": ["22", 0], "sampler": ["16", 0], "sigmas": ["48", 0], "latent_image": ["47", 0]}},
     "8": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["10", 0]}},
     "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "mcl/trk_flux"}},
    }
elif model_name == "ph3":
    need(os.path.join(M, "text_encoders", "p-h3-image_text_encoder_int8_convrot.safetensors"), os.path.join(M, "vae", "p-h3-image_vae_int8_convrot.safetensors"), os.path.join(M, "loras", "p-h3-image_lora_bf16.safetensors"))
    REQ = ("Aspect ratio: 5:3\nEdit Picture 1: Turn this grey 3D layout into a real photograph, keeping the exact composition, camera angle, car position, track layout and background motion blur. " + SCENE[0] + ". "
           "The car is " + CAR + ", racing on a race circuit with dark worn asphalt, red and white kerbs, grass run-off, concrete barriers, trees and low hills, a moody dramatic cloudy sky. "
           "Picture 2 is a colour render of the same car with its true paint colour and parts: copy its paint colour, body parts and wheels onto the car of picture 1, keeping position and shape from picture 1.")
    g = {
     "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
     "19": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "p-h3-image_lora_bf16.safetensors", "strength_model": 1.0}},
     "18": {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["19", 0], "shift_video": 1.0, "shift_audio": 1.0}},
     "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "p-h3-image_text_encoder_int8_convrot.safetensors", "type": "minimax", "device": "default"}},
     "3": {"class_type": "VAELoader", "inputs": {"vae_name": "p-h3-image_vae_int8_convrot.safetensors"}},
     "26": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
     "6": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["26", 0], "upscale_method": "lanczos", "megapixels": 0.95, "resolution_steps": 32}},
     "27": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
     "28": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["27", 0], "upscale_method": "lanczos", "megapixels": 0.95, "resolution_steps": 32}},
     "9": {"class_type": "PH3ImageConditioning", "inputs": {"clip": ["2", 0], "prompt": REQ, "width": 0, "height": 0, "vae": ["3", 0], "images.image_1": ["6", 0], "images.image_2": ["28", 0]}},
     "10": {"class_type": "BasicGuider", "inputs": {"model": ["18", 0], "conditioning": ["9", 0]}},
     "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "er_sde"}},
     "12": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
     "13": {"class_type": "ManualSigmas", "inputs": {"sigmas": "1.0, 0.984753, 0.967905, 0.951688, 0.925372, 0.881923, 0.810083, 0.528718, 0.0"}},
     "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["12", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["13", 0], "latent_image": ["9", 1]}},
     "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["3", 0]}},
     "16": {"class_type": "SaveImage", "inputs": {"images": ["15", 0], "filename_prefix": "mcl/trk_ph3"}},
    }
elif model_name == "h3":
    W_, H_ = 1920, 1152
    EDIT = ("Picture 1 is a grey 3D clay layout of the scene and picture 2 shows the real car colours and parts. Turn it into a real photograph. Keep the camera angle, the position and shape of the car, the track layout, and the motion blur of the background. "
            "The car must keep its exact design from picture 1. Picture 2 is a colour render of the same car with its true paint colour and parts: copy its paint colour, body parts, wheels and fine details onto the car of picture 1, keeping the position and shape from picture 1. "
            "Real photographic micro-texture, fine film grain, natural contrast, no plastic look. ")
    g = {
     "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_image_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
     "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
     "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_image_vae_fp16.safetensors"}},
     "4": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_clay.png"}},
     "5": {"class_type": "ImageScale", "inputs": {"image": ["4", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}},
     "11": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
     "12": {"class_type": "ImageScale", "inputs": {"image": ["11", 0], "upscale_method": "lanczos", "width": W_, "height": H_, "crop": "disabled"}},
     "6": {"class_type": "MiniMaxH3ImageConditioning", "inputs": {"clip": ["2", 0], "prompt": EDIT + PROMPT, "width": W_, "height": H_, "vae": ["3", 0], "images.image_1": ["5", 0], "images.image_2": ["12", 0]}},
     "7": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["6", 0]}},
     "8": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["6", 1], "seed": seed, "steps": 6, "cfg": 1.0, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
     "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8", 0], "vae": ["3", 0]}},
     "10": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/trk_h3"}},
    }
else: raise SystemExit("unknown model " + model_name)
outs = run(g, OUT)
if model_name == "flux":                      # FLUX render of this view = body/geometry reference for ph3 and h3
    pass
