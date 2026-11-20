set -eu
export SHANGHAI_PROJECT_ROOT="/tmp/shanghai-view-updates/dong60-numbers/stage77/projects/shanghai"
runner="/tmp/shanghai-view-updates/dong60-numbers/stage77/projects/shanghai/data/audit/hongkew-fire-station-v1/check-main-map.cjs"
spec="/tmp/shanghai-view-updates/dong60-numbers/stage77/projects/shanghai/data/audit/hongkew-fire-station-v1/map-case.json"
QA_OUTPUT_DIR="/tmp/hongkew77/control-dong60-numbers" QA_CONTROL_CITY_COUNT=121 QA_CONTROL_CATALOG="/tmp/shanghai-view-updates/dong60-numbers/stage76/projects/shanghai/data/candidate-city-integrations.json" QA_CONTROL_CATALOG_SHA256="$(python -c 'import json;print(json.load(open("/tmp/shanghai-view-updates/dong60-numbers/77-snapshot.json"))["previous_catalog_sha256"])')" MODEL_BASE_URL=http://127.0.0.1:14076/ node "$runner" "$spec" --control > "/tmp/hongkew77/control-dong60-numbers.log" 2>&1
QA_OUTPUT_DIR="/tmp/hongkew77/map-dong60-numbers" MODEL_BASE_URL=http://127.0.0.1:14077/ node "$runner" "$spec" > "/tmp/hongkew77/map-dong60-numbers.log" 2>&1
