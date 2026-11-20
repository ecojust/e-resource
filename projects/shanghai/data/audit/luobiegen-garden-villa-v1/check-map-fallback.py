"""Compare the frozen OpenFreeMap aggregate with the registered villa cut and retained connector."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.request import urlopen

import mapbox_vector_tile
import numpy as np
import shapely as geo
from shapely.geometry import mapping,shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
TILE='https://tiles.openfreemap.org/planet/20261115_080022_pt/14/13715/6696.pbf'
TILE_SHA='976cc80332d0c734d3209f6facad278b0187682c42f8ad2ca5390b4a24d604d4'
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tile',type=Path)
    parser.add_argument('--geojson',type=Path,help='Export the two original WGS84 features for the production JavaScript check')
    parser.add_argument('--out',type=Path,default=AUDIT/'fallback-vector.json')
    args=parser.parse_args()
    raw=args.tile.read_bytes() if args.tile else urlopen(TILE,timeout=40).read();assert sha(raw)==TILE_SHA
    layer=mapbox_vector_tile.decode(raw,default_options={'y_coord_down':True})['building']
    cf=AUDIT/'final-placement-contract.json';sf=PROJECT/'source/precise/changning-luobiegen-garden-villa/footprint-review.json'
    contract=json.loads(cf.read_bytes());review=json.loads(sf.read_bytes());lo,la=contract['lng'],contract['lat']
    k=6371008.8*math.cos(math.radians(la));phi=np.arcsinh(np.tan(np.radians(la)))
    def metres(p):return np.column_stack((np.radians(p[:,0]-lo)*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))
    def decode(p):
        lng=(p[:,0]/layer['extent']+13715)/16384*360-180
        loglat=np.pi*(1-2*(p[:,1]/layer['extent']+6696)/16384)
        return np.column_stack((np.radians(lng-lo)*k,(loglat-phi)*k))
    native=geo.transform(shape(review['owners'][0]['geometry_wgs84']),metres)
    cut=geo.transform(shape(contract['replacement_geometry']),metres);kept=native.difference(cut)
    reports=[]
    for f in layer['features']:
        original=geo.transform(shape(f['geometry']),decode)
        clearance=original.distance(cut)
        if clearance>0:
            # A remote overlap between components in this height aggregate lies
            # outside the cut. Avoid changing any of its original components.
            after=original;before_strip=after_strip=0.
            assert original.distance(kept)>0
        else:
            assert original.is_valid
            after=original.difference(cut)
            before_strip=original.intersection(kept).area;after_strip=after.intersection(kept).area
        assert abs(after_strip-before_strip)<1e-7
        reports.append({'source_id':f['id'],'properties':f['properties'],'minimum_clearance_m':clearance,'geometry_valid':original.is_valid,'input_m2':original.area,'residual_m2':after.area,'removed_m2':original.area-after.area,
            'western_strip_m2_before':before_strip,'western_strip_m2_after':after_strip})
    touched=[r for r in reports if r['removed_m2']>1e-6]
    assert len(touched)==1 and touched[0]['source_id']==13160566110 and 335<touched[0]['removed_m2']<336
    assert 38.8<touched[0]['western_strip_m2_after']<39.1
    if args.geojson:
        def to_wgs(p):
            lng=(p[:,0]/layer['extent']+13715)/16384*360-180
            lat=np.degrees(np.arctan(np.sinh(np.pi*(1-2*(p[:,1]/layer['extent']+6696)/16384))))
            return np.column_stack((lng,lat))
        features=[{**f,'geometry':mapping(geo.transform(shape(f['geometry']),to_wgs))} for f in layer['features']]
        args.geojson.write_text(json.dumps({'type':'FeatureCollection','tile_sha256':TILE_SHA,'features':features},separators=(',',':'))+'\n')
    args.out.write_text(json.dumps({'id':contract['id'],'frozen_tile':TILE,'tile_sha256':TILE_SHA,'tile_bytes':len(raw),'contract_sha256':sha(cf.read_bytes()),
        'source_sha256':sha(sf.read_bytes()),'script_sha256':sha(Path(__file__).read_bytes()),'all_features':reports},ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
