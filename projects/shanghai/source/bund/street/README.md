# Bund streetscape v4

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


## v4.2 Bund18 connector and paving finish

`connector_paving.py` adds 188.917m² between the existing road/shoulder/curb edge and mapped pedestrian exterior, bounded by crossing ways 745201529 and 226657312. This is **estimated construction extent**, not a measured new footprint. `bund18-connector-source.json` freezes three relevant OSM elements and records the upstream query/extract provenance. Both unidentified recesses in exterior way 160033684 are excluded, along with source inner holes, known entrances/steps, existing pavement, roads, water and the ten candidate footprints. The two recesses remain unmodeled; they are not asserted to be staircases.

The slab color is neutral grey; the browser uses estimated 1.20×0.60m slabs/4mm joints and subdued CC0 granite grain. See `references/README.md` for the 2011 morphology reference. Actual promenade height, stairs and ramps remain outside this change.

Run `python source/bund/street/build_street.py` from the project to rebuild; the connector helper and frozen source must accompany it. `bund-streets-connector-check.json` and `.geojson` record bounds and exclusions. The installed-layout rebuild and original-mesh prefix checks are in `data/bund/validation/*v4.2*`. The viewer's actual GLTFLoader/Meshopt comparison verifies decoded vertex positions exactly; exporter processing yields a maximum normal-direction difference of 0.0104°, recorded separately rather than called bit-identical.
