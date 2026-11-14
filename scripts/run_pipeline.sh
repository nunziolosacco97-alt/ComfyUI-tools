#!/bin/bash
# usage: run_pipeline.sh <tag>   (layout with terrain+motion blur for frames 35-43, LTX, finishing)
cd "/c/Users/Internet/Desktop/TEST COMFYUI/scripts"
BL="/c/Users/Internet/Documents/Blender/blender-5.1.2-windows-x64/blender.exe"
rm -f "../render/layout/"*.png
"$BL" -b "../blender/Test_circuito.blend" --python render_roadcar.py -- --out 'C:\Users\Internet\Desktop\TEST COMFYUI\render\layout\' --circuit --nocity --ground 0.27 --start 35 --end 43 --pitch 8 --shifty -0.09 --mblur > /tmp/lay_$1.out 2>&1
bash run_frame39.sh $1
