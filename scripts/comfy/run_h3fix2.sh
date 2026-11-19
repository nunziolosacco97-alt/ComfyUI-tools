export INF=mcl13
PY="${PY:-python}"
cd "$(dirname "$0")"
until grep -q ALLDONE4 h3fix_log.txt; do sleep 10; done
for s in 101 202 303; do
$PY -I minimax_img_v8.py $s 2 D
$PY -I minimax_img_v8.py $s 2 E
done
echo ALLDONE5
