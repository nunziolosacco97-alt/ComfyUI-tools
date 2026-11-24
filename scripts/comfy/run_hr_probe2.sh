PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
for p in "ph3 t" "flux g" "flux t"; do set -- $p; echo "RUN $1 $2"; timeout 5400 "$PY" -I hr_gen.py $1 trk A $2 0.4 2>&1 | grep -E "HRDONE|Error|Traceback|HTTP|memory" | cut -c1-300; done
echo PROBE2DONE
