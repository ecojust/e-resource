"""Conservative, reproducible transfer of openly licensed estimated heights.

Callers MUST preserve source height and num_floors * 3.2 before using this module.
This sampler adds estimates only: CMAB rooftop match > CNBH 10m > GHSL 2018.
No nearest-building height transfer or GCJ-02 conversion is performed.
"""
from pathlib import Path
from collections import OrderedDict
import math,json
import numpy as np
import pyarrow.parquet as pq
import shapely
from shapely.geometry import shape
from pyproj import Transformer

ROOT=Path(__file__).resolve().parent
SAMPLER_VERSION='2026-10-25-v1'

class CMABHeightMatcher:
    """Require IoU >= .60, both covered fractions >= .70; reject ambiguity.

    A second qualifying roof with IoU within .10 of the best and height differing
    by >10% makes the match ambiguous. The raster fallback is then used.
    Rooftop splits/merges and shifted high-rise roofs are deliberately rejected.
    """
    MIN_IOU=.60
    MIN_COVERAGE=.70
    def __init__(self,cmab_path,cache_tiles=24):
        self.path=Path(cmab_path);self.cache=OrderedDict();self.cache_tiles=cache_tiles
        self.manifest=json.loads((self.path/'manifest.json').read_text())
        self.available={s['file'][:-8] for s in self.manifest['shards']}
        self.project=Transformer.from_crs(4326,3857,always_xy=True)

    def _tile(self,key):
        if key not in self.available:return None
        if key in self.cache:
            self.cache.move_to_end(key);return self.cache[key]
        data=pq.read_table(self.path/(key+'.parquet'),columns=['geometry','height_m','source_id']).to_pydict()
        geoms=shapely.from_wkb(data['geometry'])
        invalid=~shapely.is_valid(geoms)
        if invalid.any():geoms[invalid]=shapely.make_valid(geoms[invalid])
        value=(geoms,shapely.STRtree(geoms),np.asarray(data['height_m']),data['source_id'])
        self.cache[key]=value
        if len(self.cache)>self.cache_tiles:self.cache.popitem(last=False)
        return value

    def sample_geometry(self,geometry):
        g=shape(geometry) if isinstance(geometry,dict) else geometry
        if g.is_empty:return None
        g=shapely.transform(g,self.project.transform,interleaved=False)
        if not g.is_valid:g=shapely.make_valid(g)
        area=g.area
        if area<=0:return None
        minx,miny,maxx,maxy=g.bounds
        # Adjacent shards cover source rooftops straddling a shard boundary.
        matches=[]
        for tx in range(math.floor(minx/5000)-1,math.floor(maxx/5000)+2):
            for ty in range(math.floor(miny/5000)-1,math.floor(maxy/5000)+2):
                tile=self._tile(f'{tx}_{ty}')
                if tile is None:continue
                geoms,tree,heights,ids=tile
                for index in tree.query(g):
                    roof=geoms[index];roof_area=roof.area
                    if roof_area<=0:continue
                    # Cheap area-ratio rejection before polygon intersection.
                    if min(area,roof_area)/max(area,roof_area)<self.MIN_COVERAGE:continue
                    overlap=g.intersection(roof).area
                    a=overlap/area;b=overlap/roof_area
                    if min(a,b)<self.MIN_COVERAGE:continue
                    iou=overlap/(area+roof_area-overlap)
                    if iou<self.MIN_IOU:continue
                    matches.append((iou,float(heights[index]),ids[index],a,b))
        if not matches:return None
        matches.sort(reverse=True);best=matches[0]
        if len(matches)>1:
            second=matches[1]
            if second[0]>=best[0]-.10 and abs(second[1]-best[1])/best[1]>.10:return None
        iou,height,source_id,a,b=best
        return {'height_m':round(height,3),'height_source':'cmab-v2-predicted-rooftop-height',
                'height_quality':'cmab_estimate_matched_rooftop','height_estimated':True,
                'height_epoch':'2020-2024 imagery; model uses 2023 training data',
                'height_method':'rooftop-overlap-iou>=0.60-both-coverage>=0.70',
                'height_license':'CC-BY-4.0','height_source_id':source_id,
                'height_match_iou':round(iou,4),'height_match_target_coverage':round(a,4),
                'height_match_rooftop_coverage':round(b,4),'height_sample_count':1}

class BuildingHeightSampler:
    def __init__(self,cnbh_path=None,ghsl_path=None,cmab_path=None):
        from raster_height_sampler import RasterHeightSampler
        self.raster=RasterHeightSampler(cnbh_path=cnbh_path,ghsl_path=ghsl_path)
        self.cmab=CMABHeightMatcher(cmab_path) if cmab_path else None
    def sample_geometry(self,geometry):
        result=self.cmab.sample_geometry(geometry) if self.cmab else None
        if result is None:result=self.raster.sample_geometry(geometry)
        if result is not None:
            result['height_sampler_version']=SAMPLER_VERSION
            # Uniform provenance keys, while preserving the raster helper's API.
            for key in ('estimated','license','method'):
                if key in result:result['height_'+key]=result[key]
            if 'count' in result:result['height_sample_count']=result['count']
            if 'resolution' in result:result['height_resolution_m']=result['resolution']
        return result
