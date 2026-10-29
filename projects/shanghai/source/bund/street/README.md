# Bund streetscape · v6

## Current v6: three additional public frontages

The single street prop now includes **844.5004 m²** of bounded, estimated paving immediately in front of 日清 (05), 中国通商 (06) and 交通银行 (14). Each confirmed front edge projects outward to the existing rendered road edge; original paving, asphalt, curbs, water, mapped openings, beds and known building outer envelopes are excluded. This is not a new surveyed footprint and creates no interior courtyards, steps or side-alley paving. Surface height remains the model west-sidewalk level **0.075 m**.

The v5 raw geometry and all 3,479 furniture/tree obstacle records are preserved. The append adds **352 triangles and 3 walkable surfaces**: current combined totals **138,830 triangles**, raw **7.47 MB**, web **2.46 MB**, and **25 sidecar features**. The old raw binary prefix is unchanged; production Three/Meshopt decoding confirms all old web triangles remain and all new raw/web positions match exactly. This does not assert bit-identical web normals. The existing sidecar filename `street-interaction-v5.json` is retained for compatibility, with updated model SHA bindings.

Use the **project-level** current entry point:

```sh
python tools/build_bund_street.py --gltfpack /path/to/gltfpack
# To rebuild without installing:
python tools/build_bund_street.py --gltfpack /path/to/gltfpack --output /path/to/fresh-output
```

The entry validates its frozen baseline dependencies and stages the complete append before replacing any installed file. [frontage-v6/README.md](frontage-v6/README.md) documents the source dependency and validation. The raw GLB is the editable mesh artifact; this procedural street has **no Blender .blend source file**. Both source-directory raw/web outputs are synchronized with the runtime assets. Direct `build_street.py` and the archived baseline driver reconstruct the historical v5 base only and must not be used as the final v6 entry. The v5 validation/browser record below remains historical; **v6 paving browser review is pending**.

## Historical v5 ground, greenery and photo-guided fittings

The v5 street build added **3,357.13 m²** of bounded west-side frontage paving across the ten verified Bund facades. `frontage_paving.py` interpolates only between selected source facade edges and the existing road edge, subtracting previous paving, carriageway, curbs, buildings, water, source holes and the two planting beds. This repairs exposed basemap strips beside the old four-metre footway; it is an estimated public-sidewalk extent, not a newly surveyed polygon. Source evidence and per-frontage checks are in `bund-streets-frontage-check.json` and `.geojson`.

`street_furniture.py` replaces the old fittings with photo-guided tapered lanterns, curved black road lamps, eight thin railing rods, inclined supports and capped granite piers. The 2011 Bohao Zhao CC BY 3.0 and 2025 Suicasmo CC0 originals support form. Their shape dimensions and retained spacing remain estimates: 24 promenade lamps, eight road lamps and 95 piers are the modeled inventory, not a measured present-day inventory. `furniture.audit()` records assumptions; `furniture.interaction()` records the exact emitted boxes, rod segments, lathe sections and lamp heads used for collision.

The two v4.3 beds retain their exact frozen quadrilaterals. The greenery module adds seven trees, supports and short grass from the located Gary Lee Todd 2010 CC0 photograph: four trees in the southern bed and three in the northern bed. Some roots are obscured and inferred from visible trunks. Source controls retain the uncertainty; no tree species or 2026 survey is claimed. Code/data and downloadable geometry: [greenery source](greenery/README.md). The live instances belong to the same `bund-streets` owner and are not loaded again from the downloadable GLB.

`ground_sidecar.py` exports actual walkable slab polygons with world-Y heights and preserved holes. Road top is 0.020 m, west sidewalk/new frontage 0.075 m, curb 0.140 m (yellow paint to 0.143 m), and current promenade 0.035 m. These are model construction levels, not Shanghai elevation measurements. The two bed borders reach 0.215 m; exact source inner openings remain walk-only exclusions. Final interaction data is `data/bund/street-interaction-v5.json`, bound to the final raw/web model hashes. Furniture and tree obstacles come from their corresponding emitted geometry. Runtime activates this data only with its loaded, visible street owner; unknown ground continues the general map fallback.

