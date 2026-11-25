PY="/c/Users/Internet/AppData/Local/Comfy-Desktop/ComfyUI-Installs/c/ComfyUI/.venv/Scripts/python.exe"
until grep -q HRCITYDONE run_hr_city_log.txt; do sleep 60; done
"$PY" -I sheet_city.py 2>&1 | grep -v Warning | tail -2; echo CITYSHEETDONE
