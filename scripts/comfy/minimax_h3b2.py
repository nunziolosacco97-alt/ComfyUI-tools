"""MiniMax H3 (video model) used as a still-image generator: 5-frame clip, depth Fun ControlNet on the repeated depth image, middle frame saved. Turbo 8-step LoRA."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7; cs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
g = {
 "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
 "2": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": "minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors", "strength_model": 1.0}},
 "3": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
 "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_int8_convrot.safetensors"}},
 "5": {"class_type": "ModelPatchLoader", "inputs": {"name": "minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors"}},
 "6": {"class_type": "LoadImage", "inputs": {"image": INF + "/depth.png"}},
 "7": {"class_type": "RepeatImageBatch", "inputs": {"image": ["6", 0], "amount": 5}},
 "8": {"class_type": "MiniMaxH3FunControlNetApply", "inputs": {"model": ["2", 0], "model_patch": ["5", 0], "vae": ["4", 0], "strength": cs, "start_percent": 0.0, "end_percent": 0.8, "control_video": ["7", 0]}},
 "30": {"class_type": "LoadImage", "inputs": {"image": INF + "/beauty_color.png"}},
 "9": {"class_type": "MiniMaxH3ImageToVideo", "inputs": {"clip": ["3", 0], "vae": ["4", 0], "prompt": "Static locked-off camera, no motion. Turn this 3D render into a real photograph. " + PROMPT, "width": 1280, "height": 768, "length": 5, "first_frame": ["30", 0]}},
 "10": {"class_type": "BasicGuider", "inputs": {"model": ["8", 0], "conditioning": ["9", 0]}},
 "11": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
 "12": {"class_type": "BasicScheduler", "inputs": {"model": ["8", 0], "scheduler": "simple", "steps": 8, "denoise": 1.0}},
 "13": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
 "14": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["13", 0], "guider": ["10", 0], "sampler": ["11", 0], "sigmas": ["12", 0], "latent_image": ["9", 1]}},
 "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["4", 0]}},
 "16": {"class_type": "ImageFromBatch", "inputs": {"image": ["15", 0], "batch_index": 4, "length": 1}},
 "17": {"class_type": "SaveImage", "inputs": {"images": ["16", 0], "filename_prefix": "mcl/h3"}},
}
run(g, "minimaxh3_v3b_firstframe_cs%g_s%d" % (cs, seed))
