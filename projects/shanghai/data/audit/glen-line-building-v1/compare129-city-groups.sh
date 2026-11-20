set -eu
export SHANGHAI_PROJECT_ROOT=/tmp/glen87/group-inputs/stage87/projects/shanghai
runner="$SHANGHAI_PROJECT_ROOT/tools/check-sourced-candidate-map.cjs"
spec="$SHANGHAI_PROJECT_ROOT/data/audit/glen-line-building-v1/map-case.json"
QA_OUTPUT_DIR=/tmp/glen87/group-control QA_CONTROL_CITY_COUNT=128 QA_CONTROL_CATALOG=/tmp/glen87/group-inputs/stage86/projects/shanghai/data/candidate-city-integrations.json QA_CONTROL_CATALOG_SHA256=6e4266b4cc86ddcd1cce3fccb76e223bca291d6b3d2dc779057bd4e5b2d36830 MODEL_BASE_URL=http://127.0.0.1:18086/ node "$runner" "$spec" --control > /tmp/glen87/group-control.log 2>&1
QA_OUTPUT_DIR=/tmp/glen87/group-after MODEL_BASE_URL=http://127.0.0.1:18087/ node "$runner" "$spec" > /tmp/glen87/group-after.log 2>&1
