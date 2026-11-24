import os, shutil
from PIL import Image
SH = r"C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared\input"; B = r"C:\Users\Internet\Desktop\TEST COMFYUI\mclaren\mtn"
for v in "1234":
    d = os.path.join(SH, "hum_" + v); os.makedirs(d, exist_ok=True)
    Image.open(os.path.join(B, "hum_out_%s" % v, "beauty_clay.png")).convert("RGB").resize((1280, 768), Image.LANCZOS).save(os.path.join(d, "beauty_clay.png"))
    Image.open(os.path.join(B, "hum_out_%s" % v, "beauty_color.png")).convert("RGB").resize((1280, 768), Image.LANCZOS).save(os.path.join(d, "beauty_color.png"))
    for n in ("depth", "lines"): shutil.copy(os.path.join(B, "hum_inputs_%s" % v, n + ".png"), os.path.join(d, n + ".png"))
    print("staged", v)
