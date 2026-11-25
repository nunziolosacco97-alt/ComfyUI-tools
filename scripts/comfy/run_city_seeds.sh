#!/bin/bash
# item 5: city scene, seeds 202 and 303, 5 models, chosen denoise (zimage/ph3/h3 0.25, moss/flux 0.4)
cd "$(dirname "$0")"
PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
for s in "$@"; do
 for spec in "ph3 g 0.25" "zimage t 0.25" "h3 t 0.25" "flux t 0.4" "moss t 0.4"; do
  set -- $spec
  echo "RUN $1 $2 $3 s$s $(date +%H:%M)"
  "$PY" -I hr_gen.py $1 city W $2 $3 $s 2>&1 | tail -n 2 || echo "FAIL $spec $s"
 done
done
echo CITYSEEDSDONE_$*
