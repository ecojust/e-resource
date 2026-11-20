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
SOURCE=AUDIT.parents[2]/'source/precise/changning-zhou-gucheng-courtyard/footprint-review.json'

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--feature-table',required=True,type=Path)
    cli.add_argument('--report',type=Path,default=AUDIT/'overview-sightlines.json')
    args=cli.parse_args()
    contract_path=AUDIT/'final-placement-contract.json'
    c=json.loads(contract_path.read_bytes());src=json.loads(SOURCE.read_bytes())
    raw=args.feature_table.read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    assert digest==src['frozen_bindings']['feature-table.json.gz']['sha256']
    rows=json.loads(gzip.decompress(raw))['features']
    lon,lat=c['lng'],c['lat'];center=np.array([lon,lat]);cos=math.cos(math.radians(lat))
    scale=np.array([111195*cos,111195]);theta=math.radians(c['heading'])
    axes=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    others=[(r,shapely.transform(shape(r['geometry']),lambda a:(a-center)*scale)) for r in rows if r['localId']!=src['owners'][0]['local_id'] and shape(r['geometry']).distance(Point(lon,lat))<.0025]
    targets=[('east upper casements',-6.5,4.8),('entry',-1.15,2.1),('balcony door',3.12,4.6),('western upper casement',7.8,4.8)]
    # MapLibre's default FOV gives camera-frustum distance 1.5 × viewport pixels.
    # Current application overview uses pitch 60 deg for the real directory path.
    views=[('initial default',157,60,c['overviewZoom'],0,0,0),('final default',c['overviewBearing'],60,c['overviewZoom'],0,0,0),
           ('door detail',174,65,20.65,-1.20,-.20,3.35),('balcony detail',174,65,20.62,3.15,-.10,4.25),('retained source context',c['heading']+33,43,19.55,0,1.85,6.10)]
    result=[]
    for name,bearing,pitch,zoom,cx,cy,elevation in views:
        a=math.radians(bearing);pitch_r=math.radians(pitch)
        out=np.array([-math.sin(a),-math.cos(a)])
        for viewport in (650,844):
            distance=viewport*1.5*(2*math.pi*6371008.8*cos)/(512*2**zoom)
            eye=out*distance*math.sin(pitch_r)+np.array([cx,cy])@axes
            high=elevation+distance*math.cos(pitch_r)
            probes=[]
            for feature,x,z in targets:
                p=np.array([x,0])@axes;ray=LineString([p,eye])
                blocked=[]
                for r,g in others:
                    segment=ray.intersection(g)
                    if segment.is_empty:continue
                    h=z+(high-z)*segment.distance(Point(p))/ray.length
                    if h<r['height']:blocked.append({'owner':r['localId'],'above_ray_m':round(r['height']-h,3)})
                probes.append({'feature':feature,'intervening_owners':blocked})
                if name=='initial default':assert 387 in [b['owner']for b in blocked]
                else:assert not blocked,(name,viewport,feature,blocked)
            result.append({'view':name,'bearing':bearing,'pitch':pitch,'zoom':zoom,'viewport_height':viewport,'rays':probes})
    args.report.write_text(json.dumps({'id':c['id'],'feature_table_sha256':digest,'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Approximate MapLibre fixed-FOV approach against independent source footprints and nominal roof heights. Detailed source relief and viewport padding require real browser frames.','views':result},ensure_ascii=False,indent=2)+'\n')
    print('Checked four sightlines for five camera configurations at two viewport heights.')

if __name__=='__main__':
    main()
