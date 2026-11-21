set -eu
w=/tmp/grace-final-31k/183
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export TMPDIR="$w/browser-work"
mkdir -p "$TMPDIR"
for phase in before after-desktop after-mobile; do
 rc=0
 node "$w/check-historical-map.cjs" "$phase" "$w/bound-inputs.json" "$w/$phase" "$w/before/before.json" >"$w/$phase.log" 2>&1 || rc=$?
 echo "$rc" >"$w/$phase.exit"
 [ "$rc" -eq 0 ] || exit "$rc"
done

export SHANGHAI_PROJECT_ROOT=/workspace/e-resource/projects/shanghai MODEL_BASE_URL=http://127.0.0.1:31183/
rc=0
node -r "$SHANGHAI_PROJECT_ROOT/data/audit/brunner-mond-v1/viewer-timeout.cjs" "$SHANGHAI_PROJECT_ROOT/tools/check-candidate-viewer.cjs" changning-wuyi-road-127-garden-front "$w/viewer" > "$w/viewer.log" 2>&1 || rc=$?
echo "$rc" > "$w/viewer.exit"
[ "$rc" -eq 0 ] || exit "$rc"
