"""Nano Banana (API Google) sulle passate Blender. Autonomo: non usa ComfyUI e non usa l'output di altri modelli.
La chiave e' letta dalla variabile d'ambiente GEMINI_API_KEY e non viene MAI stampata.

uso:
  python nanobanana.py --check                      controlla che la chiave ci sia (non la mostra)
  python nanobanana.py SCENA [refs] [size] [modello] [--dry-run]
    SCENA   city | trk_A | trk_B | trk_C | hum_1 | hum_2 | hum_3 | hum_4   (cartella in scenes/)
    refs    1 = clay | 2 = clay + colore Blender (default) | 3 = clay + colore + profondita'
    size    1K | 2K | 4K (default 1K; prova prima 1K)
    modello default gemini-nano-banana-2.1
  --dry-run costruisce la richiesta e la salva in out/ senza inviarla (nessun costo)
Output: out/nb_<scena>_<modello>_<refs>ref_<size>_<n>.png (+ .json con prompt e parametri)."""
import sys, os, json, base64, io, urllib.request, urllib.error, time
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
key = os.environ.get("GEMINI_API_KEY", "")
if "--check" in sys.argv:
    print("GEMINI_API_KEY presente, lunghezza %d" % len(key) if key else "GEMINI_API_KEY NON impostata"); sys.exit(0)
args = [a for a in sys.argv[1:] if not a.startswith("--")]; dry = "--dry-run" in sys.argv
if not args: print(__doc__); sys.exit(1)
scene = args[0]; nref = int(args[1]) if len(args) > 1 else 2; size = args[2] if len(args) > 2 else "1K"; model = args[3] if len(args) > 3 else "gemini-nano-banana-2.1"
sd = os.path.join(HERE, "scenes", scene)
if not os.path.isdir(sd): print("scena sconosciuta:", scene, "- cartelle disponibili:", ", ".join(sorted(os.listdir(os.path.join(HERE, "scenes"))))); sys.exit(1)
if not key and not dry: print("GEMINI_API_KEY non impostata: nulla e' stato inviato"); sys.exit(1)
prompt = open(os.path.join(sd, "prompt.txt"), encoding="utf-8").read().strip()
def b64(path):
    im = Image.open(path).convert("RGB"); buf = io.BytesIO(); im.save(buf, "PNG"); return base64.b64encode(buf.getvalue()).decode()
files = ["beauty_clay", "beauty_color", "depth"][:nref]
inp = [{"type": "text", "text": prompt}] + [{"type": "image", "mime_type": "image/png", "data": b64(os.path.join(sd, f + ".png"))} for f in files]
body = {"model": model, "input": inp, "response_format": {"type": "image", "mime_type": "image/png", "image_size": size}}
n = 1
while os.path.exists(os.path.join(OUT, "nb_%s_%s_%dref_%s_%d.png" % (scene, model, nref, size, n))) or os.path.exists(os.path.join(OUT, "nb_%s_%s_%dref_%s_%d.json" % (scene, model, nref, size, n))): n += 1
base = os.path.join(OUT, "nb_%s_%s_%dref_%s_%d" % (scene, model, nref, size, n))
meta = {"scene": scene, "refs": files, "size": size, "model": model, "prompt": prompt}
json.dump(meta, open(base + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if dry: print("DRY-RUN ok: richiesta pronta, immagini:", files, "- non inviata"); sys.exit(0)
req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", json.dumps(body).encode(),
    {"x-goog-api-key": key, "Content-Type": "application/json", "Api-Revision": "2026-05-20"})
t0 = time.time()
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
if not imgs: print("nessuna immagine nella risposta:", json.dumps(r)[:1500].replace(key, "***")); sys.exit(3)
open(base + ".png", "wb").write(base64.b64decode(imgs[-1]))
print("SALVATA", base + ".png", Image.open(base + ".png").size, "%.0fs" % (time.time() - t0))
if isinstance(r, dict) and r.get("usage"): print("usage", json.dumps(r["usage"])[:300])
