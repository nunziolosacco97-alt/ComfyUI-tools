PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
mode_of() { case $1 in ph3) echo g;; *) echo t;; esac; }
up() { curl -s -m 5 http://127.0.0.1:8188/queue >/dev/null; }
run1() { sc=$1; v=$2; m=$3; md=$(mode_of $m); out="results/HR/hr${md}_${sc}_${m}_${v}_s101_d40.png"
  [ -f "$out" ] && { echo "SKIP $sc $m $v"; return; }
  until up; do echo "WAIT server down $(date +%H:%M)"; sleep 60; done
  echo "RUN $sc $m $v $md $(date +%H:%M)"
  timeout 6000 "$PY" -I hr_gen.py $m $sc $v $md 0.4 2>&1 | grep -E "HRDONE|Error|Traceback|HTTP|memory" | cut -c1-250
  [ -f "$out" ] || echo "FAIL $sc $m $v"; }
for v in A B C; do for m in zimage ph3 moss h3 flux; do run1 trk $v $m; done; done
for v in 1 2 3 4; do for m in zimage ph3 moss h3 flux; do run1 hum $v $m; done; done
echo HRALLDONE
