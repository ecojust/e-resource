# Bund street v4.5: bounded frontage infill and walkable surfaces

This isolated candidate adds the missing public sidewalk between ten source-verified Bund facade edges and the existing reconstructed arterial curb. It addresses the two visible white strips on either side of the old 4 m OSM-centreline sidewalk, without filling whole city blocks or inter-building areas. Main project, runtime, manifests and Git were not modified.

## Deliverables and integration

- `stage/source/bund/street/frontage_paving.py`: composable geometry module. After the existing planting build, before GLB packing, call `frontage, frontage_audit = add_frontage_paving(globals())`. It adds material `BundFrontagePaving`, suitable for the same pavement shader as the western sidewalk. Existing materials are untouched.
- `stage/source/bund/street/ground_sidecar.py`: call `export_ground_sidecar(ns, output, raw_path, web_path)` **after the final combined asset is written and copyright restored**. The source namespace must contain current street geometry and `frontage`. Final raw/web hashes are bound in the sidecar, so regenerate it after combining furniture/greenery. `extra_features` supports externally generated trees. Furniture uses the sibling `furniture.interaction()` exact primitive export and is deliberately not duplicated by approximate ground obstacles.
- `stage/source/bund/street/build_street.py`: working isolated integration example.
- `stage/source/bund/street/bund-streets.glb`: frontage-only candidate raw, 3,953,720 bytes / 74,066 triangles.
- `web/bund-streets.glb`: compressed candidate, 1,358,452 bytes. `-cc -noq -km -ke`, then preserve raw `asset.copyright`.
- `bund-streets-ground.geojson`: candidate sidecar fixture, 12 walkable surface features, two preserved planting-bed obstacles and eight exact frozen inner-ring exclusions.
- `frontage-plan-v4.5.png`: plan diagram. Brown shows added ground; grey shows previous ground. This is an explanatory geometry diagram, not a new aerial photograph.

Rebuild the isolated fixture with `python build_candidate.py`; run `python verify_preservation.py` and `python validate_ground.py`. The fixture script is a workspace helper; portable modules themselves have no absolute project paths and retain the existing source hierarchy.

## Evidence and dimensions

- Source facade outlines and edge selection: frozen `../bund-candidates.json`, with its hash in `bund-streets-frontage-check.json`. Only the selected east-facing main frontage edges are used. Western/rear-facing candidate edges are excluded.
- Public sidewalk continuity: unmodified, located 2010 CC0 Gary Lee Todd aerial (`references/bund17-18-19-aerial-2010-original.jpg`), building identities and road crossings already established in `planting-evidence.json`. Stone sidewalk / yellow curb morphology is corroborated by the 2025 CC0 views in `street-reference-evidence.json`.
- Shanghai Planning Bureau, 2008-05-27, [外滩滨水区城市设计](https://ghzyj.sh.gov.cn/ghgs/20191231/0032-174998.html): “适当加宽西侧人行道，增加沿历史建筑的公共活动和观景空间。” This supports the sidewalk function; it is a design intention, not an as-built survey.
- New area is **3,357.1269 m²**, bounded by each verified facade segment and the existing source-derived road edge. Exact original road/curb, water, candidate footprints, existing paving, pedestrian holes and both planting beds are subtracted. Road widths remain the existing lane-count estimates.
- New surface top **0.075 m** joins the existing west sidewalk. Road is 0.020 m, curb 0.140 m, yellow curb 0.143 m, existing promenade 0.035 m. These are consistent **model construction heights**, not Shanghai elevation measurements. Curb changes therefore remain below the runtime 0.2 m low-step threshold.
- New-only polygons receive a maximum 0.1 mm topology-preserving simplification before float32 triangulation. Observed Hausdorff distance is 0.0963 mm; area symmetric difference is 0.00181 m². This removes microscopic triangle inversions caused by almost-collinear double-precision points. All previous source/mesh geometry is unchanged.

The full fresh OSM API input is separately frozen at `../inputs/osm-map.json`. This candidate deliberately retains the previously published plan geometry and old frozen source version; it does not silently replace it with the newer extract. The fresh mapped steps way 519819881 has `layer=-1,tunnel=yes` and is not a surface stair or a basis for raised-platform geometry.

## Ground sidecar contract

Top level: `schema_version:1`, `owner:'bund-streets'`, `origin:[121.4862,31.2385]`, `raw_model_sha256`, `web_model_sha256`. Geometry is WGS84; vertical coordinates are world metres relative to this asset's zero datum. Surface properties include `role:'walk-surface'`, `height_world_m`, `base_world_m`, `top_world_m`, explicit `blocks_walk:false`, `blocks_camera:false`, and source/evidence status. Polygons and their holes are preserved.

The two source-classified planting beds block walk/camera only over their actual low vertical extent, 0.005–0.215 m. Other frozen relation inner rings are exact **walk-only unmodeled-opening exclusions**; their -1…2 m vertical interval is an interaction rule, never a claimed physical wall. Furniture collision should use its actual emitted primitive data. A missing surface remains unknown (`null`) so the general district fallback can continue outside this owner. Only activate data while the same-hash model owner is loaded and visible.

## Checks and limits

`geometry-preservation.json`: all 14 previous material definitions and full position, normal, and index arrays match exactly. Added 1,152 vertices / 684 triangles; the new mesh is closed, outward-facing, finite and has no degenerate triangles.

`compression-validation.json`: all 74,066 oriented triangle positions match decoded web geometry exactly; maximum normalized normal difference is 0.00018016. Single files are far below 100 MB.

`ground-validation.json`: every sidecar surface matches actual raw top faces at its declared height (0.15 mm float32 edge tolerance); ground/obstacle footprint overlap is numerical noise below 1e-6 m². Existing mapped openings and both beds are excluded from walk surfaces.

This candidate does not claim a surveyed floodwall section or a whole raised-platform reconstruction. The 2008 planning source explicitly describes multiple levels, platforms and gentle ramps, and the 2011 promenade photograph shows real steps/retaining forms. Those establish the missing morphology but do not yet locate a particular Bund18 stair flight with defensible dimensions. No unrelated staircase is transplanted here, and the 4.7 m Financial Plaza value is not applied to this northern location.
