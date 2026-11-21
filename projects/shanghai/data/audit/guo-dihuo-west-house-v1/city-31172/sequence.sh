set -eu
w=/tmp/grace-final-31k/172
e="$w/evidence"
mkdir -p "$e" "$w/browser-work"
export TMPDIR="$w/browser-work" SHANGHAI_PROJECT_ROOT="$w/stage172" QA_CDP_PORT=19372
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
for mode in control mobile city; do
 mkdir -p "$e/$mode"
 rc=0
 case "$mode" in
 control) QA_CONTROL_CATALOG="$w/stage171/data/candidate-city-integrations.json" QA_CONTROL_CATALOG_SHA256=6745c649d1e52dfa837cdae97d4db6365a6759db9e73870f9a222bfc2cd199a5 QA_CONTROL_CITY_COUNT=208 MODEL_BASE_URL=http://127.0.0.1:31171/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-guo.cjs" "/workspace/e-resource/projects/shanghai/data/audit/guo-dihuo-west-house-v1/map-case.json" --control > "$e/$mode.log" 2>&1 || rc=$? ;;
 mobile) MODEL_BASE_URL=http://127.0.0.1:31172/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-guo.cjs" "/workspace/e-resource/projects/shanghai/data/audit/guo-dihuo-west-house-v1/map-case.json" > "$e/$mode.log" 2>&1 || rc=$? ;;
 city) MODEL_BASE_URL=http://127.0.0.1:31172/ QA_OUTPUT_DIR="$e/$mode" node "$w/check-guo.cjs" "/workspace/e-resource/projects/shanghai/data/audit/guo-dihuo-west-house-v1/map-case.json" --after-mobile > "$e/$mode.log" 2>&1 || rc=$? ;;
 esac
 echo "$rc" > "$e/$mode-exit"
 test "$rc" -eq 0 || exit "$rc"
done