The 2008 Shanghai Planning Bureau text describes a widened western sidewalk and multiple riverside levels connected by ramps. The located photos confirm such structures, but this version has not reconstructed the complete floodwall platform section. Underground OSM steps way519819881 (`layer=-1`, `tunnel=yes`) is not used as a surface stair. The newly frozen `street-v5-inputs` extract is kept distinct from previously published street inputs.

The asphalt shader now retains full-surface colour and roughness variation farther into the middle distance, while fine normals still fade nearby. It reuses the existing Poly Haven CC0 scans; no source photo is a paving or foliage texture. `BundFrontagePaving` receives the same restrained stone surface treatment as the adjoining sidewalk.

Rebuild with the existing `build_street.py` entry point, then compress using `gltfpack -cc -noq -km -ke` and restore `asset.copyright`. Regenerate interaction data after the final combined mesh and hashes are available. Historical v5 combined street record: 138,478 triangles; raw 7.45 MB; web 2.45 MB. Installed files passed the project asset check. Historical v5 browser/interaction status: **通过：7棵树、1个街景归属、12块地表和3,489个碰撞体；铺装局部Y=0.035m、实际行走、离开与返回均正确**. Browser evidence is in [the final report](../../../data/audit/city-detail-v5/release/browser.json). Geometry/source validation is in `data/bund/validation/street-v5.json`; source photographs retain their original bytes and licences.

The sections below are historical build records; their unmodeled-recess, no-trees and flat-ground notes describe those versions and are superseded where the v5 section explicitly says so.

This generator models the actual OSM road network around the detailed Bund buildings, together with the already verified four-tile west shoreline. Coordinates use metres: X east, Y up, Z south; WGS84 anchor 121.4862,31.2385.

Run from the installed `source/bund/street` directory with `python build_street.py`; the default project root is `Path(__file__).resolve().parents[3]`. For a staging copy pass the project root as the first argument. It uses the shared `source/city/build_district_models.py` mesh writer, numpy, shapely and mapbox-earcut. `road_geometry.py` must accompany the main generator.

`osm-roads.json` / `road-source.json` retain source vehicle ways, lane counts, oneway/tunnel/layer tags and the exact small Overpass query. `osm-street.json` retains mapped sidewalks and crossing axes. `bund-map.*.pbf`, `bund-map.geojson`, `tile-source.json` preserve the four water tiles, merged before extracting the physical west bank. No artificial tile-edge railing is permitted.

Road widths use OSM width if available, otherwise lane count with an explicit estimated lane width, otherwise a conservative class estimate. These are not surveyed lane widths. Center/white lane paint, drainage spacing and shoulder width are reconstruction estimates itemized per way in `bund-streets-road-check.json`. Road surfaces exclude the ten candidate `candidates[*].geometry` footprints from `../bund-candidates.json` (with 0.08m buffer) and water; this is only a Bund candidate-footprint check, not a full-city or all-neighbor-building check. Linked parts, related geometries such as the Bank of China western wing, and decorative mesh projections are outside this validation scope; underground tunnels are excluded entirely. Crossings use actual OSM crossing axes. No trees or temporary crowd barriers are invented.

Photos are visual references only: Suicasmo, 2025-05-01, CC0; URLs and supported details are in `street-reference-evidence.json`. Reference photographs are not required to rebuild. Original geometry/code MIT; OSM-derived street geometry ODbL-1.0, © OpenStreetMap contributors.

The raw GLB needs no external textures/buffers. Material names `BundStonePaving`, `BundRoadSurface`, `BundGraniteCurb` are stable hooks for the viewer's local PBR detail module. Compress without vertex position quantization or triangle simplification for the webpage with `gltfpack -i bund-streets.glb -o bund-streets-web.glb -cc -noq -km -ke`. Geometry and shoreline audits are emitted on every rebuild.

The extra riverside paving follows OpenFreeMap transportation polygon feature `21420773`, unioned across the same four retained tiles and clipped to the Bund street crop. Water, candidate footprints, road surfaces, existing pavement and curbs are subtracted. Top height is 0.035m; `bund-streets-paving-check.json` records source and overlap tests. The feature number is an MVT ID, not a claimed OSM way ID.

## Static traffic illustration

The original procedural vehicles are deliberately sparse and static, not a live traffic feed or a claim about real parking or a bus route. Source lane directions/counts follow the actual two OSM carriageways; vehicle appearance, color and presence are illustrative. The module uses eight InstancedMesh batches, no animation loop or extra light.

