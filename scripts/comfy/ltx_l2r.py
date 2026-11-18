"""LTX-2.5 Layout-to-Render IC-LoRA used for a still: the clay is repeated into a 9-frame layout clip, the middle frame is kept. args: seed [inputs folder]"""
import sys, os, subprocess, shutil, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cx import *
import av
from PIL import Image
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 7
W_, H_, N_ = 1600, 960, 9
MC = os.path.dirname(HERE); SCR = os.environ.get("LTX_SCRIPTS", "scripts")
clay = Image.open(os.path.join(MC, "inputs", "beauty_clay.png")).convert("RGB").resize((W_, H_), Image.LANCZOS)
name = "layout_mclaren_s%d.mp4" % seed
c = av.open(os.path.join(SH, "input", name), "w"); st = c.add_stream("libx264", rate=24); st.width, st.height, st.pix_fmt = W_, H_, "yuv420p"; st.options = {"crf": "8"}
for _ in range(N_):
    for p in st.encode(av.VideoFrame.from_image(clay)): c.mux(p)
for p in st.encode(): c.mux(p)
c.close()
tag = "mclltx_s%d" % seed
P = PROMPT + " Real photograph, not a render."
r = subprocess.run([sys.executable, "-I", "run_ltx_l2r.py", "--style", "0", "--layout", name, "--w", str(W_), "--h", str(H_), "--n", str(N_), "--seed", str(seed), "--prompt", P, "--tag", tag], cwd=SCR, capture_output=True, text=True)
print(r.stdout[-600:], r.stderr[-600:])
src = os.path.join(SH, "output", "ltx", "%s_%05d_.png" % (tag, 5))
dst = os.path.join(RES, "ltx_l2r_v7_s%d.png" % seed); shutil.copy(src, dst); print("DONE", dst)
