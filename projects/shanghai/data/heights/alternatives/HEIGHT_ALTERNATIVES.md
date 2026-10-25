# Shanghai building-height rasters: downloaded and verified alternatives

Validation date: 2026-10-25. All files below were actually downloaded, opened
with Rasterio, spatially clipped, and inspected. No result should be described
as a surveyed individual building height. The rasters included in this release
are the [CNBH clip](cnbh_2020_shanghai_core_dm.tif), the
[Microsoft height-only comparison](microsoft_2023q4_shanghai_height_m.tif), and
the parent directory's [GHSL clip](../shanghai_ghsl_anbh_2018_3arcsec.tif).
Raw source tiles, the Microsoft global index/cache, and its two-band research
intermediate are not included. Every included file is below 100 MB.

Portable rebuild evidence is in [portability_validation.json](portability_validation.json).
Four script entry points support `--help`; importing them or requesting help
performs no download or reconstruction. Actual CNBH/GHSL rebuilds using existing
source TIFFs, from a different working directory, produced byte-identical
SHA-256 hashes to the released rasters. No source files were redownloaded.

## Selected fine-resolution fallback: CNBH-10m, 2020

**License: Creative Commons Attribution 4.0 International (CC-BY-4.0).**
The license is stated in the dataset's registered DataCite metadata, saved in
[`datacite-7827315.json`](datacite-7827315.json), and in the Zenodo record. Attribution must accompany
redistributed data and derived results; identify the clipping and quantization.

- Dataset: Wu, Wanben (2023), *CNBH-10 m: A first Chinese building height at
  10 m resolution*, Zenodo, https://doi.org/10.5281/zenodo.7827315.
- Paper: Wu, W.; Ma, J.; Banzhaf, E.; et al. (2023), *A first Chinese building
  height estimate at 10 m resolution (CNBH-10 m) using multi-source earth
  observations and machine learning*, Remote Sensing of Environment 291,
  113578. https://doi.org/10.1016/j.rse.2023.113578.
- License: https://creativecommons.org/licenses/by/4.0/;
  [included license text](LICENSE-CC-BY-4.0.txt).
- Metadata verification: https://api.datacite.org/dois/10.5281/zenodo.7827315.
- Original public file:
  https://zenodo.org/api/records/7827315/files/CNBH10m_X121Y31.tif/content.
- Original checksum, verified after download:
  MD5 `72fccc03160010daeb697220e2c0db1b`.
- Original size: 335,234,763 bytes. **Do not put this upstream source file in
  the Git repository; it exceeds the user's 100 MB per-file limit.**

The actual original GeoTIFF is **Float32 in meters**, EPSG:32651 (UTM zone 51N),
10 × 10 m resolution, 22,517 rows × 19,496 columns. Scale is 1.0; zero means
background/no building estimate. A third-party Xi'an example distributed
processed UInt16 decimeters; its encoding does not describe this original.

The release-ready Shanghai clip is `cnbh_2020_shanghai_core_dm.tif`:

- 24,314,417 bytes, 13,341 rows × 11,051 columns; each file is below 100 MB.
- UInt16 decimeters, band scale **0.1**, offset 0, nodata 0. Multiply read
  values by the dataset scale to obtain meters; Rasterio's `read()` and
  `sample()` do not automatically apply that scale.
- Changes from source: mask to the Shanghai district union intersecting the
  source tile, quantize to 0.1 m, lossless DEFLATE compression. Maximum rounding
  error is 0.05 m. Zero also represents cells masked outside Shanghai.
- SHA-256:
  `6bdaefd92ce796c87c4ee0f25150cdafef6d22fdabd2cf2ad41741fd8ec52777`.
- 16,602,562 positive building pixels; observed min 8.5 m, median 16.7 m,
  90th percentile 25.4 m, maximum 41.7 m.

**Coverage and accuracy:** The source tile covers all 16 district centers and
the main Shanghai land area. OSM administrative boundaries include distant
exclaves and eastern maritime territory outside this tile. These portions
are not silently assigned CNBH values; use the independently prepared GHSL
fallback or a separately sourced neighboring tile. The dataset's national
validation reports RMSE 6.1 m and MAE 5.2 m, not Shanghai-specific accuracy.
The local 41.7 m maximum demonstrates strong smoothing of tall buildings.
Documented source heights, floor counts, and verified building-level data
must have priority over CNBH. This raster cannot reproduce the skyline alone.

