"""Verify No. 3's geometry, glazing and open balcony recess in each delivered mesh."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

AUDIT=Path(__file__).resolve().parent
RAY=AUDIT.parents[2]/'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec=importlib.util.spec_from_file_location('geometry_ray',RAY)
ray=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ray)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
BRICK=('smoke brown facing brick','purple brown facing brick','burnished russet facing brick')
SAMPLES=[
 ('ceramic green house plate',1.043,1.88,('green ceramic number plaque',),-1.53,-1.50),
 ('raised house number 3',1.061,2.003,('faded numeral',),-1.54,-1.516),
 ('gate leaf',1.985,1.07,('dark weathered gate',),-1.08,-1.05),
 ('gate jamb',2.675,1.44,('blue grey cast stone',),-1.48,-1.45),
 ('east middle glazed light',-3.07,4.44,('muted blue window glass',),.49,.53),
 ('other middle glazed light',-.79,4.44,('muted blue window glass',),.49,.53),
 ('east upper glazed light',-3.07,7.13,('muted blue window glass',),.49,.53),
 ('other upper glazed light',-.79,7.13,('muted blue window glass',),.49,.53),
 ('ground glazed light',-3.12,1.36,('muted blue window glass',),.49,.53),
 ('brick field between paired lights',-1.98,4.8,BRICK,.135,.170),
 ('over-eaves brick blade',.12,8.37,BRICK,-.34,-.30),
 ('left recess behind balcony rail',1.45,4.80,('dark fascia and roof edge',),.72,.76),
 ('glazed right balcony bay',2.43,4.72,('muted blue window glass',),.25,.29),
 ('steel balcony guard',2.05,4.49,('blackened steel window frames',),-.22,-.175),
 ('setback half-round light',1.67,6.95,('muted blue window glass',),1.24,1.28),
]

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',required=True,type=Path,help='Directory retained by verify-placement.py --work')
    cli.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
    args=cli.parse_args();result=[]
    for r in json.loads((args.work/'delivered-decode.json').read_bytes()):
        t=np.fromfile(r['triangle_file'],np.float64).reshape(-1,3,3);t[:,:,2]*=-1
        m=np.fromfile(r['triangle_material_ids_file'],np.uint16);names=r['material_names'];records=[]
        for label,x,z,materials,lo,hi in SAMPLES:
            material,y=ray.face_hit(t,m,names,x,z)
            assert material in materials and lo<=y<=hi,(label,r['variant'],material,y)
            records.append({'visible_feature':label,'x_m':x,'height_m':z,'first_y_m':y,'material':material})
        result.append({'variant':r['variant'],'sha256':r['sha256'],'rays':records})
    args.report.write_text(json.dumps({'id':'jingan-yuhua-new-residential-quarter-03','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(r['rays'])for r in result),'material and depth samples')
if __name__=='__main__':
    main()
