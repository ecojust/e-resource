set -eu
w=/tmp/huaihai169/final-map-31169
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export TMPDIR=/dev/shm/huaihai169-browser-profile
mkdir -p "$TMPDIR"
for phase in before after-desktop after-mobile; do
 if [ -f "$w/$phase.exit" ] && [ "$(cat "$w/$phase.exit")" = 0 ]; then continue; fi
 rc=0
 if [ "$phase" = before ]; then
  CHECK_DEVICE=desktop node "$w/check-historical-map.cjs" before "$w/bound-inputs.json" "$w/before" "$w/before/before.json" >"$w/before.log" 2>&1 || rc=$?
 else
  CHECK_DEVICE="${phase#after-}" node "$w/check-historical-map.cjs" after "$w/bound-inputs.json" "$w/$phase" "$w/before/before.json" >"$w/$phase.log" 2>&1 || rc=$?
 fi
 echo "$rc" >"$w/$phase.exit"
 [ "$rc" -eq 0 ] || exit "$rc"
done
python -B "$w/merge.py"