Regenerate positions from the installed project with `python source/bund/street/generate_traffic.py`; run the CPU geometry/resource validation with `node source/bund/street/validate_traffic.mjs`. Both default to the relative project root and can accept an explicit project-root argument. The validation transforms every actual component vertex into its vehicle frame, checks the dimensions against the previously road-contained envelope, checks ground clearance, and confirms idempotent disposal. It does not open a browser.

Outputs: `data/bund/traffic-v4.json` and `data/bund/validation/traffic-v4.json`; rendering module: `src/street-traffic.js`. The mapped-road placement excludes crossing/junction safety zones, water and the ten candidate footprints. All geometry and bounds are authored locally; there are no downloaded car models, brand marks or external textures.

## Basemap road stroke replacement

`generate_basemap_remainders.py` reads only the four preserved MVT files, extracts numeric features `403013682` and `4489314812` from `transportation`, removes duplicated tile-buffer portions by clipping to the nominal tile cores, and unions the centerlines before subtracting the exact street crop. All portions outside the crop are retained with their original style attributes and `source_mvt_id`; neither the map centerline nor the GLB road is widened. Run `python source/bund/street/generate_basemap_remainders.py` to regenerate `data/bund/basemap-road-remainders-v4.geojson` and its `.json` metadata. Length partition and outside-coverage checks run during generation.

`src/street-basemap.js` exports `async createStreetBasemapReplacement(map)`, returning `setActive(bool)`, `getState()` and `dispose()`. The owner must activate it only when the local street GLB has loaded successfully and is visible, walk mode is active, and zoom is at least 18. While active, only the two numeric IDs are excluded from the original `road_secondary_tertiary` and casing layers; exact clones draw the retained outside fragments. Disable on model unload/failure, overview or lower zoom; original filters are restored. Call `dispose()` before `map.remove()`. Repeated identical activation requests do not rewrite filters.

Run `node source/bund/street/validate_basemap_replacement.mjs` for the small mock test of enable/disable, duplicate calls, style preservation, rollback on load/install/filter failure, and disposal. Both scripts use the project-relative default root and accept an explicit root argument. This is a cartographic rendering correction, not additional physical road modeling.


## Historical v4.2 Bund18 connector and paving finish

`connector_paving.py` adds 188.917m² between the existing road/shoulder/curb edge and mapped pedestrian exterior, bounded by crossing ways 745201529 and 226657312. This is **estimated construction extent**, not a measured new footprint. `bund18-connector-source.json` freezes three relevant OSM elements and records the upstream query/extract provenance. Both unidentified recesses in exterior way 160033684 are excluded, along with source inner holes, known entrances/steps, existing pavement, roads, water and the ten candidate footprints. The two recesses remain unmodeled; they are not asserted to be staircases.

The slab color is neutral grey; the browser uses estimated 1.20×0.60m slabs/4mm joints and subdued CC0 granite grain. See `references/README.md` for the 2011 morphology reference. Actual promenade height, stairs and ramps remain outside this change.

Run `python source/bund/street/build_street.py` from the project to rebuild; the connector helper and frozen source must accompany it. `bund-streets-connector-check.json` and `.geojson` record bounds and exclusions. The installed-layout rebuild and original-mesh prefix checks are in `data/bund/validation/*v4.2*`. The viewer's actual GLTFLoader/Meshopt comparison verifies decoded vertex positions exactly; exporter processing yields a maximum normal-direction difference of 0.0104°, recorded separately rather than called bit-identical.

## Historical v4.3 Photo-classified planting strips

The two previously unidentified recesses are now interpreted as shallow planting beds from the located 2010 CC0 aerial photograph by Gary Lee Todd, Ph.D.; `planting-evidence.json` records the source, unchanged image hash, building/crossing landmarks and identification limits. `planting_beds.py` uses the exact two frozen source quadrilaterals. Stone edging is estimated at 0.18m above the original pavement; soil/grass surfaces are 0.08/0.09m on the existing datum. No trees or complete raised-promenade topography are added. See `bund-streets-planting-check.json` for the tested overlaps, including small nonzero overlap with preserved quantized MVT paving. This supersedes the earlier unknown-recess classification, while the v4.2 connector geometry stays unchanged.
