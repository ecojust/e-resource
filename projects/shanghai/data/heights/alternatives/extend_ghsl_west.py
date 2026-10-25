"""Rebuild the full Shanghai GHSL height clip from eastern/western TIFF or ZIP.

No downloading occurs here. Obtain R6_C31 (east) and R6_C30 (west) explicitly
with the parent download_height_sources.py. Source data are CC-BY-4.0.
The output retains the eastern source grid and Float32 meter values. Optional
--previous checks every old clip pixel before the rebuilt file is published.
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
import math
from pathlib import Path
import shutil
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8*2**20), b''):
            digest.update(part)
    return digest.hexdigest()


def unpack_source(path, directory):
    if path.suffix.lower() != '.zip':
        return path
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(('.tif','.tiff'))]
        if len(members) != 1:
            raise ValueError(f'Expected one TIFF in {path.name}, found {len(members)}')
        # Copy the single member to a controlled basename, avoiding extraction
        # of unrelated archive paths. Reading the full member verifies its CRC.
        output = directory / Path(members[0]).name
        with archive.open(members[0]) as source, output.open('wb') as target:
            shutil.copyfileobj(source, target, 8*2**20)
        return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--east', type=Path, required=True, help='Eastern R6_C31 source TIFF or ZIP')
    parser.add_argument('--west', type=Path, required=True, help='Western R6_C30 source TIFF or ZIP')
    parser.add_argument('--boundaries', type=Path, default=HERE.parents[1]/'districts.geojson',
                        help='WGS84 GeoJSON; default: project data/districts.geojson')
    parser.add_argument('--output', type=Path, default=HERE.parent/'rebuilt'/'shanghai_ghsl_anbh_2018_3arcsec.tif',
                        help='Default: data/heights/rebuilt/shanghai_ghsl_anbh_2018_3arcsec.tif')
    parser.add_argument('--previous', type=Path, help='Optional old clip whose pixels must remain unchanged')
    parser.add_argument('--report', type=Path, help='Validation JSON; default: OUTPUT with .validation.json suffix')
    args = parser.parse_args(argv)
    import numpy as np
    import rasterio
    from rasterio.features import geometry_mask
    from rasterio.mask import mask
    from rasterio.windows import Window, bounds as window_bounds
    from rasterio.warp import reproject, Resampling
    from shapely.geometry import shape, mapping, box
    from shapely.ops import unary_union
    from shapely.prepared import prep
    for path in [args.east, args.west, args.boundaries] + ([args.previous] if args.previous else []):
        if not path.is_file():
            parser.error(f'Input not found: {path}')
    if args.output.resolve() in {args.east.resolve(), args.west.resolve()}:
        parser.error('--output must differ from source inputs')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name(args.output.name+'.tmp.tif')
    districts = json.loads(args.boundaries.read_text())['features']
    city = unary_union([shape(feature['geometry']) for feature in districts])
    prepared = prep(city)
    with tempfile.TemporaryDirectory(prefix='ghsl-sources-', dir=args.output.parent) as folder, ExitStack() as stack:
        directory = Path(folder)
        east_path = unpack_source(args.east, directory)
        west_path = unpack_source(args.west, directory)
        east = stack.enter_context(rasterio.open(east_path))
        west = stack.enter_context(rasterio.open(west_path))
        if east.crs != west.crs or east.crs != rasterio.crs.CRS.from_epsg(4326):
            raise ValueError('Both source rasters must use EPSG:4326')
        if east.dtypes != ('float32',) or west.dtypes != ('float32',):
            raise ValueError('Expected single-band Float32 sources')
        if east.transform.b or east.transform.d or east.transform.a <= 0 or east.transform.e >= 0:
            raise ValueError('Expected a north-up eastern source')
        # Preserve eastern origin and pixel values exactly. Western floats are
        # nearest-neighbor aligned only where the eastern tile is unavailable.
        minx, miny, maxx, maxy = city.bounds
        inverse = ~east.transform
        c0, r0 = inverse*(minx,maxy)
        c1, r1 = inverse*(maxx,miny)
        c0, r0, c1, r1 = math.floor(c0), math.floor(r0), math.ceil(c1), math.ceil(r1)
        crop = Window(c0,r0,c1-c0,r1-r0)
        transform = east.window_transform(crop)
        profile = east.profile.copy()
        profile.update(width=int(crop.width), height=int(crop.height), transform=transform,
                       compress='deflate', predictor=3, tiled=True, blockxsize=256,
                       blockysize=256, nodata=0)
        source_extent = box(*east.bounds).union(box(*west.bounds))
        if not source_extent.covers(city):
            raise ValueError('The two source tiles do not cover the complete district geometry')
        with rasterio.open(temporary,'w',**profile) as target:
            target.update_tags(source='European Commission JRC GHS-BUILT-H ANBH R2023A',
                               epoch='2018', license='CC-BY-4.0', unit='metres',
                               meaning='Average net building height per cell; not surveyed individual buildings',
                               source_url='https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php',
                               source_tiles='R6_C30,R6_C31',
                               preparation='Shanghai full 16-district administrative union; nearest-neighbor western alignment; eastern source grid preserved')
            for _, window in target.block_windows(1):
                tile = box(*window_bounds(window,transform))
                if not prepared.intersects(tile):
                    continue
                source_window = Window(c0+window.col_off,r0+window.row_off,window.width,window.height)
                values = east.read(1,window=source_window,boundless=True,fill_value=0)
                if tile.bounds[0] < east.bounds.left:
                    western = np.zeros(values.shape,dtype=np.float32)
                    reproject(rasterio.band(west,1),western,
                              src_transform=west.transform,src_crs=west.crs,
                              dst_transform=target.window_transform(window),dst_crs=target.crs,
                              src_nodata=0,dst_nodata=0,resampling=Resampling.nearest)
                    xs = transform.c+(np.arange(int(window.col_off),int(window.col_off+window.width))+.5)*transform.a
                    use_west = xs < east.bounds.left
                    values[:,use_west] = western[:,use_west]
                if not prepared.contains(tile):
                    inside = geometry_mask([mapping(city.intersection(tile))],out_shape=values.shape,
                                           transform=target.window_transform(window),invert=True,all_touched=True)
                    values[~inside] = 0
                target.write(values,1,window=window)
    base = 'https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss/V1-0/tiles/'
    stem = 'GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss_V1_0_R6_C'
    report = {'source':'GHS-BUILT-H ANBH E2018 R2023A','license':'CC-BY-4.0',
              'download_urls':[base+stem+suffix+'.zip' for suffix in ['30','31']],
              'source_inputs':[{'name':path.name,'bytes':path.stat().st_size,'sha256':sha256(path)}
                               for path in [args.west,args.east]],
              'raster':args.output.name,'raster_bytes':temporary.stat().st_size,
              'raster_sha256':sha256(temporary),'crs':'EPSG:4326','dtype':'float32',
              'resolution_degrees':[transform.a,-transform.e],
              'resolution_m_at_31N':[79.5,92.8],'nodata':0,
              'shape':[1,int(crop.height),int(crop.width)],
              'coverage':'Entire supplied district administrative union, including remote exclaves',
              'district_statistics':[]}
    with rasterio.open(temporary) as source:
        if args.previous:
            with rasterio.open(args.previous) as old:
                if old.crs != source.crs or not np.allclose(old.res,source.res,rtol=0,atol=1e-12):
                    raise ValueError('Previous raster has a different CRS or resolution')
                old_values = old.read(1)
                start_col,start_row = (~source.transform)*(old.bounds.left,old.bounds.top)
                if not np.allclose([start_col,start_row],np.round([start_col,start_row]),rtol=0,atol=1e-5):
                    raise ValueError('Previous clip is not aligned to the eastern grid')
                old_window = Window(round(start_col),round(start_row),old.width,old.height)
                new_values = source.read(1,window=old_window)
                if not np.array_equal(old_values,new_values):
                    raise ValueError('At least one previous clip pixel changed; output not replaced')
                report['unchanged_old_clip_pixels'] = int(old_values.size)
                report['unchanged_old_positive_cells'] = int(np.count_nonzero(old_values>0))
        full = source.read(1)
        valid = full[np.isfinite(full)&(full>0)]
        report['valid_height_cells'] = int(valid.size)
        if args.previous:
            report['added_positive_cells'] = int(valid.size-report['unchanged_old_positive_cells'])
        report['bounds'] = list(source.bounds)
        report['height_metres_quantiles'] = dict(zip(['min','p10','p50','p90','p99','max'],
                                                    map(float,np.quantile(valid,[0,.1,.5,.9,.99,1])))) if valid.size else {}
        for feature in districts:
            geometry = shape(feature['geometry'])
            part,_ = mask(source,[feature['geometry']],crop=True,all_touched=True,nodata=0)
            values = part[np.isfinite(part)&(part>0)]
            props = feature['properties']
            report['district_statistics'].append({
                'name':props.get('name'),'id':props.get('id',props.get('adcode')),
                'source_covers_full_geometry':source_extent.covers(geometry),
                'height_cells':int(values.size),'median_m':float(np.median(values)) if values.size else None,
                'p90_m':float(np.quantile(values,.9)) if values.size else None,
                'max_m':float(values.max()) if values.size else None})
    if temporary.stat().st_size >= 100_000_000:
        raise ValueError('Output exceeds the 100 MB repository file limit')
    temporary.replace(args.output)
    report_path = args.report or args.output.with_suffix('.validation.json')
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({'output':str(args.output),'report':str(report_path),
                      'bytes':report['raster_bytes'],'sha256':report['raster_sha256'],
                      'valid_height_cells':report['valid_height_cells'],
                      'unchanged_old_clip_pixels':report.get('unchanged_old_clip_pixels')},ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
