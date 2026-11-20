"""Check default overview approach against fixed nearby city source footprints and heights."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import LineString, Point, shape

AUDIT=Path(__file__).resolve().parent
SOURCE=AUDIT.parents[2]/'source/precise/huangpu-development-building/footprint-review.json'

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--feature-table',required=True,type=Path)
    cli.add_argument('--contract',type=Path,default=AUDIT/'final-placement-contract.json')
    cli.add_argument('--report',type=Path,default=AUDIT/'overview-sightlines.json')
    args=cli.parse_args()
    contract_path=args.contract
    c=json.loads(contract_path.read_bytes());src=json.loads(SOURCE.read_bytes())
    raw=args.feature_table.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==next(r['sha256']for r in src['frozen_bindings']if r['repository_path'].endswith('feature-table.json.gz'))
    rows=json.loads(gzip.decompress(raw))['features']
    lon,lat=c['lng'],c['lat'];center=np.array([lon,lat]);cos=math.cos(math.radians(lat))
    scale=np.array([111195*cos,111195]);theta=math.radians(c['heading'])
    axes=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    mask=shapely.transform(shape(c['replacement_geometry']),lambda xy:(xy-center)*scale)
    others=[]
    for r in rows:
        if shape(r['geometry']).distance(Point(lon,lat))>=.0016:
            continue
        poly=shapely.transform(shape(r['geometry']),lambda xy:(xy-center)*scale)
        if r['localId']==c['owner']['feature_local_id']:
            poly=poly.difference(mask)
        others.append((r,poly))
    targets=[('black portal',-.70,-.44,2.40),('central three bays',-.70,-.25,32.0),('six crest ribs',-.70,-.15,67.0),('left single tower',-4.45,-.66,45.2),('right single tower',2.80,-.93,45.2),('left shoulder',-9.85,-4.24,18.0),('right shoulder',8.58,-4.89,18.0),('left street return',-14.36,-3.6,12.0),('right street return',12.80,-2.67,12.0)]
    views=[('street-aligned secondary approach',170,42,c['overviewZoom'],0,0,0),
           ('selected default',c['overviewBearing'],c['overviewPitch'],c['overviewZoom'],0,0,0)]
    result=[]
    for name,bearing,pitch,zoom,cx,cy,elevation in views:
        a=math.radians(bearing);pitch_r=math.radians(pitch)
        out=np.array([-math.sin(a),-math.cos(a)])
        for viewport in (650,844):
            distance=viewport*1.5*(2*math.pi*6371008.8*cos)/(512*2**zoom)
            eye=out*distance*math.sin(pitch_r)+np.array([cx,cy])@axes
            high=elevation+distance*math.cos(pitch_r)
            probes=[]
            for feature,x,y,z in targets:
                p=np.array([x,y])@axes;ray=LineString([p,eye])
                blocked=[]
                for r,g in others:
                    segment=ray.intersection(g)
                    if segment.is_empty:continue
                    h=z+(high-z)*segment.distance(Point(p))/ray.length
                    if h<r['height']:blocked.append({'owner':r['localId'],'above_ray_m':round(r['height']-h,3)})
                probes.append({'feature':feature,'intervening_owners':blocked})
                if name=='selected default':assert not blocked,(name,viewport,feature,blocked)
            result.append({'view':name,'bearing':bearing,'pitch':pitch,'zoom':zoom,'viewport_height':viewport,'rays':probes})
    args.report.write_text(json.dumps({'id':c['id'],'feature_table_sha256':digest,'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Approximate fixed-FOV projection against the retained offices and the three opposite corner lots with their nominal city heights. The plaza corner, both street returns, and all three tower tiers are checked on two viewport heights.','views':result},ensure_ascii=False,indent=2)+'\n')
    print('Checked nine sightlines at two camera approaches and two viewport heights.')

if __name__=='__main__':
    main()
