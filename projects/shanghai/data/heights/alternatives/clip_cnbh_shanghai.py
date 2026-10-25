"""Clip the public CNBH Float32-meter source to the Shanghai district union.

Output is UInt16 decimeters with band scale 0.1, zero nodata, and at most
0.05 m quantization error. Default output is a separate rebuilt directory;
the shipped locked raster is never overwritten unless explicitly selected.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', type=Path, default=HERE.parent/'.cache'/'height-sources'/'CNBH10m_X121Y31.tif',
                        help='Original Float32-meter source; default: data/heights/.cache/height-sources/CNBH10m_X121Y31.tif')
    parser.add_argument('--boundaries', type=Path, default=HERE.parents[1]/'districts.geojson',
                        help='WGS84 district GeoJSON; default: project data/districts.geojson')
    parser.add_argument('--output', type=Path, default=HERE.parent/'rebuilt'/'cnbh_2020_shanghai_core_dm.tif',
                        help='Output GeoTIFF; default: data/heights/rebuilt/cnbh_2020_shanghai_core_dm.tif')
    parser.add_argument('--report', type=Path, help='Manifest JSON; default: OUTPUT with .manifest.json suffix')
    args = parser.parse_args(argv)
    # Keep --help and imports independent of optional geospatial libraries.
    import numpy as np
    import rasterio
    from rasterio.windows import Window, bounds as window_bounds
    from rasterio.features import geometry_window, geometry_mask
    from shapely.geometry import shape, mapping, box, Point
    from shapely.ops import transform, unary_union
    from shapely.prepared import prep
    from pyproj import Transformer
    if not args.raw.is_file():
        parser.error(f'Raw source not found: {args.raw}; run download_cnbh_ranges.py explicitly first')
    if not args.boundaries.is_file():
        parser.error(f'Boundary file not found: {args.boundaries}')
    if args.output.resolve() == args.raw.resolve():
        parser.error('--output must differ from --raw')
    with args.raw.open('rb') as stream:
        digest = hashlib.md5()
        for chunk in iter(lambda: stream.read(8*2**20), b''):
            digest.update(chunk)
        source_md5 = digest.hexdigest()
    if source_md5 != '72fccc03160010daeb697220e2c0db1b':
        raise ValueError('Raw file does not match the official CNBH10m_X121Y31.tif MD5; refusing misattribution')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name+'.tmp.tif')
    geo = json.loads(args.boundaries.read_text())
    histogram = np.zeros(65536, dtype=np.int64)
    with rasterio.open(args.raw) as source:
        if source.dtypes != ('float32',) or source.scales[0] != 1.0:
            raise ValueError('Expected the original single-band Float32 CNBH meter source with scale 1')
        if source.crs != rasterio.crs.CRS.from_epsg(32651) or not np.allclose(source.res, [10,10], rtol=0, atol=1e-8):
            raise ValueError('Expected CNBH EPSG:32651 and 10 x 10 meter resolution')
        project = Transformer.from_crs(4326, source.crs, always_xy=True)
        districts = [(f['properties'], transform(project.transform, shape(f['geometry']))) for f in geo['features']]
        city = unary_union([g for _, g in districts])
        extent = box(*source.bounds)
        coverage = city.intersection(extent)
        if coverage.is_empty:
            raise ValueError('Districts and source raster do not overlap')
        prepared = prep(coverage)
        crop = geometry_window(source, [mapping(coverage)]).round_offsets().round_lengths()
        affine = source.window_transform(crop)
        profile = source.profile.copy()
        profile.update(width=int(crop.width), height=int(crop.height), transform=affine,
                       dtype='uint16', nodata=0, compress='deflate', predictor=2,
                       tiled=True, blockxsize=256, blockysize=256)
        with rasterio.open(temporary, 'w', **profile) as target:
            target.scales = (.1,)
            target.offsets = (0,)
            target.set_band_description(1, 'CNBH2020 estimatedbuildingheight decimeters')
            target.update_tags(source='CNBH-10m2020, Wu etal.2023, April2023version',
                               source_doi='10.5281/zenodo.7827315', license='CC-BY-4.0',
                               units='decimeters', height_multiply='0.1',
                               nodata_interpretation='0 means source no-building or outside Shanghai clip; not measured zeroheight',
                               source_dtype='float32 meters', quantization_error_max_m='0.05')
            for _, window in target.block_windows(1):
                tile = box(*window_bounds(window, affine))
                if not prepared.intersects(tile):
                    continue
                source_window = Window(crop.col_off+window.col_off, crop.row_off+window.row_off,
                                       window.width, window.height)
                values = source.read(1, window=source_window)
                if not prepared.contains(tile):
                    inside = geometry_mask([mapping(coverage.intersection(tile))], out_shape=values.shape,
                                           transform=target.window_transform(window), invert=True)
                    values = np.where(inside, values, 0)
                values = np.nan_to_num(values, nan=0, posinf=0, neginf=0)
                quantized = np.clip(np.rint(values*10), 0, 65535).astype('uint16')
                target.write(quantized, 1, window=window)
                histogram += np.bincount(quantized.ravel(), minlength=65536)
        source_bounds = list(source.bounds)
        source_crs = str(source.crs)
        source_resolution = list(source.res)
    total = int(histogram[1:].sum())
    cumulative = np.cumsum(histogram[1:])
    percentiles = {str(p): float((np.searchsorted(cumulative, total*p/100)+1)/10)
                   for p in [10,25,50,75,90,95,99,100]} if total else {}
    if total:
        percentiles['0'] = float(np.flatnonzero(histogram[1:])[0]+1)/10
    report = {'title': 'CNBH-10m 2020 Shanghai core clip',
              'source_url': 'https://zenodo.org/records/7827315',
              'file_url': 'https://zenodo.org/api/records/7827315/files/CNBH10m_X121Y31.tif/content',
              'license': 'CC-BY-4.0', 'year': 2020,
              'attribution': 'Wu, Wanben (2023). CNBH-10 m: A first Chinese building height at 10 m resolution. Zenodo. DOI:10.5281/zenodo.7827315. See HEIGHT_ALTERNATIVES.md for paper citation.',
              'crs': source_crs, 'resolution_m': source_resolution,
              'source_dtype': 'float32', 'source_units': 'meters',
              'output_dtype': 'uint16', 'output_scale_to_meters': .1, 'output_nodata': 0,
              'quantization_max_error_m': .05, 'path': args.output.name,
              'bytes': temporary.stat().st_size, 'shape': [int(crop.height), int(crop.width)],
              'transform': list(affine)[:6], 'source_bounds': source_bounds,
              'valid_building_cells': total, 'height_percentiles_m': percentiles,
              'district_coverage': [],
              'coverage_note': 'Main-city source tile; remote administrative exclaves and far-eastern maritime territory outside the tile need the full-extent GHSL fallback.'}
    for props, geometry in districts:
        entry = {'id': props.get('id', props.get('adcode')), 'name': props.get('name'),
                 'district_geometry_fraction_inside_source_tile': round(float(geometry.intersection(extent).area/geometry.area), 6)}
        if props.get('center'):
            entry['source_tile_covers_district_center'] = extent.covers(transform(project.transform, Point(props['center'])))
        report['district_coverage'].append(entry)
    report['source_md5'] = source_md5
    report['sha256'] = hashlib.sha256(temporary.read_bytes()).hexdigest()
    if temporary.stat().st_size >= 100_000_000:
        raise ValueError('Rebuilt clip exceeds the 100 MB repository file limit')
    temporary.replace(args.output)
    report_path = args.report or args.output.with_suffix('.manifest.json')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps({'output': str(args.output), 'report': str(report_path), 'bytes': report['bytes'],
                      'sha256': report['sha256'], 'valid_building_cells': total}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
