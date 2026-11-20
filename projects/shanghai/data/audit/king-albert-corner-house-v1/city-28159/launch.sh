set -eu
work=/dev/shm/grace-final-28k/159
mem=/dev/shm/qa-shannan159
p=/workspace/e-resource/projects/shanghai
casefile="$p/data/audit/king-albert-corner-house-v1/city-24159-map-case.json"
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
export SHANGHAI_PROJECT_ROOT="/dev/shm/grace-final-28k/159/stage159" QA_CDP_PORT=19359 TMPDIR="$mem/browser-work"
if ! test -e "$mem/evidence"; then
 python -B - "$mem" "$work" <<'STORAGE'
from pathlib import Path
from datetime import datetime,timezone
import json,os,sys
mem,work=map(Path,sys.argv[1:]);work=Path('/tmp/shannan159/final24159');mem.mkdir(exist_ok=True)
def available(p):
 raw=os.statvfs(p);return raw.f_bavail*raw.f_frsize
amounts={str(base):available(base)for base in [mem,work]};best=max((mem,work),key=lambda base:amounts[str(base)])
for name in ('evidence','browser-work'):
 target=best/name;target.mkdir(exist_ok=True)
 if best!=mem and not (mem/name).exists():(mem/name).symlink_to(target,target_is_directory=True)
(work/'actual-storage.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),working_volume=str(best),available_before=amounts),indent=2)+'\n')
STORAGE
fi
mkdir -p "$mem/evidence/control" "$mem/evidence/city" "$TMPDIR"
export QA_CONTROL_CATALOG="/dev/shm/grace-final-28k/159/stage158/data/candidate-city-integrations.json"
export QA_CONTROL_CATALOG_SHA256=b4e79645b355a9bed7f6fb3a11b0f5e66527da71949b37525eaa78a95ed84226 QA_CONTROL_CITY_COUNT=195
k=0
MODEL_BASE_URL=http://127.0.0.1:28158/ QA_OUTPUT_DIR="$mem/evidence/control" node "$work/check-shannan.cjs" "$casefile" --control > "$mem/evidence/control.log" 2>&1 || k=$?
printf '%s\n' "$k" > "$mem/evidence/control-exit"
test "$k" = 0
unset QA_CONTROL_CATALOG QA_CONTROL_CATALOG_SHA256 QA_CONTROL_CITY_COUNT
MODEL_BASE_URL=http://127.0.0.1:28159/ QA_OUTPUT_DIR="$mem/evidence/city" node "$work/check-shannan.cjs" "$casefile" > "$mem/evidence/city.log" 2>&1 || k=$?
printf '%s\n' "$k" > "$mem/evidence/city-exit"
exit "$k"
