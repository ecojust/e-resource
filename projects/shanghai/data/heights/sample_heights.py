"""Sample the Shanghai GHSL average-net-building-height fallback.

This is an estimated cell average (~80x93m), NOT an individual measured roof.
Explicit building heights or documented floor counts must take precedence.

Example:
  python sample_heights.py --input buildings.geojson --output annotated.geojson

Requires numpy, rasterio, shapely. Does not modify any project source files.
"""
from pathlib import Path
import argparse
import json
import math
import numpy as np
import rasterio
from shapely.geometry import shape

DEFAULT_RASTER=Path(__file__).with_name('shanghai_ghsl_anbh_2018_3arcsec.tif')

class GHSLHeightSampler:
    source='ghsl-anbh-2018-cell-mean'
    def __init__(self,raster=DEFAULT_RASTER):
        with rasterio.open(raster) as ds:
            self.data=ds.read(1)
            self.transform=ds.transform
            self.inverse=~self.transform
            self.bounds=ds.bounds
            self.crs=str(ds.crs)
        if self.crs!='EPSG:4326':raise ValueError('This sampler expects the supplied WGS84 clip')
    def sample_point(self,longitude,latitude):
        col,row=self.inverse*(longitude,latitude)
        col,row=int(math.floor(col)),int(math.floor(row))
        if not (0<=row<self.data.shape[0] and 0<=col<self.data.shape[1]):return None
        value=float(self.data[row,col])
        if not math.isfinite(value) or value<=0:return None
        return {'height_m':round(value,3),'height_source':self.source,'height_estimated':True,
                'height_epoch':2018,'height_method':'raster-cell-average','height_resolution_arcsec':3,
                'height_license':'CC-BY-4.0'}
    def height_at(self,longitude,latitude):
        item=self.sample_point(longitude,latitude)
        return item['height_m'] if item else None
    def sample_geometry(self,geometry):
        # A representative point stays inside concave footprints. No neighboring
        # pixels are silently substituted if the cell has no building estimate.
        point=shape(geometry).representative_point()
        return self.sample_point(point.x,point.y)
    def sample_many(self,coordinates):
        pts=np.asarray(coordinates,dtype=float)
        cols=np.floor((pts[:,0]-self.transform.c)/self.transform.a).astype(np.int64)
        rows=np.floor((pts[:,1]-self.transform.f)/self.transform.e).astype(np.int64)
        inside=(rows>=0)&(rows<self.data.shape[0])&(cols>=0)&(cols<self.data.shape[1])
        output=np.full(len(pts),np.nan,dtype=np.float32)
        output[inside]=self.data[rows[inside],cols[inside]]
        output[(output<=0)|(~np.isfinite(output))]=np.nan
        return output

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--raster',default=DEFAULT_RASTER,type=Path)
    args=parser.parse_args();geo=json.loads(args.input.read_text());sampler=GHSLHeightSampler(args.raster)
    existing=sampled=missing=0
    for feature in geo['features']:
        props=feature.setdefault('properties',{})
        # Preserve positive numeric input heights; leave source metadata intact.
        candidate=props.get('height_m',props.get('height'))
        try:usable=float(candidate)>0
        except (TypeError,ValueError):usable=False
        if usable:existing+=1;continue
        item=sampler.sample_geometry(feature['geometry'])
        if item:props.update(item);sampled+=1
        else:missing+=1;props['height_source']='unavailable';props['height_estimated']=True
    geo['height_provenance']={'source':sampler.source,'license':'CC-BY-4.0','url':'https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php','note':'Cell average, not surveyed per-building height; zero/noData remain unavailable.'}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(geo,ensure_ascii=False,separators=(',',':')))
    print(json.dumps({'existing_heights_preserved':existing,'raster_estimates':sampled,'unavailable':missing},ensure_ascii=False))
if __name__=='__main__':main()
