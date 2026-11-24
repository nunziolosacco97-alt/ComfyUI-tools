#!/bin/bash
cd "/c/Users/Internet/Desktop/TEST COMFYUI/mclaren/bench"
PY=/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe
export TAG=_nf
for v in A B C; do for m in zimage flux moss ph3 h3; do echo "RUN trk $m $v"; $PY -I trk_gen.py $m $v 101 2>&1 | grep -E "DONE|Error|RuntimeError|Traceback|HTTP" | cut -c1-160; done; done
echo TRKNFDONE
for v in 1 2 3 4; do for m in zimage flux moss ph3 h3; do echo "RUN hum $m $v"; $PY -I hum_gen.py $m $v 101 2>&1 | grep -E "DONE|Error|RuntimeError|Traceback|HTTP" | cut -c1-160; done; done
echo NF35DONE
