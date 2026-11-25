PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
up() { curl -s -m 5 http://127.0.0.1:8188/queue >/dev/null; }
run1() { sc=$1; v=$2; m=$3; out="results/HR/hrt_${sc}_${m}_${v}_s101_d25.png"
  [ -f "$out" ] && { echo "SKIP $sc $m $v"; return; }
  until up; do echo "WAIT server down $(date +%H:%M)"; sleep 60; done
  echo "RUN $sc $m $v $(date +%H:%M)"
  timeout 6000 "$PY" -I hr_gen.py $m $sc $v t 0.25 2>&1 | grep -E "HRDONE|Error|Traceback|HTTP|memory" | cut -c1-250
  [ -f "$out" ] || echo "FAIL $sc $m $v"; }
for m in zimage h3; do
  for v in A B C; do run1 trk $v $m; done
  for v in 1 2 3 4; do run1 hum $v $m; done
  run1 city W $m
  echo "${m^^}ALLDONE"
done
