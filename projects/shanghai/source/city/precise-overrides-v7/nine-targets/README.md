# Nine-target exact-owner full rebuild source

This package rebuilds the city-baseline ownership partitions for Bund05/06/07/09/14, Qingpu Beidajie208–212 and222, and Wukang129 and210. The frozen inputs address9source features in7near blocks across3macros; all116other features in those blocks remain. It does not create the photo-informed architectural models, accepted navigation, ordinary catalogs or HTML approval.

The three entry-point tools and all9geometry inputs plus4mapping reports are copied byte-for-byte from the frozen21-file whitelist. [Original whitelist](evidence/original-source-files-v9.json) and [copy/input verification](source-check.json) bind those bytes. Original staging documents and compose_incremental.py are retained only underevidence/history; their references toeight-targets or private stage directories describe history. They are not dependencies of the full rebuild below.

## Full rebuild from a complete published project

Start in source/city/precise-overrides-v7/nine-targets. The project must already contain the immutable city-detail baseline for14-13701-6700,14-13718-6695 and14-13720-6694 and the code/vendor dependencies listed in [dependencies.json](dependencies.json). No large baseline files are duplicated here. Missing source data must be restored from the matching published project, not replaced by downloaded current footprints or guessed heights.

Use CPython3.12.14, NumPy2.3.5, Shapely2.2.0/GEOS3.14.1, mapbox-earcut2.1.0 and Node24.19.0. The generator requires Shapely's constrained Delaunay API; Shapely2.0 is insufficient. Install the minimal pinned wheels into an isolated environment with `python -m pip install -r requirements.lock`. The existing project tooling lock pins npm gltfpack1.3.0; prepare that tool with `npm ci --prefix "$PROJECT/source/city/detail/tooling"` after setting PROJECT below. A previously installed matching compressor may be used instead.

```sh
PROJECT="$(cd ../../../.. && pwd)"
GLTFPACK="$PROJECT/source/city/detail/tooling/node_modules/.bin/gltfpack"
NEW_OUTPUT=/absolute/path/to/a-new-nine-target-output-outside-project

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python -B tools/build_precise_overrides.py \
  --project "$PROJECT" --output "$NEW_OUTPUT" \
  --geometry-input-root ./inputs \
  --ids bund05 bund06 bund07 bund09 bund14 \
    qingpu-beidajie-208-212 qingpu-beidajie-222 xuhui-wukang-129 xuhui-wukang-210 \
  --gltfpack "$GLTFPACK" --asset-prefix assets/city-overrides-v6

node tools/verify_override_geometry.mjs "$NEW_OUTPUT/geometry-comparison-input.json"
node tools/verify_override_runtime.mjs "$PROJECT" "$NEW_OUTPUT/precise-buildings-v6.json"
```

NEW_OUTPUT must be a new directory outside PROJECT; preserve its work/per-feature references until both validators finish. This command intentionally supplies all9IDs and no reuse-registry/reuse-asset-root. It regenerates all7near blocks directly from the frozen3macro baselines; no eight-targets directory, earlier incremental result or existing override model is required. Keep the asset-prefix shown: the published runtime paths still use city-overrides-v6 even though this source-delivery revision isv7.

The generator first writes precise-buildings-v6.draft.json and geometry-comparison-input.json. The original geometry validator decodes the real baseline and new near models using project Three/Meshopt, verifies every target and neighbor, and writes a complete registry only after passing. Positions/materials/oriented triangles/multiplicity are checked exactly; normal directions have the explicit1e-7component and1e-5degree tolerances, not byte identity. It also exercises an actual decoded-normal negative control. The original runtime validator then checks all3far and7near models, individual/all/hidden owners, neighbor preservation, eviction anddestroy; it writes runtime-owner-validation.json. These areCPU checks, not WebGL or photographic truth tests. Neither tool installs results or marks a new architectural model/catalog accepted.

## Version and reproducibility limits

Direct inspection for this delivery found package.json version1.3.0 and CLI output`gltfpack 1.3`; the four installed compressor fileSHAs exactly match the published environment lock. The old six-target README's1.0 wording is not used as a version pin. [dependencies.json](dependencies.json) records the npm tarball integrity, CLI/library/WASM SHAs, engine/configuration hashes and every required baseline fileSHA. Compression uses the original arguments and deterministic gzip level6/mtime0.

This delivery performed pure input/dependency/path checks only. It did not run a full rebuild, decode aGLB or rerun browser/runtime visual acceptance. The nine-target artifacts previously assembled incrementally are a different construction history: a clean full rebuild may change registry JSON bookkeeping, paths or compressed bytes, especially with a changed tool/environment. No cross-version or whole-registry byte-identity guarantee is claimed. Every new output must pass the supplied independent geometry and runtime checks; retain any failure rather than relaxing tolerances or changing frozen source dimensions.

## Attribution and scope

[LICENSE](LICENSE) covers the original generation/validation code. [COPYRIGHT.md](COPYRIGHT.md) distinguishes the Overture/OSM database, the two Zenodo/East Asian Buildings footprints and frozen height provenance. These inputs preserve source geometry, source heights and provider identity. Qingpu208–212 and222 are not OSM building ways. The package contains no photographs or photo-textured model binaries and makes no claim that the entire city's inferred baseline has photographic detail.
