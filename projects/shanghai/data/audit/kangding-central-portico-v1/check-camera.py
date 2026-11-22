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
    return [('西圆柱柱身', -2.68, -0.35067, 3.63), ('东圆柱柱身', 2.68, -0.35067, 3.63), ('西柱顶方帽', -2.68, -0.44, 8.59), ('东柱顶方帽', 2.68, -0.44, 8.59), ('西段露台石栏', -5.9347, -0.23521, 5.82), ('中段露台石栏', -0.6316, -0.23521, 5.82), ('东段露台石栏', 4.6953, -0.23521, 5.82), ('中段石栏顶', 0.0, -0.32414, 6.23), ('顶层回纹栏墙', 0.1, -0.2, 10.12), ('正中老虎窗玻璃', 0.42, 1.875, 14.0), ('老虎窗顶徽', 0.0, 1.34, 15.91), ('坡顶陶瓦', -5.8, 3.52585, 15.03)]



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
        if row['localId']==record['selection']['owner']:geom=geom.difference(mask)
        other.append((row['localId'],geom,row['height']))
    h=math.radians(receipt['heading'])
    targets=[(name,x*math.cos(h)+y*math.sin(h),-x*math.sin(h)+y*math.cos(h),z)for name,x,y,z in eye_points(record)]
    choices=[('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
             ('花园西侧',321,43),('花园东侧',347,43),('较高机位',332,35),('较低机位',332,52)]
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
