# V11 independent modern-model registration preparation

This tool prepares **one model-only registration draft** for either `jiading-shanghai-auto-museum` or `minhang-baoyugang-library`. The two supplied requests remain pending. No actual model is accepted by this preparation work. It does not launch Blender or a browser, compress geometry, modify MAIN, normalize against live owners, install files, or use Git.

```sh
python /workspace/shanghai_expansion/building-by-building-v11/packaging-preparation/registration/prepare_registration.py \
  --request /absolute/path/to/actual-registration-request.json \
  --output /workspace/shanghai_expansion/building-by-building-v11/packaging-preparation/registration/NEW-ACTUAL-RUN
```

The output must be a new directory below this registration directory. Every actual descriptor uses `{source: absolute_path, bytes: positive_integer, sha256: lowercase_64_hex}`. Every referenced regular file must exist, match both size and hash, and be strictly below **100,000,000 bytes**. Symlinks, path traversal and input drift are rejected. Unknown actual geometry report schemas fail closed. Pending requests or targets create no output directory.

## Request and actual target

Request schema: `modern-model-registration-request-v11`. The exact keys are `schema`, `building_id`, `inputs_ready`, `source_roles`, and these actual descriptors:

| Descriptor | Meaning |
| --- | --- |
| `target_spec` | Same ready target bytes used for the actual package and decoder |
| `source_geometry` | Existing exact owner geometry freeze; never replace with a new outline |
| `source_freeze` | Frozen author files and dependencies |
| `tool_source_freeze` | Separate explicit frozen decoder/checker/registrar dependencies |
| `package_record` | Actual `precise-building-packaging-v1` four-asset package |
| `decoded_report` | Actual `modern-actual-decoded-package-v11` report |
| `independent_raw_review` | Original independent `modern-actual-finite-checks-v1` raw result |
| `native_report` | Actual author native report and three existing rendered images |
| `root_native_review` | Root's actual review of those three images |
| `navigation` | A reviewed current-raw observation-point proposal; browser still pending |
| `prebrowser_review` | Nine substantive source/geometry/size review sections written from actual evidence |
| `source_delivery_whitelist` | Exact permitted source and licensed-photo delivery files |

`inputs_ready` must be literal `true`; the target must have `status: ready`, `registration_allowed: true`, and `browser_accepted: false`. Its current `actual` descriptors must match the request. Package and decoded target hashes must equal this exact target SHA. Fill a new ready target before packaging; changing it afterward requires a newly bound package/decoded result. The author `raw_geometry` sidecar is bound directly. No optional museum metadata or nonexistent library asset-metadata filename is guessed.

Set `registration_allowed: true` in the final ready target **before** packaging. This authorizes attempting these strict registration checks; it is not an acceptance result. Never flip it after package/decoder hashes have been bound. Pending targets stay false and are always rejected.

`source_roles` contains exactly `builder`, `calibration`, and `renderer`, each an actual descriptor present in the author source freeze. Calibration must bind `source_geometry_sha256`. `tool_source_freeze` has schema `modern-packaging-tool-source-freeze-v11`, `status: frozen`, and a nonempty `files` list of actual descriptors. External helpers stay in this separate freeze; they are not inserted into an already frozen author manifest. Decoder, bridge, actual checker files and the three registrar implementation files must appear in it.

## Independent geometry and actual decoding

The selected target supplies actual `source_structure_report` and `probe_set` descriptors. The only supported raw report chain is:

1. `modern-actual-raw-structure-v1`: actual current raw bytes, model ID, geometry/calibration/author-freeze SHA, every nonempty serialized part, closed oriented positive components, flat normals at the unchanged 0.001 degree policy, and original checker descriptors.
2. `modern-actual-finite-checks-v1`: the original `run_finite_checks.py` raw result; exact source binding, the actual structure report, the frozen `modern-finite-requests-v1` request set, nonempty actual results for every requested check, and actual oriented-position comparisons for every retained part.
3. `modern-actual-decoded-package-v11`: actual raw/web/LOD descriptors in `assets`; optional authored LOD in top-level `authored_lod`. Exact oriented position/material preservation, modern material preservation, selected LOD policy, actual model bounds and current package/target/source SHA are required.
4. `modern-actual-decoded-finite-suite-v11`: an actual independent finite result for **each** selected role. Each `modern-actual-decoded-finite-role-v11` contains the original full finite-engine result, current asset bytes, array manifest, engine lock, bridge, and request binding.

No raw index ranges are treated as compressed geometry evidence. Actual decoded semantic arrays are reconstructed by oriented position/material/normal matching, then independently audited. Their small `modern-decoded-semantic-arrays-v11` manifests and finite/retention reports remain permanent. Derived Float64 chunks may already be deleted after their actual checks: the registrar verifies their recorded hashes, sizes, triangle coverage and retention declaration, **without demanding those deleted buffers or publishing them**.

The museum allows compression-only LOD. Library authored subtraction may omit only the explicitly approved `fine-tile-joints-N` labels, with retained geometry proved individually. No general QEM or historical geometry acceptance is permitted. Finite proofs do not establish photographic likeness, complete collision freedom, public access or physical structural safety.

## Native and root visual review

