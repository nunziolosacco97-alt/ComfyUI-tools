PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
for d in 0.30 0.25; do echo "RUN h3 city $d $(date +%H:%M)"; timeout 6000 "$PY" -I hr_gen.py h3 city W t $d 2>&1 | grep -E "HRDONE|Error|Traceback" | cut -c1-200; done
echo H3DENDONE
