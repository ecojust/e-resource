"""Check the public map camera against the rounded street corner and retained neighboring buildings."""
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
LOCAL=[('curved pale upper balustrade',1.0,-1.88,7.8),('second-floor engaged red shaft',1.38,-1.49,5.77),
       ('low surviving attic drum',1.27,-1.35,13.46),('Dianchi Road arched doorway',-3.46,-.71,2.10),
       ('east return segmental window',1.03,4.12,6.07),('ground-floor canopy',.99,-1.87,2.65),
       ('upper shaft and cornice',1.17,-1.71,10.70),('short west window wall',-7.15,-.71,9.52)]


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
        if row['localId']==102:geom=geom.difference(mask)
        other.append((row['localId'],geom,row['height']))
    h=math.radians(receipt['heading'])
    targets=[(name,x*math.cos(h)+y*math.sin(h),-x*math.sin(h)+y*math.cos(h),z)for name,x,y,z in LOCAL]
    choices=[('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
             ('east sidewalk',-70,49),('south sidewalk',-23,46),('high crossing',-43,37),('lower crossing',-42,61)]
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
    assert all(r['clear_count']>=7 and all(p['clear']for p in r['probes'][:3])for r in cases['delivered'])


if __name__=='__main__':
    main()
