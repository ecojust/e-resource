# Bund streetscape v4

This generator models the actual OSM road network around the detailed Bund buildings, together with the already verified four-tile west shoreline. Coordinates use metres: X east, Y up, Z south; WGS84 anchor 121.4862,31.2385.

Run from the installed `source/bund/street` directory with `python build_street.py`; the default project root is `Path(__file__).resolve().parents[3]`. For a staging copy pass the project root as the first argument. It uses the shared `source/city/build_district_models.py` mesh writer, numpy, shapely and mapbox-earcut. `road_geometry.py` must accompany the main generator.

`osm-roads.json` / `road-source.json` retain source vehicle ways, lane counts, oneway/tunnel/layer tags and the exact small Overpass query. `osm-street.json` retains mapped sidewalks and crossing axes. `bund-map.*.pbf`, `bund-map.geojson`, `tile-source.json` preserve the four water tiles, merged before extracting the physical west bank. No artificial tile-edge railing is permitted.

Road widths use OSM width if available, otherwise lane count with an explicit estimated lane width, otherwise a conservative class estimate. These are not surveyed lane widths. Center/white lane paint, drainage spacing and shoulder width are reconstruction estimates itemized per way in `bund-streets-road-check.json`. Road surfaces exclude the ten candidate `candidates[*].geometry` footprints from `../bund-candidates.json` (with 0.08m buffer) and water; this is only a Bund candidate-footprint check, not a full-city or all-neighbor-building check. Linked parts, related geometries such as the Bank of China western wing, and decorative mesh projections are outside this validation scope; underground tunnels are excluded entirely. Crossings use actual OSM crossing axes. No trees or temporary crowd barriers are invented.

Photos are visual references only: Suicasmo, 2025-05-01, CC0; URLs and supported details are in `street-reference-evidence.json`. Reference photographs are not required to rebuild. Original geometry/code MIT; OSM-derived street geometry ODbL-1.0, © OpenStreetMap contributors.

The raw GLB needs no external textures/buffers. Material names `BundStonePaving`, `BundRoadSurface`, `BundGraniteCurb` are stable hooks for the viewer's local PBR detail module. Compress losslessly for the webpage with `gltfpack -i bund-streets.glb -o bund-streets-web.glb -cc -noq -km -ke`. Geometry and shoreline audits are emitted on every rebuild.
