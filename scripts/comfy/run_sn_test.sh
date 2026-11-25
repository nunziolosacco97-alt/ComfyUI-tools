#!/bin/bash
cd "$(dirname "$0")"
PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
until grep -q CITYSEEDSDONE_ run_city_seeds_303_log.txt; do sleep 30; done
export INF=mcl13
for a in "1920 1152 plain" "1920 1152 tex" "2560 1536 tex"; do set -- $a; echo "RUN $a $(date +%H:%M)"; "$PY" -I sensenova_v10.py 101 L 2 $1 $2 $3 2>&1 | tail -n 2; done
echo SNTESTDONE
