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
    # These local points were first intersected against the full and reduced exported meshes.
    # Each point lies on the visible face of its named surface from both public viewports.
    return [('中央底层拱窗', 0.2, -1.239451, 2.78), ('三角山花', 0.000167, -1.794451, 8.662722), ('中央中层长窗', 0.25, -1.239451, 10.65), ('中央顶层窗轴', 0.24, -1.239451, 14.71), ('西侧石窗框', -2.353764, -0.435665, 6.986903), ('南侧山花', 2.010902, -0.983588, 8.6761), ('四川中路首开间上窗', -3.569254, 2.067543, 10.81), ('汉口路首开间上窗', 4.253534, 1.399612, 10.87), ('塔身分层石檐', -1.979301, -1.150676, 12.9925), ('浅色托齿', 2.189237, -1.038598, 16.407928), ('矮铜穹前缘', 8.4e-05, -1.327813, 17.672342), ('中央细杆', 6.2e-05, 1.078546, 19.306025)]



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
             ('四川中路侧',29,48),('汉口路侧',1,48),('较高机位',17,35),('较低机位',17,55)]
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