### Reproduction and use

Dependencies: `numpy`, `rasterio`, `pyproj`, `shapely>=2.0`. Run these commands
from the project root; script defaults also work from other current directories
because they are resolved relative to `__file__`:

```bash
python data/heights/alternatives/download_cnbh_ranges.py --help
python data/heights/alternatives/download_cnbh_ranges.py
python data/heights/alternatives/clip_cnbh_shanghai.py
python data/heights/alternatives/validate_sampler.py
```

The [downloader](download_cnbh_ranges.py) explicitly downloads the original to
`data/heights/.cache/height-sources/CNBH10m_X121Y31.tif`, an ignored cache, and
supports `--output`, `--workers`, and `--chunk-mib`. It uses ordinary public
HTTP byte ranges and verifies the official MD5. Plain full-file requests were
intermittently blocked by the host; public API byte-range requests succeeded.

The [clipper](clip_cnbh_shanghai.py) accepts `--raw`, `--boundaries`, `--output`,
and `--report`. Defaults read that same cached source and the project's
`data/districts.geojson`, and write to `data/heights/rebuilt/`, preserving the
shipped locked raster. It rejects an incorrect source MD5, CRS, resolution,
or encoding. For an explicit source location:

```bash
python data/heights/alternatives/clip_cnbh_shanghai.py \
  --raw /path/to/CNBH10m_X121Y31.tif \
  --boundaries data/districts.geojson \
  --output data/heights/rebuilt/cnbh_2020_shanghai_core_dm.tif
```

Raw chunks and the original file are preparation assets, not release assets.
The included [CNBH manifest](cnbh_shanghai_manifest.json) records the released
file's provenance, encoding, checksum and coverage.

Use `../raster_height_sampler.py`:

```python
from raster_height_sampler import RasterHeightSampler
sampler = RasterHeightSampler()  # Construct once per worker.
estimate = sampler.sample_geometry(feature['geometry'])  # WGS84 GeoJSON.
if estimate:
    height_m = estimate['height_m']
    quality = estimate['height_quality']
```

CNBH sampling uses the median of positive pixels whose centers lie inside
the building footprint, excluding holes. If a narrow footprint encloses no
pixel centers, it samples the footprint's representative point. If its CNBH
pixels contain no estimate, GHSL at the representative point is used.
No neighboring building cells are substituted. Returned fields include
height, source, quality, epoch, resolution, estimated flag, license, method,
and positive contributing pixel count.

Cached CNBH occupies approximately 295 MB per worker. In this environment,
loading both rasters took 2.86 s, and 680 real Huangpu footprints took 0.344 s
(about 1,974 footprints/s). Of those, 653 used CNBH and 27 used GHSL.
Six independent semantic fixtures passed, covering metadata scale, positive
median, polygon holes, narrow footprints, fallback without neighbor fill,
and unavailable coordinates. Five hundred random positive source/clip
samples agreed within 0.04996 m. Evidence is saved in
[`raster_sampler_validation.json`](raster_sampler_validation.json); fixtures
are in [validate_sampler.py](validate_sampler.py). The fixture checker supports
`--help` and an optional `--report` JSON output; it performs no network access.

## Downloaded comparison alternative: Microsoft, 2023 Q4

**License: CDLA-Permissive-2.0**, not Creative Commons.
Repository and data documentation: https://github.com/microsoft/buildings.
License: https://cdla.dev/permissive-2-0/;
[included license agreement](LICENSE-CDLA-Permissive-2.0.txt).
Source documentation is saved as [microsoft_buildings.md](microsoft_buildings.md);
its relative documentation/image links were converted to upstream absolute URLs.
The code's MIT license is separate from the data's CDLA license.

- Public spatial index:
  https://opendata.aiforgood.ai/building-density/tile_index.gpkg.
- Example verified source COG:
  https://opendata.aiforgood.ai/building-density/v1/2023q4/12-39-p3_ensemble_downsampled/L15-1715E-1211N.tif.
- Original CRS EPSG:3857. Observed projected pixel resolution is
  76.437028285 m, about 65 m on the ground at Shanghai's latitude; the source
  product is described as nominal 100 m.
