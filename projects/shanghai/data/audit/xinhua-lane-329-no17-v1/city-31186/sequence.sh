set -eu
w=/tmp/grace-final-31k/186
e="$w/evidence"
mkdir -p "$e" "$w/browser-work"
export TMPDIR="$w/browser-work" SHANGHAI_PROJECT_ROOT="$w/stage186" QA_CDP_PORT=19386
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
for mode in control mobile city; do
 mkdir -p "$e/$mode"
 rc=0
 case "$mode" in
 control) QA_CONTROL_CATALOG="$w/stage185/data/candidate-city-integrations.json" QA_CONTROL_CATALOG_SHA256=0ff08a431b1db0cd8d0d739ae94e30d4447f14e157c78764f365f93b42d78233 QA_CONTROL_CITY_COUNT=222 MODEL_BASE_URL=http://127.0.0.1:31185/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-xinhua.cjs" "/workspace/e-resource/projects/shanghai/data/audit/xinhua-lane-329-no17-v1/map-case.json" --control > "$e/$mode.log" 2>&1 || rc=$? ;;
 mobile) MODEL_BASE_URL=http://127.0.0.1:31186/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-xinhua.cjs" "/workspace/e-resource/projects/shanghai/data/audit/xinhua-lane-329-no17-v1/map-case.json" > "$e/$mode.log" 2>&1 || rc=$? ;;
 city) MODEL_BASE_URL=http://127.0.0.1:31186/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-xinhua.cjs" "/workspace/e-resource/projects/shanghai/data/audit/xinhua-lane-329-no17-v1/map-case.json" --after-mobile > "$e/$mode.log" 2>&1 || rc=$? ;;
 esac
 echo "$rc" > "$e/$mode-exit"
 test "$rc" -eq 0 || exit "$rc"
 if test "$mode" != city; then python -Bu "$w/coordinated-window.py" "$mode"; fi
done
