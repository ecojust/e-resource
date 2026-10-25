"""Check the shipped raster sampler with independent synthetic fixtures.

No network access or source downloads. Fixtures verify raster scale, median,
holes, narrow footprints, missing-cell fallback and unavailable coordinates.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,help='Optional JSON result destination')
    args = parser.parse_args(argv)
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin
    from shapely.geometry import Polygon,box,mapping
    sys.path.insert(0,str(HERE.parent))
    from raster_height_sampler import RasterHeightSampler

    def write_raster(path,data,scale):
        with rasterio.open(path,'w',driver='GTiff',height=3,width=3,count=1,
                           dtype='uint16',crs='EPSG:4326',nodata=0,
                           transform=from_origin(0,3,1,1)) as dataset:
            dataset.write(np.array(data,dtype=np.uint16),1)
            dataset.scales = (scale,)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        write_raster(root/'cnbh.tif',[[100,200,0],[300,900,0],[0,0,0]],.2)
        write_raster(root/'ghsl.tif',[[70]*3]*3,.5)
        sampler = RasterHeightSampler(root/'cnbh.tif',root/'ghsl.tif')
        result = sampler.sample_geometry(mapping(box(0,1,2,3)))
        assert result['height_m']==50 and result['count']==4,result
        assert result['method']=='footprint-pixel-center-positive-median',result
        geom = Polygon([(0,1),(2,1),(2,3),(0,3)],holes=[[(1.1,1.1),(1.9,1.1),(1.9,1.9),(1.1,1.9)]])
        result = sampler.sample_geometry(mapping(geom))
        assert result['height_m']==40 and result['count']==3,result
        result = sampler.sample_geometry(mapping(box(.01,2.01,.02,2.02)))
        assert result['height_m']==20 and result['method']=='representative-point-cell',result
        result = sampler.sample_geometry(mapping(box(2,2,3,3)))
        assert result['height_m']==35 and result['height_quality']=='raster_estimate_2018',result
        assert sampler.sample_point(-1,10) is None
        assert sampler.sample_geometry({'type':'Polygon','coordinates':[]}) is None
    report = {'passed':True,'fixtures':['metadata-scale','positive-median','hole-exclusion',
                                      'narrow-footprint-point','no-neighbor-fallback','unavailable']}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
