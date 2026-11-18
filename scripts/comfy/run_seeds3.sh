export INF=mcl13
PY="python"
cd "$(dirname "$0")"
$PY -I minimax_img.py 303 1
$PY -I p_h3_rich.py 303
$PY -I moss_v9.py 303 0 0.6
$PY -I flux2_dev_v9.py 202 1
$PY -I flux2_dev_v9.py 303 1
echo ALLDONE3
