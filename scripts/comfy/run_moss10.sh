export INF=mcl13
PY="${PY:-python}"
cd "$(dirname "$0")"
until grep -q ALLDONE5 h3fix2_log.txt; do sleep 10; done
for s in 101 202 303; do
$PY -I moss_v10.py $s 1 0.8
$PY -I moss_v10.py $s 1 1.0
done
echo ALLDONE6
