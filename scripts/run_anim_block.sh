#!/bin/bash
# usage: run_anim_block.sh <tag> [first_layout_frame=35]   finishes all 9 LTX frames of clip <tag> (layout frames first..first+8)
cd "/c/Users/Internet/Desktop/TEST COMFYUI/scripts"
PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
TAG=$1; F0=${2:-35}
SRC="C:\Users\Internet\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output\ltx"
FR='C:\Users\Internet\Desktop\TEST COMFYUI\frames\'
mkdir -p "../frames/anim_$TAG"
for k in 1 2 3 4 5 6 7 8 9; do
  fn=$((F0+k-1)); p=$(printf "%04d" $fn)
  cp "/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Shared/output/ltx/${TAG}_0000${k}_.png" "../frames/anim_$TAG/raw_$p.png"
  FF_NOFR2=1 FF_NOSKYDEEP=1 FF_NOASPH=1 FF_SAT=1.28 FF_CON=1.14 FF_PARTS="C:\Users\Internet\Desktop\TEST COMFYUI\render\parts\parts_$p.png" FF_WARM=0.7 FF_NOHELM=1 FF_NOSKY=1 FF_LOWDOF=1 "$PY" -I finish_frame3.py "C:\Users\Internet\Desktop\TEST COMFYUI\frames\anim_$TAG\raw_$p.png" "C:\Users\Internet\Desktop\TEST COMFYUI\frames\anim_$TAG\fin_$p.png" >> /tmp/anim_$TAG.out 2>&1
  echo "frame $p done" >> /tmp/anim_$TAG.out
done
echo ALLDONE >> /tmp/anim_$TAG.out
