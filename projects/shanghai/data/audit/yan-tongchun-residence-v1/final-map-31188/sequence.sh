set -eu
w=/tmp/yan816188/final-map-31188
for phase in before desktop phone architecture distant; do
  if [ -f "$w/$phase.exit" ] && [ "$(cat "$w/$phase.exit")" = 0 ]; then continue; fi
  [ ! -e "$w/$phase.exit" ] || { echo "Retain and inspect the earlier incomplete $phase session." >&2; exit 2; }
  rc=0
  export TMPDIR="$w/profile-$phase"
  mkdir -p "$TMPDIR"
  bash "$w/run.sh" "$phase" > "$w/$phase.log" 2>&1 || rc=$?
  echo "$rc" > "$w/$phase.exit"
  [ "$rc" -eq 0 ] || exit "$rc"
  case "$phase" in before|desktop) python -B "$w/slot-between.py" "$phase";; esac
done
python -B "$w/merge-sessions.py"
