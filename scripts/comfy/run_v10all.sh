cd "$(dirname "$0")"
export INF=mcl13
PY="${PY:-python}"
up() { until curl -s -m 5 http://127.0.0.1:8188/system_stats >/dev/null; do sleep 15; done; }
go() { up; "$@"; }
sleep 120; up; sleep 30
for s in 101 202 303; do
  go $PY -I zimage_v10.py $s depth 0.8 0.8 0
  go $PY -I zimage_v10.py $s depth 1 1 0.4
  go $PY -I flux2_dev_v10.py $s 1 A
  go $PY -I flux2_dev_v10.py $s 1 B
  go $PY -I p_h3_v10.py $s A
  go $PY -I p_h3_v10.py $s B
  go $PY -I minimax_img_v10.py $s 2 F
  go $PY -I minimax_img_v10.py $s 2 G
done
echo ALLDONE10
