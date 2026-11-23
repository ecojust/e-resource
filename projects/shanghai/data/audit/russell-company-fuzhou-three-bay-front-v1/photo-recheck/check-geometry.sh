set -eu
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MALLOC_ARENA_MAX=1
p=/workspace/e-resource/projects/shanghai
ident=huangpu-russell-company-fuzhou-three-bay-front
base=/dev/shm/russell283-live
a="$p/data/audit/russell-company-fuzhou-three-bay-front-v1"
b="$base/bank/283/assets/models/candidates/$ident"
export TMPDIR="$base/work"
python -B "$a/check-packed-stone.py" --manifest "$b/manifest.json" --out "$base/verified-audit/photo-recheck/stone-texture.json"
python -B "$p/source/precise/$ident/source/check_surfaces.py" --manifest "$b/manifest.json" --out "$base/verified-audit/photo-recheck/three-surface-results.json"
