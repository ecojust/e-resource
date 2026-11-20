set -eu
w=/tmp/grace-final-31k/163
e="$w/evidence"
mkdir -p "$e" "$w/browser-work"
export TMPDIR="$w/browser-work" SHANGHAI_PROJECT_ROOT="$w/stage163" QA_CDP_PORT=19363
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
for mode in control mobile city; do
 mkdir -p "$e/$mode"
 rc=0
 case "$mode" in
 control) QA_CONTROL_CATALOG="$w/stage162/data/candidate-city-integrations.json" QA_CONTROL_CATALOG_SHA256=e64746f5308d6ad005e173de5d6b18e7952bb76ca77b2b010cd8e2c5dd6c864c QA_CONTROL_CITY_COUNT=199 MODEL_BASE_URL=http://127.0.0.1:31162/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-yicun.cjs" "/workspace/e-resource/projects/shanghai/data/audit/yicun-no2-street-front-v1/map-case.json" --control > "$e/$mode.log" 2>&1 || rc=$? ;;
 mobile) MODEL_BASE_URL=http://127.0.0.1:31163/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-yicun.cjs" "/workspace/e-resource/projects/shanghai/data/audit/yicun-no2-street-front-v1/map-case.json" > "$e/$mode.log" 2>&1 || rc=$? ;;
 city) MODEL_BASE_URL=http://127.0.0.1:31163/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-yicun.cjs" "/workspace/e-resource/projects/shanghai/data/audit/yicun-no2-street-front-v1/map-case.json" --after-mobile > "$e/$mode.log" 2>&1 || rc=$? ;;
 esac
 echo "$rc" > "$e/$mode-exit"
 test "$rc" -eq 0 || exit "$rc"
done
