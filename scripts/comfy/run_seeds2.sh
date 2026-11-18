#!/bin/bash
cd "/c/Users/Internet/Desktop/TEST COMFYUI/mclaren/bench"
export INF=mcl13
PY="${PY:-python}"
$PY -I minimax_img.py 101 1
$PY -I p_h3_rich.py 101
$PY -I moss_v9.py 101 0 0.6
for s in 202 303; do
  $PY -I zimage.py $s depth 0.8 0.8 0
  $PY -I flux2_dev_v9.py $s 1
  $PY -I minimax_img.py $s 1
  $PY -I p_h3_rich.py $s
  $PY -I moss_v9.py $s 0 0.6
done
echo ALLDONE
