# Precise-building packaging and registration proposals

See [the ordinary-building source overview](../README.md). Both Python tools are
preserved byte-for-byte from the reviewed staging versions. Run from the project
root; supply actual independent inputs and a new external output directory:

```sh
PROJECT="$PWD"
python -B source/precise/tooling/package_precise_building.py \
  --spec /absolute/path/to/package-spec.json \
  --raw /absolute/path/to/model.glb --native /absolute/path/to/model.blend \
  --project "$PROJECT" --output /absolute/path/to/new-package \
  --gltfpack /absolute/path/to/gltfpack \
  --shared-helper "$PROJECT/source/bund/photo-rebuild-v6/common/package_building.py"
```

The explicit shared-helper argument is required in this published layout; the
original default refers to its old work directory. Its project dependency is
`tools/build_bund_lods.py`. Packaging preserves original photographs and licenses,
keeps each asset below 100 MB, and produces an isolated package. It does
not inspect native Blender geometry, prove photo accuracy, install or publish.

The frozen registration tool restricts output to a new child of its own directory
while also forbidding any output inside the project. Preserve that safeguard by
copying **only the unchanged script** to an external review directory first:

```sh
REVIEW_TOOL=$(mktemp -d)
cp source/precise/tooling/generalize_precise_registration.py "$REVIEW_TOOL/"
python -B "$REVIEW_TOOL/generalize_precise_registration.py" \
  --input /absolute/path/to/reviewed-registration-input.json \
  --project "$PROJECT" --districts "$PROJECT/data/districts.json" \
  --output "$REVIEW_TOOL/proposal"
```

Do not invent placeholder evidence to make this command pass. Explicit identity,
district/provider/source URL/license, source photos and asset records are required.
Ten acceptance stages cover photos/licenses, identity/footprint, height evidence,
visible opening grid, roof, texture QA, geometry, size, browser proof and stated
uncertainty. One building must bind to its complete exact macro/local owner;
unreviewed linked building parts/residuals require further mapping, not deletion.

The registration output is a **proposal**, never a navigation edit or automatic
publication. Its accepted records still need current runtime metadata (LOD counts
and thresholds, original-photo orientation/material scope/image counts), the
audited complete replacement registry, guarded integration and actual catalog
lifecycle verification. `--allow-draft` only emits review material and excludes
pending buildings from the runtime catalog. Whole-city procedural buildings do
not become photo-level completed buildings through registration.