Supported actual author schemas are `auto-museum-native-render-v11` and `pao-yue-kong-library-native-render-v11`, bound to their respective target IDs through the schema plus current raw/native and frozen builder/calibration/renderer hashes. The author reports have no required `id` field. Their generated `human_visual_review_passed: false` is expected and is never rewritten. Ground used for rendering must be excluded from actual model bounds.

Root review schema `modern-root-native-visual-v11` requires:

- `building_id`, `reviewer: root`, `passed: true`, `actually_viewed: true`, `final: true`, `browser_accepted: false`;
- exact `raw` and `native` size/SHA, `native_report_sha256`, `source_geometry_sha256`;
- exactly three `actually_viewed_images` with unique actual PNG hashes and roles `full`, `detail`, `rear`; each carries `file`, `bytes`, `sha256`, `role`, `actually_viewed: true`;
- nonempty `scope` and `limitations`.

Each image must match the native report render row and camera. Image basenames resolve beside both the native report and root visual review; placing the review next to the renders avoids copies. A root declaration does not replace the actual PNG bytes. No native acceptance is inferred from Blender's file header alone.

## Nine prebrowser sections and navigation

`modern-prebrowser-review-v11` requires literal `passed: true`, `actually_reviewed: true`, `browser_accepted: false`, a reviewer, and current top-level SHA bindings for source geometry, raw, package record, decoded report, independent raw report, native report, root native review and source freeze.

Its `sections` must contain exactly `source_photos`, `identity_footprint`, `height_evidence`, `visible_facade_opening_grid`, `roof`, `texture_mapping_qa`, `geometry_proof`, `size_proof`, `uncertainty`. Each section needs current `building_id`, `passed: true`, `geometry_input_sha256`, `raw_sha256`, `package_record_sha256`, nonempty `scope` and a nonempty list of actual evidence descriptors. Additional bindings are explicit in the pending template and `contracts.py`: full declared-photo SHA coverage; current independent-raw and decoded evidence for geometry; decoded/package evidence for texture and size; actual grounded bounds and estimated height for height. A separate actual review provides these sections; this tool does not manufacture substantive reviews from a passed geometry result.

`registration` in that review supplies a declared `primary_photo`, `architecture_style` and `detail_note`; `limitations` remains nonempty. Source photographs must be actual individually licensed JPEG/PNG reference files. Native renders are not replacements for source photography. Official/manufacturer URLs do not imply permission to redistribute their images.

Navigation schema `modern-source-bound-navigation-proposal-v11` requires current `building_id`, `status: ready`, `source_geometry_sha256`, `raw_sha256`, the exact source `anchor`, `navigation`, `scope`, `limitations`, and `browser_accepted: false`. A listed point needs finite lon/lat and bearing. The earlier source-only navigation preparation is not an actual-ready proposal; the registrar does not assert that an estimated point is an entrance or passes browser collision checks.

## Public source whitelist and outputs

`modern-model-public-source-whitelist-v11` requires `building_id`, `status: ready`, author/tool freeze SHA, `document_roles`, and nonempty `files`. `document_roles` is exactly `{readme, build, attribution}`, each naming a real whitelisted source document; one README may also contain build instructions. No nonexistent DELIVERY/BUILD/COPYRIGHT filename is assumed.

Every file row has canonical destination `file`, actual `source/bytes/sha256`, `kind`, explicit `license/license_url`, and `redistribution_basis` for source/evidence. Only these kinds are accepted:

- `authored-source`: exact author **or tool** frozen dependency, under `source/precise/BUILDING_ID/`;
- `generated-evidence`: JSON/Markdown evidence under the same source prefix; executable tools cannot bypass the source freeze under this category;
- `licensed-reference`: exactly a declared licensed package photograph under `assets/references/precise/BUILDING_ID/`.

Case-fold collisions, unknown whitelist fields, symlinks, generic HTML/text snapshots, unlicensed photo bytes, encoded image/PDF snapshots in source documents and files outside the one-model namespace are rejected. Explicit LICENSE/NOTICE/font-license text files are permitted; cached public pages are not. URL citations and factual metadata may remain. Research-only manufacturer roof images are excluded.

Successful preparation writes five new JSON files: `prebrowser-acceptance-summary.json`, `registration.draft.json`, `model-metadata.json`, `delivery-manifest.json`, `input-lock.json`. The draft follows `precise-registration-input-v1`, with nine actual prebrowser sections and **browser_proof pending**. The delivery manifest references exactly four model assets plus whitelisted source/reference files and three generated delivery documents; it copies no payloads. Before installation the root must separately validate destination guards. Outputs explicitly retain `browser_accepted: false`, `registered: false`, and `installed: false`. No live owner/catalog/navigation output is generated.

Generated destinations are reserved before any writes. An `INCOMPLETE` marker remains if an error occurs during output writing or the final drift check. A usable result requires an actual `input-lock.json`, a successful process exit, and absence of that marker; partial output must never be installed. All generated JSON is also checked for forbidden encoded snapshots and the strict file-size limit.

Run bounded contract tests with `python tests/test_guards.py`. They exercise pending-input rejection and local schema/hash/path guards only; they are not model, native or browser acceptance.
