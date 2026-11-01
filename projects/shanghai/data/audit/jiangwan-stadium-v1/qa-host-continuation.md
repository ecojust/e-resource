# Jiangwan browser QA host and frozen inputs

The executable requires an explicit `--run`, a frozen QA contract, and the new
public metadata/manifest. The completed run is recorded in `browser.json`. `--preflight` reads only local
files. One retained host/page owns all later WebGL work; the continuation helper
does not attach a second controller.

The preparation is adapted from the completed City Hall QA, with old bridge,
source 525, seven-owner and count-77 assumptions removed. The new contract binds
the independent footprint review SHA and supplies the actual ring/source facts.

Each `context_sources` item supplies `source_id`, `source_layer`, `macro_id`,
`local_id`, `name`, `source_geometry_wgs84`, and `roof_probe` containing `wgs84`,
`height_m`, `height_is_map_estimate`, and `actual_native_triangle_verified`.

Each `near_groups` item supplies the exact production `group_id`, `macro_id`,
`feature_local_ids`, `clip_feature_local_ids`, `triangles`, `near_path` (repository
or project-relative), `bytes`, and `sha256`. At least one accepted visual view must
exercise every required group and verify its actual HTTP response bytes.

`ground_probes` contain a descriptive `name`, `wgs84`, and `expected` (`null` for
open field/entry or `building` for low solid positive controls). These run against
the production scene's real collision cache, in addition to the independent static
mesh/source checks. They do not enable walking or certify stairs/interiors.

`visual_views` requires keys `openField` and `entry`, each with `label`, `note`,
`whole_model` (boolean), `expected_variant` (`full` or `distant`), `near_group_indices`, `probe` (`wgs84`, `height_m`), and
`camera` (`center`, `zoom`, `pitch`, `bearing`, `elevation`). Actual view images are
inspected while the host waits. A projection or owner-state assertion never
substitutes for observing open field, arch aperture, or neighboring structures.

Pixel review controls contain `viewKey`, `captureFile`, `captureSha256`,
`scriptSha256`, `captureControlSha256` (null for the original script),
`runGeneratedAt`, `accepted`, and `observation`. A rejected image additionally
contains a full replacement `camera` with bounded zoom/pitch. Controls are copied
to immutable SHA-named audit records; the active control is removed after the host
closes. Stale run/script/file decisions are rejected before use.

Required coverage: auxiliary full/LOD/mobile and four download bytes, directory
and all 78 runtime routes, main default desktop/mobile, actual original city near
groups, visible field and entry, retained neighboring source identities, real
full/LOD swaps, GPU/no-error state, 78 all-present and independently hit-testable
number sprites at 320×568 and the real worst-title free area, then native CDP
touch from Green Tile City Hall to this stadium.

All public model/source/production inputs must freeze before the run. Native or
heavy geometry jobs stop first. Frame gates use actual render events (three
frames/two stable comparisons) and all queues/pending feature writes equal zero;
900-second budget with 30-second progress is retained for software WebGL. Final
screenshots are hash-bound and separately opened by QA and root.

Run from the repository root with the installed Playwright module path:

```sh
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules node projects/shanghai/data/audit/jiangwan-stadium-v1/qa-browser.cjs --preflight
NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules node projects/shanghai/data/audit/jiangwan-stadium-v1/qa-browser.cjs --run
```

The local audit server serves edited working files first and missing sparse files
from immutable baseline `96e4dfaff588222475c25a66af1c84a24b45a475` using a separate
revision cache. Explicit source HTTP requests before browser launch are labeled
separately from actual page-loaded source receipts. A global fitted default view
may use the distant asset; the dedicated near/entry/passage views require full.
The two stand display corrections remain separately owned (25 and 20 triangles),
and collision boundary capacity is a CPU validation budget, not the GPU clip
texture budget. The global static total is 192; a screenshot reports its actual
active rows instead of claiming all catalog corrections were active at once.
