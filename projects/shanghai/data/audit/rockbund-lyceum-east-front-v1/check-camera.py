"""Check the public map camera against the cut street corner and retained neighboring buildings."""
from argparse import ArgumentParser
import gzip
import json
import math
from pathlib import Path
import runpy
from shapely.affinity import scale,translate
from shapely.geometry import Point,shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SHARED=runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))
def eye_points(record):
    source=PROJECT/'source/precise'/record['model_id']/'source/frontage-registration.json'
    edges=json.loads(source.read_bytes())['visible_edges_local_m']
    probes=[(0,'塔门185门牌',-10.80,2.18,-.30),(0,'门额',-10.80,3.76,.14),(0,'塔身第三排窄窗',-10.80,12.74,-.29),(0,'券窗上方三角楣',-10.80,22.28,.30),(0,'上段半圆大窗',-10.80,31.74,-.35),(0,'塔楼檐带',-10.80,35.17,-.15),(0,'北翼街层窗',.22,2.15,-.30),(0,'三联钢窗',7.8,10.16,-.30),(0,'浅石框顶层短窗',10.1,16.35,-.30),(0,'退台兼栏杆',6.4,19.07,-.11),(0,'后退上层窗',4.7,23.40,-1.26)]
    result=[]
    for edge,label,u,z,depth in probes:
        a,b=edges[edge:edge+2]
        dx,dy=b[0]-a[0],b[1]-a[1]
        length=math.hypot(dx,dy);tx,ty=dx/length,dy/length
        result.append((label,(a[0]+b[0])/2+tx*u+ty*depth,(a[1]+b[1])/2+ty*u-tx*depth,z))
    return result



def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--contract',type=Path,default=HERE/'final-placement-contract.json')
    parser.add_argument('--table',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE/'camera-sightlines.json')
    args=parser.parse_args()
    receipt=json.loads(args.contract.read_bytes())
    record=json.loads((PROJECT/'source/precise'/receipt['id']/'footprint-review.json').read_bytes())
    expected=next(b['sha256'] for b in record['frozen_bindings'] if b['repository_path'].endswith('/feature-table.json.gz'))
    assert SHARED['digest'](args.table.read_bytes())==expected
    lon,lat=receipt['lng'],receipt['lat'];north=math.radians(1)*SHARED['EARTH'];east=north*math.cos(math.radians(lat))
    def convert(poly):
        return scale(translate(poly,xoff=-lon,yoff=-lat),xfact=east,yfact=north,origin=(0,0))
    mask=convert(shape(receipt['replacement_geometry']))
    other=[]
    for row in json.loads(gzip.decompress(args.table.read_bytes()))['features']:
        geom=shape(row['geometry'])
        if geom.distance(Point(lon,lat))>.002:continue
        geom=convert(geom)
        if geom.distance(Point(0,0))>150:continue
        if row['localId']==2358:geom=geom.difference(mask)
        other.append((row['localId'],geom,row['height']))
    h=math.radians(receipt['heading'])
    targets=[(name,x*math.cos(h)+y*math.sin(h),-x*math.sin(h)+y*math.cos(h),z)for name,x,y,z in eye_points(record)]
    choices=[('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
             ('南向斜视',-123,38),('北向斜视',-71,37),('较高机位',-97.28,28),('较低机位',-97.28,52)]
    cases={}
    for name,bearing,pitch in choices:
        rows=[]
        for label,width,height,padding in SHARED['VIEWS']:
            viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],padding)))
            rows.append(SHARED['evaluate']({**receipt,'overviewBearing':bearing,'overviewPitch':pitch},
                                           viewport,label,other,lon,lat,east,north,targets))
        cases[name]=rows
    result={'id':receipt['id'],'contract_sha256':SHARED['digest'](args.contract.read_bytes()),
            'camera_module_sha256':SHARED['digest']((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
            'retained_volumes':len(other),'source_sha256':expected,'cases':cases}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print({key:[v['clear_count'] for v in vset]for key,vset in cases.items()})
    assert all(r['clear_count']==len(r['probes'])for r in cases['delivered'])


if __name__=='__main__':
    main()
