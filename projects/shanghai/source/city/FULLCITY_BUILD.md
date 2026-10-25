# Shanghai full-city building models

`build_fullcity_models.py` converts the downloaded and globally deduplicated
Overture building footprints into geographically anchored GLB meshes. It does
not invent a street grid. This is a footprint extrusion model (LoD1): decorative
façades in the viewer are a visualization, not recovered surveyed architecture.
The five individually modeled landmarks replace explicitly verified source IDs.

## Inputs and rebuild

Python dependencies: `numpy`, `mapbox-earcut`, `shapely`, `pyproj`, `pyarrow`, and
`rasterio`. Default output compression also requires `gltfpack` with meshopt
support. Run the source acquisition scripts first and keep the matching height
source lockfile beside their source datasets.

```sh
python source/city/build_fullcity_models.py \
  --input data/fullcity-raw \
  --output assets/city \
  --gltfpack gltfpack \
  --height-raster data/heights/shanghai_ghsl_anbh_2018_3arcsec.tif \
  --cnbh-raster data/heights/alternatives/cnbh_2020_shanghai_core_dm.tif \
  --cmab-shards data/heights/cmab/shards \
  --height-lock data/heights/height_sources_lock.json \
  --landmark-exclusions data/landmark-exclusions.json \
  --parent-residuals data/parent-residual-overrides.json \
  --workers 2
```

Use `--no-compress` to rebuild ordinary GLBs for applications that do not support
`EXT_meshopt_compression`. This includes Blender installations without a meshopt
import extension. Keep compressed browser assets and editor rebuilds in separate
output directories. All individual files have a hard limit of 100,000,000 bytes;
the normal precompression chunk target is 9 MB.

## Coordinates and partitioning

Input geometry is EPSG:4326/WGS84. Each output tile has an explicit longitude and
latitude origin. Mesh coordinates are local metres, X east, Y up, Z south, using
Web Mercator differences scaled by the cosine of the origin latitude. This
avoids storing city-sized Mercator coordinates in float32 attributes.

All fragments sharing a source-layer/UUID key are merged before meshing. Whole
buildings are assigned to one owner cell; buildings crossing cell edges are not
artificially sliced. `geographic_bbox` describes the owner grid rectangle while
`geometry_bbox` describes the actual expanded geometry. Oversized cells split
at the spatial median between features, preserving whole buildings. Polygon
holes are retained by earcut triangulation. Duplicate adjacent points below
1 mm and degenerate rings below 0.01 m² are rejected; there is no deliberate
footprint simplification. A feature with no renderable polygon fails visibly.

The mesh compressor uses 16-bit position and 12-bit normal quantization, retains
materials and names, and performs no triangle simplification. Every compressed
GLB is checked for finite accessor bounds, valid headers, correct lengths, and
unchanged triangle count. On roughly 2 km cells, position quantization is of the
order of centimetres, finer than the source footprint resolution.

The residual-parent source pass suppresses 42 entire residuals with area at most
1 m² (22.635866 m² combined). It retains 402 residual parents totalling
953,690.012 m², including narrow shapes. The mesh precision threshold described
above separately removes 94 tiny residual polygon components totalling only
0.104702 m² (largest 0.009373 m²). The original residual GeoJSON retains those
components. These mesh omissions are explicitly recorded as degenerate polygons;
they do not remove any of the 402 restored parent features.

## Height provenance

Priority is source height, source floor count × 3.2 m, CMAB matched predicted
rooftop height, CNBH 2020 10 m estimated raster height, GHSL 2018 regional mean,
then an explicitly recorded 12 m visualization default. Source `min_height`
is retained for elevated building parts.

CMAB requires intersection-over-union ≥ 0.60 and both footprint coverage
fractions ≥ 0.70. Near-equivalent candidates with inconsistent heights are
rejected. CNBH uses the median of positive raster pixel centres inside the
footprint, with an interior representative-point fallback for small footprints.
The compact CNBH raster contains decimetres with embedded scale 0.1; the sampler
reads that scale. GHSL is approximately 80 × 93 m at Shanghai latitude and is a
regional mean, not a measured individual roof height. All transferred heights
and floor-derived heights remain explicitly classified as estimates.

Where a parent building has parts, the exact parent footprint minus the union
of all its parts is retained as a separate residual volume when the source
processing configuration identifies meaningful remaining geometry. This keeps
podiums that a single taller tower part does not cover. A parent's height or
floor count can describe the tallest tower, so these attributes are retained
in raw source data but are never applied as the residual podium height. The
sampler estimates heights for the exact residual footprint; these counts and
areas are reported separately. Detailed-landmark exclusions take precedence.

Height counts are retained per output tile and district. The input lockfile
pins source datasets and sampler source code. Records contain the configuration
hash; reruns resume only matching input and configuration checkpoints.

## Files and completeness

`tiles/<id>.glb` and `ids/<id>.json` are published before the matching
`records/<id>.json` is atomically written. A record is the completed-file signal
for an uploader. IDs are separated into `building` and `building_part`; parent
IDs can occur in several sidecars when parts span owner cells, so a viewer must
reference-count IDs when suppressing streamed online duplicates.

The aggregate `manifest.json` includes per-district source and modeled counts,
height quality, bytes, triangles, and an explicit completeness flag. Completeness
requires every source cell to finish, zero export failures, and exact agreement
between modeled features plus the detailed-landmark replacements and the raw
renderable source counts plus restored residual parents. Parent volumes replaced by actual building parts and
underground records are reported separately. Detailed landmark replacements
use verified UUIDs, never a circular deletion radius. Geometry overrides can
preserve wings of a footprint when only part is modeled separately.

## Attribution and limitations

Derived building geometry: © Overture Maps Foundation and © OpenStreetMap
contributors, ODbL-1.0. Source East Asian building footprints: Qian Shi et al.,
CC BY 4.0, DOI `10.5281/zenodo.8174931`. CMAB predicted rooftops, CNBH 2020 height
estimates and European Commission JRC GHSL 2018 height data are CC BY 4.0; retain
their source provenance files and citations. These datasets have different
capture dates and incomplete source attribution, heights, and building coverage.
Model completeness means all available downloaded source geometry within the
documented display boundary, not a claim that every physical building in
Shanghai has been mapped or individually surveyed.
