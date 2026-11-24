PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
for m in moss h3 ph3 flux; do for mode in g t; do echo "RUN $m $mode"; timeout 5400 "$PY" -I hr_gen.py $m trk A $mode 0.4 2>&1 | grep -E "HRDONE|Error|Traceback|HTTP|out of memory" | cut -c1-220; done; done
echo PROBEDONE
