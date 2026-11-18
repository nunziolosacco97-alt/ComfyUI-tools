"""Invia a ComfyUI uno dei workflow in formato API (workflows/*.json) e attende il risultato.

Uso:  python tools/run_workflow.py workflows/1_z_image_turbo_depth.json [seed]
Serve ComfyUI acceso su http://127.0.0.1:8188 (cambia con COMFY_API).
Le immagini guida (beauty_clay.png, depth.png) devono stare in ComfyUI/input/mcl13/.
"""
import json, os, sys, time, urllib.request, uuid

API = os.environ.get("COMFY_API", "http://127.0.0.1:8188")


def call(path, data=None):
    req = urllib.request.Request(API + path, json.dumps(data).encode() if data else None, {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def main():
    graph = json.load(open(sys.argv[1], encoding="utf-8"))
    if len(sys.argv) > 2:  # sostituisce il seed in tutti i nodi che ne hanno uno
        for node in graph.values():
            for k in ("seed", "noise_seed"):
                if k in node["inputs"]:
                    node["inputs"][k] = int(sys.argv[2])
    pid = call("/prompt", {"prompt": graph, "client_id": str(uuid.uuid4())})["prompt_id"]
    print("In coda:", pid)
    while True:
        h = call("/history/" + pid)
        if pid in h:
            st = h[pid]["status"]
            if st.get("status_str") == "error":
                sys.exit("Errore: " + json.dumps(st)[:1500])
            for o in h[pid]["outputs"].values():
                for im in o.get("images", []):
                    print("Salvata in output/%s/%s" % (im.get("subfolder", ""), im["filename"]))
            return
        time.sleep(2)


if __name__ == "__main__":
    main()
