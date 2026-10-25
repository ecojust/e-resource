# Rebuilding the source-qualified roof patch

The frozen qualification contains **126 roofs: 29 gabled and 97 skillion**, in
six owner cells and four districts. It matches the unchanged cached Overture
footprints to exact historical OpenStreetMap way versions. It supplies roof
shape, source height, roof height and an explicit ridge or downslope direction.
It does not add guessed roofs to buildings with incomplete source parameters.

The frozen file is `data/roofs/qualified-roofs.json`, with SHA-256:

```
25eeaa8e353190e54cbc575cabe0110530540c5dd1a04b3c04e943c5ffd3c0f2
```

Thirty accepted rows have zero-height eaves relative to their base; these are
roof-only shells, including eight elevated shells. The geometry code accepts
these cases without creating zero-area wall faces. Height comparisons permit
only floating-point rounding at the scale of the source numbers.

## Prerequisites and frozen inputs

Run these Bash/WSL commands from the published Shanghai project directory
(`projects/shanghai` in the repository). Use Python 3.11 or newer and Node.js.
Install the GIS dependencies and the mesh triangulator, then verify the height
release:

```bash
python -m pip install -r data/heights/requirements-rebuild.txt mapbox-earcut
python data/heights/verify_release.py
python source/city/check_roof_geometry.py
python source/city/check_source_roof_pipeline.py
```

Required inputs are the full `data/fullcity-raw/` archive, the current complete
`assets/city/` tree including `records/`, `state/` and `ids/`, the current exact
landmark exclusions, parent residual overrides, and the published locked height
rasters/CMAB shards. The small webpage launcher does not contain these build
inputs. Height-data reproduction is documented in
[`data/heights/REBUILD.md`](../../data/heights/REBUILD.md).

For the release's exact original base, use the immutable city snapshot identified
by `base_manifest_sha256` in `source-roof-patch-patch-plan.json`. A later city
snapshot may have the same geometry but different manifest/configuration hashes.
The tools reject mismatched source states, changed input locks and missing
accepted roofs; do not edit those checksums to make a changed source pass.

## Plan, build and merge

The following creates temporary work directories outside the repository. Keep
the resulting directory if you intend to inspect or publish its files.

```bash
roof_work="$(mktemp -d -t shanghai-roofs.XXXXXX)"
npm install --prefix "$roof_work/tools" gltfpack@1.3.0

roof_args=(
  --raw data/fullcity-raw
  --base-models assets/city
  --qualified-roofs data/roofs/qualified-roofs.json
  --landmark-exclusions data/landmark-exclusions.json
  --parent-residuals data/parent-residual-overrides.json
  --height-lock data/heights/height_sources_lock.json
  --height-raster data/heights/shanghai_ghsl_anbh_2018_3arcsec.tif
  --cnbh-raster data/heights/alternatives/cnbh_2020_shanghai_core_dm.tif
  --cmab-shards data/heights/cmab/shards
  --gltfpack "$roof_work/tools/node_modules/.bin/gltfpack"
  --output "$roof_work/patch"
  --workers 2
)

# Read and verify sources; write a plan only.
python source/city/build_source_roof_patches.py "${roof_args[@]}"

# Generate the six affected owner cells in the isolated patch directory.
python source/city/build_source_roof_patches.py "${roof_args[@]}" --export

# Build a separate, complete city. This does not switch the webpage to it.
python source/city/merge_source_roof_patches.py \
  --base-models assets/city \
  --patch "$roof_work/patch" \
  --output "$roof_work/merged" \
  --raw data/fullcity-raw \
  --published-raw-path data/fullcity-raw
```

The default exporter remains unchanged when no roof overrides are supplied.
The patch invokes its existing `export_source` implementation and the merge
invokes its existing `build_manifest` implementation. The same source-height
priority, exact landmark exclusions and restored parent residuals remain active.
Configuration records include source/qualifier/module versions and SHA-256
hashes. The source height rasters, sampler implementations and mesh writer must
match the base city's locks.

Owner-cell partitions retain their existing output IDs by replaying the original
median-split tree. A roof cannot cause silent subdivision or silently fall back
to a flat roof. Invalid accepted geometry, missing source records, changed
parameters or a changed count terminate the cell. The production baseline and
merged city retain **1,796,419 source features and 1,708 GLB tiles**. The 14
separately loaded detailed landmarks and existing `detail_patch` metadata are
preserved. This count describes source building/part features, not surveyed
individual buildings.

## Readiness signals and checks

`ROOF_CELL_READY` is emitted after the entire owner cell has passed file hashes,
GLB validation, unchanged feature-ID sidecars, unchanged footprint/height/district
counts and exactly-once application of all its accepted roofs. Its JSON payload
lists GLB, ID sidecar, record and state files with sizes and SHA-256 hashes.
Consumers may stage that cell's files incrementally, but must not publish a final
city manifest until `patch-manifest.json` has `complete:true` and the merge
passes. An exception leaves the patch incomplete.

The patch writes `roof-validation.json` with every source-qualified ID and its
geometry statistics, plus totals by roof shape and district. The merged city
includes those provenance documents under `source-roof-patch-*`, updates all
affected records and district indexes, and checks the final model/feature totals.
Unchanged GLBs and ID files may be hard-linked; metadata is copied, and patched
paths are unlinked before replacement. Original assets, unrelated records/states,
and preview symlinks remain unchanged.

Every generated GLB must be below 100,000,000 bytes. A file-size or partition
failure is reported rather than hiding an accepted roof. The caller should run
the project's full city audit and visual comparison before publishing. The small
fixture report in `data/roofs/pipeline-fixture-validation.json` validates software
invariants only; it is not a production geometry or browser-quality report.

## Re-running source qualification

Use a separate output when reviewing the qualifier, including offline reviews:

```bash
python source/city/qualify_roofs.py \
  --project . \
  --input data/roofs/cached-roof-candidates.geojson \
  --evidence data/roofs/source-evidence \
  --output "$roof_work/requalified-roofs.json" \
  --offline
```

The qualifier may write a new generation timestamp. Consequently, an otherwise
equivalent qualification can have a different file SHA-256. **Do not overwrite
the frozen qualification and expect byte-identical rebuilds.** A changed
qualification is a new input release; review it and rebuild the dependent patch
configuration and assets together. Exact historical source responses are retained
under `data/roofs/source-evidence/`; general roof-shape assumptions and limitations
are documented alongside the roof research data.
