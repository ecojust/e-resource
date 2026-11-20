set -u
w=/dev/shm/qa-yongjia167-31
mkdir -p "$w/tmp" "$w/evidence"
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export SHANGHAI_PROJECT_ROOT=/dev/shm/qa-yongjia167-31/stage167 TMPDIR="$(python -B /tmp/sichuan223/choose-profile.py "$(basename "$w")")"
export QA_CONTROL_CATALOG=/dev/shm/qa-yongjia167-31/stage166/data/candidate-city-integrations.json
export QA_CONTROL_CATALOG_SHA256=d2d234ca0f68cea0437ecb13f78234247ad286b3c29e3c2eafd7c3082452dd9e
export QA_CONTROL_CITY_COUNT=203
code=0
MODEL_BASE_URL=http://127.0.0.1:31166/ QA_OUTPUT_DIR="$w/evidence/before" node /workspace/e-resource/projects/shanghai/tools/check-sourced-candidate-map.cjs /workspace/e-resource/projects/shanghai/data/audit/yongjia-road-501-v1/map-case.json --control >"$w/control.log" 2>&1 || code=$?
if test "$code" -eq 0; then TMPDIR="$(python -B /tmp/sichuan223/choose-profile.py "$(basename "$w")")"; export TMPDIR; MODEL_BASE_URL=http://127.0.0.1:31167/ QA_OUTPUT_DIR="$w/evidence/after" node /workspace/e-resource/projects/shanghai/tools/check-sourced-candidate-map.cjs /workspace/e-resource/projects/shanghai/data/audit/yongjia-road-501-v1/map-case.json >"$w/main.log" 2>&1 || code=$?; fi
echo "$code" > "$w/exit"
exit "$code"
