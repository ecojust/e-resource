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
SOURCE=AUDIT.parents[2]/'source/precise/xuhui-medical-college-east-building-one/footprint-review.json'

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
    assert digest==src['frozen_bindings']['feature-table.json.gz']['sha256']
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
    targets=[('central lawn arch',-.95,6.70,2.6),('west pylon',-7.3,6.5,11.2),('east pylon',6.5,6.5,11.2),
             ('left pavilion roof',-51.4,17.1,17.8),('right pavilion roof',51.3,18.5,17.8),('auditorium ridge',-.95,-3.12,19.83)]
    views=[('northeast oblique',-139,57,c['overviewZoom'],0,0,0),
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
                probes.append({'feature':feature,'local_target_m':[x,y,z],'intervening_owners':blocked})
                if name=='selected default':assert not blocked,(name,viewport,feature,blocked)
            result.append({'view':name,'bearing':bearing,'pitch':pitch,'zoom':zoom,'viewport_height':viewport,'rays':probes})
    args.report.write_text(json.dumps({'id':c['id'],'feature_table_sha256':digest,'contract_sha256':hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'method':'Approximate MapLibre fixed-FOV approach against the surrounding school and city source footprints and nominal roof heights. Detailed source relief and viewport padding require real browser frames.','views':result},ensure_ascii=False,indent=2)+'\n')
    print('Checked six sightlines at two camera approaches and two viewport heights.')

if __name__=='__main__':
    main()
