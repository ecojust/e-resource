set -eu
wk=/tmp/oriental65
p=/tmp/shanghai-view-revision/stage111/projects/shanghai
spec="$p/data/audit/oriental-hotel-v1/map-case.json"
runner="$p/data/audit/oriental-hotel-v1/check-main-map.cjs"
export SHANGHAI_PROJECT_ROOT="$p"
QA_OUTPUT_DIR="$wk/control-revised" QA_CONTROL_CITY_COUNT=110 QA_CONTROL_CATALOG=/tmp/shanghai-view-revision/stage110/projects/shanghai/data/candidate-city-integrations.json QA_CONTROL_CATALOG_SHA256=f1e4ab715e08a2e3fd133c743dbc3ca559dec0f21e209d1577f3c64b18ed3509 MODEL_BASE_URL=http://127.0.0.1:9064/ node "$runner" "$spec" --control > "$wk/control-revised.log" 2>&1
QA_OUTPUT_DIR="$wk/map-revised" MODEL_BASE_URL=http://127.0.0.1:9081/ node "$runner" "$spec" > "$wk/main-revised.log" 2>&1
