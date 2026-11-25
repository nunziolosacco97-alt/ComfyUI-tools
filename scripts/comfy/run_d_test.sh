PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
up() { curl -s -m 5 http://127.0.0.1:8188/queue >/dev/null; }
t() { m=$1; md=$2; d=$3; until up; do sleep 60; done; echo "RUN $m $md $d $(date +%H:%M)"
  timeout 6000 "$PY" -I hr_gen.py $m city W $md $d 2>&1 | grep -E "HRDONE|Error|Traceback" | cut -c1-200; }
t ph3 g 0.25
t moss t 0.25
t flux t 0.25
echo DTESTDONE
