"""Tiny ComfyUI API helper for the model bench. Inputs live in ComfyUI-Shared/input/mcl/, outputs go to ComfyUI-Shared/output/mcl/."""
import json, time, urllib.request, uuid, os, shutil
API = "http://127.0.0.1:8188"; SH = r"C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared"
HERE = os.path.dirname(os.path.abspath(__file__)); INF = os.environ.get("INF", "mcl3"); RES = os.path.join(HERE, "results"); os.makedirs(RES, exist_ok=True)
PROMPT = ("Photorealistic automotive advertising photograph: a papaya orange McLaren 765LT supercar parked on a dark asphalt road in front of a monumental "
          "modern stone colonnade building with exactly three tall square stone columns standing on low plinths and supporting one continuous heavy cornice, dark glazed shopfronts recessed behind the columns. A raised light stone sidewalk runs continuously along the whole foreground, separated from the road by one continuous straight kerb, and another sidewalk runs along the building behind the car. Low warm late-afternoon sun from behind-left casting long hard "
          "shadows across the pavement, deep contrast between sunlit and shaded areas, in the right foreground a real human woman in a long dark wool coat walks past in profile, with natural hair and skin, slightly motion blurred, shallow depth "
          "of field, cinematic commercial car photography, 50mm lens, natural reflections in the paint and glass, subtle film grain, high detail")
NEG = "mannequin, statue, silhouette cutout, dress, cartoon, illustration, cgi, 3d render, oversaturated, blurry car, deformed car, extra wheels, text, watermark, logo, low quality"
def post(path, data):
    r = urllib.request.Request(API + path, json.dumps(data).encode(), {"Content-Type": "application/json"})
    try: return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e: raise RuntimeError("HTTP %s: %s" % (e.code, e.read().decode("utf-8", "replace")[:2500]))
def get(path): return json.load(urllib.request.urlopen(API + path))
def run(graph, name, timeout=3600):
    if os.environ.get("DUMP_DIR"):  # export the graph as ComfyUI API-format JSON instead of running it
        os.makedirs(os.environ["DUMP_DIR"], exist_ok=True)
        p = os.path.join(os.environ["DUMP_DIR"], name + ".json"); json.dump(graph, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False); print("DUMPED", p); return [p]
    cid = str(uuid.uuid4()); pid = post("/prompt", {"prompt": graph, "client_id": cid})["prompt_id"]; t0 = time.time()
    while time.time() - t0 < timeout:
        h = get("/history/" + pid)
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") == "error": raise RuntimeError(json.dumps(st)[:1500])
            outs = []
            for n, o in h[pid]["outputs"].items():
                for im in o.get("images", []): outs.append(os.path.join(SH, "output", im.get("subfolder", ""), im["filename"]))
            dst = []
            for i, p in enumerate(outs):
                d = os.path.join(RES, "%s_%d.png" % (name, i)); shutil.copy(p, d); dst.append(d)
            print("DONE", name, "%.0fs" % (time.time() - t0), dst); return dst
        time.sleep(2)
    raise TimeoutError(name)
