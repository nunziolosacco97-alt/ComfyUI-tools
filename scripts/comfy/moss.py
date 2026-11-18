"""MOSS-Image SFT + colour/depth control LoRA (template image_moss_image_color_depth_control). args: seed [color 0|1] [end_percent]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; use_col = int(sys.argv[2]) if len(sys.argv) > 2 else 0; en = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
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
 "53": {"class_type": "MOSSImageControl", "inputs": {"positive": ["5", 0], "negative": ["6", 0], "vae": ["4", 0], "strength": 1.0, "start_percent": 0.0, "end_percent": en, "depth_map": ["10", 0]}},
 "54": {"class_type": "EmptyLatentImage", "inputs": {"width": 1280, "height": 768, "batch_size": 1}},
 "21": {"class_type": "SamplerER_SDE", "inputs": {"solver_type": "ER-SDE", "max_stage": 3, "eta": 1.0, "s_noise": 1.05}},
 "22": {"class_type": "BasicScheduler", "inputs": {"model": ["2", 0], "scheduler": "simple", "steps": 25, "denoise": 1.0}},
 "20": {"class_type": "SamplerCustom", "inputs": {"model": ["2", 0], "add_noise": True, "noise_seed": seed, "cfg": 3.0, "positive": ["53", 0], "negative": ["53", 1], "sampler": ["21", 0], "sigmas": ["22", 0], "latent_image": ["54", 0]}},
 "9": {"class_type": "VAEDecode", "inputs": {"samples": ["20", 0], "vae": ["4", 0]}},
 "85": {"class_type": "SaveImage", "inputs": {"images": ["9", 0], "filename_prefix": "mcl/moss"}},
}
if use_col:
    g["11"] = {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}}
    g["53"]["inputs"]["color_map"] = ["11", 0]
run(g, "moss_v7_%s_end%g_s%d" % ("depth_color" if use_col else "depth", en, seed))
