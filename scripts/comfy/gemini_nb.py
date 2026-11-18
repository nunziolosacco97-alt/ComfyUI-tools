"""Nano Banana through Google's own API (Interactions API, revision 2026-05-20). The key is read from the GEMINI_API_KEY environment variable and is NEVER printed.
usage: gemini_nb.py --check | gemini_nb.py [model=gemini-nano-banana-2.1] [refs=1|2] [size=1K] [tag]"""
import sys, os, json, base64, urllib.request, urllib.error
from PIL import Image
import io
HERE = os.path.dirname(os.path.abspath(__file__)); MC = os.path.dirname(HERE); RES = os.path.join(HERE, "results")
sys.path.insert(0, HERE)
key = os.environ.get("GEMINI_API_KEY", "")
if "--check" in sys.argv:
    print("GEMINI_API_KEY presente, lunghezza %d" % len(key) if key else "GEMINI_API_KEY NON impostata"); sys.exit(0)
if not key: print("GEMINI_API_KEY non impostata: nulla e' stato inviato"); sys.exit(1)
model = sys.argv[1] if len(sys.argv) > 1 else "gemini-nano-banana-2.1"; nref = int(sys.argv[2]) if len(sys.argv) > 2 else 1
size = sys.argv[3] if len(sys.argv) > 3 else "1K"; tag = sys.argv[4] if len(sys.argv) > 4 else "v7"
from cx import PROMPT
EDIT = ("Image 1 is a grey 3D layout of the exact scene" + (" and image 2 is the same scene with the real car colours and parts" if nref == 2 else "") + ". Turn it into a real photograph. "
        "Keep the camera angle, the exact position and shape of the car, the position of the pedestrian, the road, the raised sidewalk and the kerb exactly as in image 1, and the direction of the sun shadows. "
        "The pedestrian is a real woman walking in profile towards the right, face visible, wearing a long dark wool coat and elegant women's ankle boots with a slim heel; her body, feet and face point the same way she walks. "
        "The car paint is softly lit with gentle highlights. 5:3 landscape. ")
def b64(path):
    im = Image.open(path).convert("RGB"); buf = io.BytesIO(); im.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
inp = [{"type": "text", "text": EDIT + PROMPT}, {"type": "image", "mime_type": "image/png", "data": b64(os.path.join(MC, "inputs", "beauty_clay.png"))}]
if nref == 2: inp.append({"type": "image", "mime_type": "image/png", "data": b64(os.path.join(MC, "inputs", "beauty_color.png"))})
body = {"model": model, "input": inp, "response_format": {"type": "image", "mime_type": "image/png", "image_size": size}}
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", json.dumps(body).encode(), {"x-goog-api-key": key, "Content-Type": "application/json", "Api-Revision": "2026-05-20"})
try: r = json.load(urllib.request.urlopen(req, timeout=300))
except urllib.error.HTTPError as e: print("HTTP", e.code, e.read().decode("utf-8", "replace")[:1500].replace(key, "***")); sys.exit(2)
imgs = []
def walk(o):
    if isinstance(o, dict):
        if o.get("type") == "image" and isinstance(o.get("data"), str): imgs.append(o["data"])
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(r)
if not imgs: print("nessuna immagine nella risposta:", json.dumps(r)[:1500]); sys.exit(3)
out = os.path.join(RES, "nanobanana_%s_%s_%dref_%s.png" % (tag, model.replace("/", "_"), nref, size)); open(out, "wb").write(base64.b64decode(imgs[-1])); print("SALVATA", out, Image.open(out).size)
if isinstance(r, dict) and r.get("usage"): print("usage", json.dumps(r["usage"])[:300])
