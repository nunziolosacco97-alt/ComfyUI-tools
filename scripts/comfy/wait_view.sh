# usage: wait_view.sh SCENE VIEW  -> waits for the 5 4K files, builds the comparison sheet
PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
sc=$1; v=$2
while true; do n=0; for m in zimage flux moss h3; do [ -f results/HR/hrt_${sc}_${m}_${v}_s101_d40.png ] && n=$((n+1)); done; [ -f results/HR/hrg_${sc}_ph3_${v}_s101_d40.png ] && n=$((n+1)); [ $n -eq 5 ] && break; grep -q HRALLDONE run_hr_all_log.txt && break; sleep 60; done
"$PY" -I sheet_hr.py $sc $v 2>&1 | grep -v Warning | tail -2; echo "VIEWDONE $sc $v $n"
