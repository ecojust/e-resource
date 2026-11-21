set -u
w=/dev/shm/qa-yueyang176-31
mkdir -p "$w/tmp" "$w/evidence"
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export SHANGHAI_PROJECT_ROOT=/dev/shm/qa-yueyang176-31/stage176 TMPDIR="$(python -B /tmp/sichuan223/choose-profile.py "$(basename "$w")")"
export QA_CONTROL_CATALOG=/dev/shm/qa-yueyang176-31/stage175/data/candidate-city-integrations.json
export QA_CONTROL_CATALOG_SHA256=a2863fe6fa3935e97a919c46246713680092361383cc7d502d53cf9bf08d2407
export QA_CONTROL_CITY_COUNT=212
phase=${1:-all}
case "$phase" in before|after|all) ;; *) exit 2 ;; esac
code=0
if [ "$phase" != after ]; then
  MODEL_BASE_URL=http://127.0.0.1:31175/ QA_OUTPUT_DIR="$w/evidence/before" node /dev/shm/qa-yueyang176-31/check-map-low-memory.cjs /workspace/e-resource/projects/shanghai/data/audit/yueyang-road-110-v1/map-case.json --control >"$w/control.log" 2>&1 || code=$?
  echo "$code" > "$w/control.exit"
  if [ "$phase" = before ] || [ "$code" -ne 0 ]; then exit "$code"; fi
fi
if [ "$phase" = after ]; then
  test "$(cat "$w/control.exit")" = 0 || exit 2
fi
if test "$code" -eq 0; then TMPDIR="$(python -B /tmp/sichuan223/choose-profile.py "$(basename "$w")")"; export TMPDIR; MODEL_BASE_URL=http://127.0.0.1:31176/ QA_OUTPUT_DIR="$w/evidence/after" node /dev/shm/qa-yueyang176-31/check-map-low-memory.cjs /workspace/e-resource/projects/shanghai/data/audit/yueyang-road-110-v1/map-case.json >"$w/main.log" 2>&1 || code=$?; fi 
echo "$code" > "$w/exit"
exit "$code"
