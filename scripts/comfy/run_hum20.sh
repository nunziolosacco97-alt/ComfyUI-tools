#!/bin/bash
cd "/c/Users/Internet/Desktop/TEST COMFYUI/mclaren/bench"
PY=/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe
for v in 1 2 3 4; do for m in flux zimage moss ph3 h3; do echo "RUN $m $v"; $PY -I hum_gen.py $m $v 101 2>&1 | grep -E "DONE|Error|RuntimeError|Traceback|HTTP" | cut -c1-250; done; done
echo HUM20DONE
