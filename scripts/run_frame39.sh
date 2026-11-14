#!/bin/bash
# usage: run_frame39.sh <tag> [finish_only]   (layout with Blender motion blur in ../render/layout, parts in ../render/parts)
cd "/c/Users/Internet/Desktop/TEST COMFYUI/scripts"
PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
TAG=$1
FR='C:\Users\Internet\Desktop\TEST COMFYUI\frames\'
RAW="${FR}${TAG}_raw_5.png"
OUTF="${FR}frame39_${TAG}.png"
if [ "$2" != "finish_only" ]; then L_FAR=8 L_NEAR=12 "$PY" -I run_f39.py $TAG 35 5 7 > /tmp/$TAG.out 2>&1; fi
FF_NOFR2=1 FF_NOSKYDEEP=${NOSKYDEEP:-0} FF_NOASPH=1 FF_SAT=1.28 FF_CON=1.14 FF_PARTS='C:\Users\Internet\Desktop\TEST COMFYUI\render\parts\parts_0039.png' FF_WARM=0.7 FF_NOHELM=1 FF_NOSKY=1 FF_LOWDOF=1 "$PY" -I finish_frame3.py "$RAW" "$OUTF" >> /tmp/$TAG.out 2>&1
echo ALLDONE >> /tmp/$TAG.out
