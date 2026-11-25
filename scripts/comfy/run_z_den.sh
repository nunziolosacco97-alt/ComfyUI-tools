PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
until grep -q H3DENDONE run_h3_den_log.txt; do sleep 30; done
for d in 0.25 0.55; do echo "RUN zimage city $d $(date +%H:%M)"; timeout 3000 "$PY" -I hr_gen.py zimage city W t $d 2>&1 | grep -E "HRDONE|Error|Traceback" | cut -c1-200; done
echo ZDENDONE
