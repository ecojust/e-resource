set -eu
w=/tmp/grace-final-31k/175
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules TMPDIR=/dev/shm/guo175-browser-profile MALLOC_ARENA_MAX=2
for phase in after-desktop after-mobile; do
 rc=0
 node "$w/check-historical-map-actions.cjs" "$phase" "$w/bound-inputs.json" "$w/$phase" "$w/before/before.json" >"$w/$phase.log" 2>&1 || rc=$?
 echo "$rc" >"$w/$phase.exit"
 [ "$rc" -eq 0 ] || exit "$rc"
done
export SHANGHAI_PROJECT_ROOT=/workspace/e-resource/projects/shanghai MODEL_BASE_URL=http://127.0.0.1:31175/
rc=0
node "$SHANGHAI_PROJECT_ROOT/data/audit/kwok-brothers-residence-v1/check-webgl.cjs" "$w/viewer" > "$w/viewer.log" 2>&1 || rc=$?
echo "$rc" > "$w/viewer.exit"
exit "$rc"
