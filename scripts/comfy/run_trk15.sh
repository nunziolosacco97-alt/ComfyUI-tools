#!/bin/bash
cd "/c/Users/Internet/Desktop/TEST COMFYUI/mclaren/bench"
PY=/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe
until grep -q FINALDONE ../mtn/run_final_log.txt 2>/dev/null; do sleep 15; done
$PY -I stage_trk.py
for v in A B C; do for m in zimage flux moss ph3 h3; do echo "RUN $m $v"; $PY -I trk_gen.py $m $v 101 2>&1 | grep -E "DONE|Error|RuntimeError|Traceback|HTTP" | cut -c1-300; done; done
echo ALL15DONE
