"""Check published estate markers and roof-scale observations without source imagery."""
import argparse
from pathlib import Path
import hashlib
import json
import math

from shapely.geometry import Point, shape
from shapely.ops import transform

HERE=Path(__file__).resolve().parent


def check(source, observations):
    parcel=source['ordinary_city']
    centre=source['location']['local_reference_wgs84']
    mx=111320*math.cos(math.radians(centre[1]));my=110860
    def project(lon,lat,z=None):
        from numpy import asarray
        return (asarray(lon)-centre[0])*mx,(asarray(lat)-centre[1])*my
    house=transform(project,shape(parcel['geometry_wgs84']))
    distances={}
    for key,meta in source['location']['points'].items():
        xy=project(*meta['point_wgs84'])
        distances[key]={'covered':house.covers(Point(xy)),'distance_to_parcel_m':house.distance(Point(xy))}
    if not distances['published historical-house coordinates']['covered'] or distances['沙逊别墅']['covered']:
        raise ValueError('Unexpected coordinate/POI distinction at the garden.')
    spread={}
    for name,grp in observations['candidates'].items():
        for label,item in grp.items():
            if not isinstance(item,dict):continue
            a,b=[project(*wgs)for wgs in item['wgs84']]
            length=math.dist(a,b);angle=math.degrees(math.atan2(b[0]-a[0],b[1]-a[1]))%360
            if abs(length-item['length_m'])>.07:
                raise ValueError(f'Inconsistent map/ground segment length for {label}.')
            spread[label]={'length_m':length,'geographic_bearing_deg':angle}
    return {'macro':parcel['macro'],'optional_ordinary_host':parcel['id'],'plan_m2':house.area,
            'distances':distances,'lines':spread,
            'scope':'The spatial check supports an estate marker and dimensional hypothesis; no exact 1937 facade position is imposed on the full coarse map feature.'}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('output',type=Path);args=cli.parse_args()
    p=HERE/'estate-location-evidence.json';o=HERE/'service-wing-plan-tests.json'
    result=check(json.loads(p.read_bytes()),json.loads(o.read_bytes()))
    result['input_sha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in (p,o)}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
