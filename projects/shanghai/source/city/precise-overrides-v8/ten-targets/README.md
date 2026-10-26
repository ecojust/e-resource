# Ten-target exact-owner rebuild source

This source adds only Hongde Church (`hongkou-hongde-church`) to the nine previously published exact-owner targets. Ten source features in eight near blocks across four macros are independently switchable; all 126 other features in those blocks remain. It does not create or accept the detailed church model.

The Hongde input is the immutable 36,862-byte `aa1d42251a01fc487ee01bc90190e2e561e85d60ee0b61e8cacdc69808fa4179` source. Compared with the initial identity input, only the photographic horizontal sign and its explanation changed. Its footprint, anchor, OSM w1085786138@2 identity, local2557 owner and ten neighbors did not change. The baseline17.25m value is an estimated raster-derived height, not a measured church/tower height. [Source binding](evidence/source-binding.json), [identity/front review](evidence/independent-identity-front-review.json) and [preservation check](evidence/preservation-check.json) retain the evidence boundaries.

This revision generated one11-feature near and reused the seven existing variants byte-for-byte. The [new actual decoded check](evidence/fresh-geometry-validation.json) verifies all82,362 oriented triangles, positions, materials and owner assignments exactly. Normals are not byte-identical: the maximum component difference is7.19e-9 and direction difference4.20e-7degrees, below the existing1e-7/1e-5degree limits. The real decoded-normal negative control was rejected. [Combined geometry evidence](evidence/geometry-validation.json) marks earlier checks as reused; [actual CPU owner checks](evidence/runtime-owner-validation.json) cover all four far and eight near models, independent/all/hidden owners, neighbor preservation, eviction and destruction. These checks are not WebGL or appearance acceptance.

## Rebuild from the matching complete project

The three tools and ten geometry inputs/five provider mapping reports are exact copies. Dependencies and all selected baseline hashes are in [dependencies.json](dependencies.json); no city baseline, photographs or detailed model binaries are duplicated here. Use CPython3.12.14, NumPy2.3.5, Shapely2.2.0/GEOS3.14.1, mapbox-earcut2.1.0, Node24.19.0 and npm gltfpack1.3.0. Install `requirements.lock` in a separate Python environment and the project `source/city/detail/tooling/package-lock.json` with npm ci. From this directory:

```sh
PROJECT="$(cd ../../../.. && pwd)"
GLTFPACK="$PROJECT/source/city/detail/tooling/node_modules/.bin/gltfpack"
NEW_OUTPUT=/absolute/path/to/a-new-output-outside-project
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python -B tools/build_precise_overrides.py \
  --project "$PROJECT" --output "$NEW_OUTPUT" --geometry-input-root ./inputs \
  --ids bund05 bund06 bund07 bund09 bund14 qingpu-beidajie-208-212 \
    qingpu-beidajie-222 xuhui-wukang-129 xuhui-wukang-210 hongkou-hongde-church \
  --gltfpack "$GLTFPACK" --asset-prefix assets/city-overrides-v6
node tools/verify_override_geometry.mjs "$NEW_OUTPUT/geometry-comparison-input.json"
node tools/verify_override_runtime.mjs "$PROJECT" "$NEW_OUTPUT/precise-buildings-v6.json"
```

This optional full-ten command regenerates only eight selected near blocks, not the whole city; it was not run for this delivery. For the new Hongde near alone use `--ids hongkou-hongde-church`. Keep work/per-feature references until validation finishes. Registry bookkeeping/paths or compressed bytes can differ across construction histories/environments, so validate each new output instead of asserting cross-version byte identity. Historical incremental composition is retained under evidence/history and is not required by this portable full rebuild.

Existing Wukang and Qingpu catalog index/replacement JSONs remain untouched. A future Hongkou macro index can be appended only after real detailed-model, static browser and catalog lifecycle evidence. This source does not set those acceptance flags or install anything.

## Attribution

Generation/validation code is MIT; see [LICENSE](LICENSE). Overture aggregate and frozen OSM footprints retain ODbL1.0 attribution, including Hongde w1085786138@2. Qingpu208–212 and222 remain EastAsianBuildings/Zenodo footprints under CCBY4.0, with OSM only as address context. Existing height-source attribution stays in each frozen feature. [COPYRIGHT.md](COPYRIGHT.md) preserves those distinctions. Photographic/model licenses belong to separate building packages.
