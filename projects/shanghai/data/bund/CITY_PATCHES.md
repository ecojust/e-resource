# Confirmed detailed-building replacements

`build_bund_city_patches.py` makes an independent patch set. It does not edit the
published project, the original raw source, or the existing city model directory.
The normal full set of ten selected Bund buildings intersects only owner cells
`14/13720/6693` and `14/13720/6694`.

The confirmation file describes models that actually exist and cover the whole
listed candidate footprint. A planning draft with `coverage_confirmed:false`
does not remove anything. This flag records the model author's geometry scope;
it is not an additional user approval requirement.

```json
{
  "models": [
    {
      "candidate_id": "bund02",
      "glb": "bund_classics/shanghai-club.glb",
      "scope": "entire_candidate_footprint",
      "coverage_confirmed": true,
      "coverage_statement": "Author verified the complete supplied OSM footprint is modeled.",
      "included_optional_groups": []
    },
    {
      "candidate_id": "bund23",
      "glb": "art_deco/bank-of-china.glb",
      "scope": "entire_candidate_footprint",
      "coverage_confirmed": true,
      "included_optional_groups": ["bank-west-wing"]
    }
  ]
}
```

Omit `bank-west-wing` if that wing was not modeled. The script checks actual GLB2
headers and the strict 100,000,000-byte file limit. It scans the full source
archive for each UUID and closes parent/part relationships, including parts
assigned to adjacent cells. No radius-based suppression is used.

For the Customs House candidate `bund13`, the optional group
`customs-roof-components` covers five independently mapped source volumes: the
central clock body and four roof corner pavilions. Their affiliation is recorded
in `customs-components.json`; include that group only after the detailed model
author verifies every exact component footprint, including upper projections
outside the original main-body rectangle. The western rear wing is not in it.

To reproduce the two-cell update, keep the original five-landmark V2 city in
`work/city-v2`. If it is no longer available, use the complete generation steps
in `source/city/FULLCITY_BUILD.md` with
`data/bund/landmark-exclusions-v2.json` and a separate output directory to rebuild
that baseline. The published `assets/city` already contains V3; it is not the V2
input for this historical patch.

Run these commands from the project root:

```sh
python source/city/build_bund_city_patches.py \
  --raw data/fullcity-raw \
  --base-models work/city-v2 \
  --base-exclusions data/bund/landmark-exclusions-v2.json \
  --candidates data/bund/bund-candidates.json \
  --confirmations data/bund/bund-model-confirmations.json \
  --output work/bund-city-patches \
  --city-source-dir source/city \
  --height-raster data/heights/shanghai_ghsl_anbh_2018_3arcsec.tif \
  --cnbh-raster data/heights/alternatives/cnbh_2020_shanghai_core_dm.tif \
  --cmab-shards data/heights/cmab/shards \
  --height-lock data/heights/height_sources_lock.json \
  --parent-residuals data/parent-residual-overrides.json \
  --gltfpack gltfpack \
  --export
```

Without `--export`, this writes only the concrete plan and combined exclusion
configuration. With `--export`, it invokes the existing full-city exporter only
for affected source cells and publishes `tiles`, `ids`, `records` and `state`
inside the separate output directory. Other cells are never migrated or rebuilt.

After the completed detailed GLBs are present in the destination, merge only the
listed owner-cell assets and their states. Remove any old split-output IDs listed
as superseded but absent from the patch. Preserve all unrelated state and
configuration hashes. Finally call the existing aggregate `build_manifest` on
the merged directory and run `audit_fullcity_models.py` against the original raw
archive. The patch manifest is deliberately labelled as a patch, not a complete
city manifest.

```sh
python source/city/merge_bund_city_patches.py \
  --base-models work/city-v2 \
  --patch work/bund-city-patches \
  --output work/city-v3 \
  --raw data/fullcity-raw \
  --city-source-dir source/city \
  --published-raw-path data/fullcity-raw

python source/city/audit_fullcity_models.py \
  --raw data/fullcity-raw \
  --models work/city-v3 \
  --output work/city-v3-validation.json
```

The optional `--working-project` merge argument connects a separate non-Git
preview only when its `assets/city` is already a symlink. Omit it when building
inside a normal repository; review the audited output before installing it.

If a model author changes only architectural embellishments after its footprint
coverage was frozen, finalize the input-model hashes without pretending that
the generic meshes were regenerated:

```sh
python source/city/finalize_bund_patch_model_metadata.py \
  --patch work/bund-city-patches \
  --confirmations data/bund/bund-model-confirmations.json
```

This preserves `bund-landmark-exclusions.generation-snapshot.json` with the exact
hash used by existing mesh/state configuration values. It refreshes the final
runtime model hashes and proves that every exclusion ID, anchor, boundary and
geometry override remains unchanged. A changed footprint/ID fails this check
and requires an actual patch rebuild. `model-metadata-finalization.json`
records that distinction explicitly.
