# Six-target precise-owner near rebuild

This package replaces only exact frozen owners for Bund 05/06/07/09/14 and
Qingpu Beidajie 222. It preserves 49 neighbors in four near models across two
macros. The ordinary Qingpu footprint is an Overture Zenodo/East Asian Buildings
provider feature, not a fabricated OSM way. Source footprints/heights and original
full macro neighbors are retained. This is ownership geometry, not a claim that
the 1,796,419 source buildings are photographically reconstructed.

The original staging README and its whitelist are preserved in `evidence/` as
historical records. This README supersedes their staging-relative command paths.
The generator and validators are byte-identical to that audited source.

From this directory, with a complete published project checkout (including the
two required city-detail macros), create a fresh output **outside the project**:

```sh
PROJECT="$(cd ../../../.. && pwd)"
GLTFPACK=/absolute/path/to/gltfpack
NEW_OUTPUT=/absolute/path/to/new-six-target-output
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
python build_precise_overrides.py --project "$PROJECT" --output "$NEW_OUTPUT" \
  --geometry-input-root ./inputs \
  --ids bund05 bund06 bund07 bund09 bund14 qingpu-beidajie-222 \
  --gltfpack "$GLTFPACK"
node verify_override_geometry.mjs "$NEW_OUTPUT/geometry-comparison-input.json"
node verify_override_runtime.mjs "$PROJECT" "$NEW_OUTPUT/precise-buildings-v6.json"
SHANGHAI_PROJECT="$PROJECT" python -B test_precise_generator.py -v
```

Python requires NumPy and Shapely 2.x; Node requires `node:module.registerHooks`.
The original assets use gltfpack 1.0, gzip level 6, mtime 0. Use the pinned engine
and original city detail configuration. `dependencies.json` lists exact project
code SHAs and frozen macro references; missing macro inputs must be obtained from
the published project rather than synthesized. No new geometry is inferred from
the evidence reports. The generator verifies baseline input hashes, recreates all
per-feature references and writes a new comparison input. Historical absolute
paths in audit JSONs are not needed for this rebuild.

Run the independent decoded geometry validator before using any generated
registry. Positions, materials, oriented triangles and multiplicity must match;
the recorded tiny normal tolerance is explicit in the audit, not bit identity.
The generated geometric registry does not create an accepted ordinary catalog.
The separately reviewed registration owner supplies accepted navigation/catalog
and the final top-level registry; this package never auto-installs any of them.
