set -eu
w=/tmp/yan816188/final-map-31188
a="$w/fixture/projects/shanghai/data/audit/yan-tongchun-residence-v1"
s=/tmp/yan816188/final-map-31188
if [ "$1" != before ]; then export NODE_OPTIONS="--require=$w/constrained-viewport.cjs"; fi
export NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules
if [ "$1" = architecture ]; then python -B "$w/slot-between.py" phone; fi
case "$1" in
  before) n=187; mode=before; export YAN_BROWSER_SEGMENT=complete;;
  desktop|phone|architecture|distant) n=188; mode=after; export YAN_BROWSER_SEGMENT="$1";;
  *) exit 2;;
esac
driver=check-independent-city.cjs
if [ "$1" = distant ]; then driver=check-distant-and-downloads.cjs; fi
node "$w/$driver" "$a/city-actions.json" "$mode" "http://127.0.0.1:31$n/" "$s/$n-production.json" "$w/$1" "$w/before/before.json"
