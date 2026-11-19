export INF=mcl13
PY="${PY:-python}"
cd "$(dirname "$0")"
for s in 101 202 303; do
$PY -I minimax_img_v7.py $s 1 A
$PY -I minimax_img_v7.py $s 2 B
$PY -I minimax_img_v7.py $s 1 C
done
echo ALLDONE4
