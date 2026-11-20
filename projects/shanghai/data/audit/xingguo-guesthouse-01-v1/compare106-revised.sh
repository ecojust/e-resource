set -eu
wk=/tmp/xingguo60
p=/tmp/shanghai-view-revision/stage106/projects/shanghai
spec="$p/data/audit/xingguo-guesthouse-01-v1/map-case.json"
runner="$p/data/audit/xingguo-guesthouse-01-v1/check-main-map.cjs"
export SHANGHAI_PROJECT_ROOT="$p"
QA_OUTPUT_DIR="$wk/control-revised" QA_CONTROL_CITY_COUNT=105 QA_CONTROL_CATALOG=/tmp/shanghai-view-revision/stage105/projects/shanghai/data/candidate-city-integrations.json QA_CONTROL_CATALOG_SHA256=5cf0a274a61f0588385a24c7d0a01ade124f57f364a8604caf404125acb1e223 MODEL_BASE_URL=http://127.0.0.1:8859/ node "$runner" "$spec" --control > "$wk/control-revised.log" 2>&1
QA_OUTPUT_DIR="$wk/map-revised" MODEL_BASE_URL=http://127.0.0.1:9076/ node "$runner" "$spec" > "$wk/main-revised.log" 2>&1