- Original band 1 is building density (0–1); original band 2 is normalized
  estimated height (0–1). The prepared output multiplies band 2 by 100 to
  obtain meters. Nodata is -1 and remains -1.
- The original research intermediate, named
  `microsoft_2023q4_shanghai_density_height_m.tif`, was 8,187,862 bytes, 2 bands,
  4,767 rows × 6,736 columns, Float32, Shanghai administrative union mask.
  **This two-band intermediate is not included in the release.**
- The included [height-only clip](microsoft_2023q4_shanghai_height_m.tif) is
  2,609,062 bytes, 1 height band in meters, with the same CRS/grid and nodata.
  Its own [release manifest](microsoft_height_only_manifest.json) records
  the shipped checksum, units, conversion and license.
- Per-district positive building-cell statistics for all 16 districts are
  in [microsoft_district_stats.json](microsoft_district_stats.json); full source
  URLs and the historical two-band intermediate's checksum are in
  [microsoft_shanghai_manifest.json](microsoft_shanghai_manifest.json).

This is a coarse cell estimate. Its Shanghai maximum is about 42.3 m and
typical values are much lower, so it is retained as an independently
downloaded comparison, not the preferred street-level height source.
The 383,967,232-byte national tile index and raw COG cache are local
preparation assets and should not be added to the Git repository.

## Candidates excluded from release

- `lauraset/BuildingHeightModel`: its 42-city Amap-derived reference dataset
  explicitly cannot be fully published because of copyright; research
  access links do not establish redistribution permission.
- `lauraset/Super-resolution-building-height-estimation`: a promising 2.5 m
  city product, but a clearly applicable redistribution license was not
  verified during this investigation.
- TUM GlobalBuildingAtlas: the parent investigation rejected its
  noncommercial/reuse terms for the combined released data. No GBA heights
  were merged into these output rasters.

## GHSL fallback extension covering remote administrative exclaves

The western public source archive `R6_C30.zip` was subsequently downloaded
(149,402,092 bytes), verified with the ZIP member CRCs, and combined with the
existing eastern `R6_C31` tile. Reproduce with
[extend_ghsl_west.py](extend_ghsl_west.py).
Both sources are GHS-BUILT-H ANBH E2018 R2023A, licensed CC-BY-4.0.

The replacement `../shanghai_ghsl_anbh_2018_3arcsec.tif` is 2,685,448 bytes,
Float32 meters, EPSG:4326, approximately 3 arcseconds, zero nodata,
3,330 rows × 5,552 columns. SHA-256:
`3d4fe310d0c159e19ac847fe51bc7e14316877b8662ea0bc7cc2d75db9c73535`.

All 16 districts' complete administrative geometries are within the combined
source extent. The original eastern clip's **12,923,730 pixels are bitwise
unchanged**, including its 796,956 positive height cells. The western extension
adds 1,927 positive cells in Baoshan's remote administrative exclaves, for
798,883 total. The eastern source grid is retained; western values use nearest
neighbor alignment, without height interpolation. Full evidence and both
archive SHA-256 hashes are saved in
[ghsl_full_extent_validation.json](../ghsl_full_extent_validation.json) and
[ghsl_validation.json](../ghsl_validation.json). The large western source
archive stays in the ignored raw cache, outside Git. The original
[JRC copyright notice](../ghsl-copyright.txt) is also included.

The portable rebuild entry performs no download and accepts TIFF or ZIP sources:

```bash
python data/heights/alternatives/extend_ghsl_west.py \
  --east /path/to/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss_V1_0_R6_C31.zip \
  --west /path/to/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss_V1_0_R6_C30.zip \
  --boundaries data/districts.geojson \
  --output data/heights/rebuilt/shanghai_ghsl_anbh_2018_3arcsec.tif \
  --previous data/heights/shanghai_ghsl_anbh_2018_3arcsec.tif
```

`--previous` is optional: rebuilding does not require an existing old clip.
When supplied, every previous pixel must remain unchanged before output is
published. Default boundaries are located relative to the script; default
output is in `data/heights/rebuilt/`, preserving the locked release. ZIP inputs
are extracted to a temporary directory; source file CRCs and SHA-256 values
are recorded/validated. `--report` selects a validation JSON destination.

GHSL interpretation and the separate CMAB building-level investigation are
documented further by the parent height-data task. A finer nominal raster
resolution does not establish a more accurate height for a specific building.
