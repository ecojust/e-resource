"""Verify the Renji ward tower, numbered portal and gallery depths in all three delivered meshes."""
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
SAMPLES=[
    ('recessed entrance glass',0.42,1.7,('cool blue-grey glazing',),0.318,0.382),
    ('portal arch jamb',2.53,2.28,('carved pale stone',),-1.292,-1.228),
    ('shallow crown of arch',0.44,4.13,('carved pale stone',),-1.292,-1.228),
    ('number medallion field',0.2,4.64,('ivory stone cladding',),-1.402,-1.338),
    ('numeral two on plaque',0.02,4.48,('graphite railings',),-1.417,-1.353),
    ('three-part lobby sash',0.38,6.32,('cool blue-grey glazing',),-0.972,-0.908),
    ('tower eastern stair light',0.85,15.04,('cool blue-grey glazing',),-0.012,0.052),
    ('tower western stair light',-0.73,11.46,('cool blue-grey glazing',),-0.012,0.052),
    ('tower central stair light',0.06,19.0,('cool blue-grey glazing',),-0.012,0.052),
    ('tower upper right paired light',1.99,28.0,('cool blue-grey glazing',),-0.012,0.052),
    ('vent above brow',0.09,22.29,('cool blue-grey glazing',),-0.012,0.052),
    ('projecting stair brow',1.32,21.17,('carved pale stone',),-1.022,-0.958),
    ('left gallery rail',-7.38,19.98,('graphite railings',),-0.64,-0.576),
    ('right narrow gallery light one',5.93,19.79,('cool blue-grey glazing',),0.288,0.352),
    ('right narrow gallery light four',9.01,20.02,('blackened steel sash',),0.138,0.202),
    ('western regular high window',-8.48,23.18,('cool blue-grey glazing',),0.288,0.352),
    ('east plinth window',8.58,1.19,('cool blue-grey glazing',),0.288,0.352),
    ('dark brick and mortar between bays',10.07,14.28,('mauve facing brick','grey facing brick','smoked brown facing brick','warm grey mortar'),-0.047,0.017),
    ('ivory tower crown',0,29.36,('ivory stone cladding',),-0.332,-0.268),
    ('flat stone tower crown',0,30.09,('carved pale stone',),-0.397,-0.333),
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
    args.report.write_text(json.dumps({'id':'huangpu-renji-hospital-ward-entrance','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(r['rays'])for r in result),'material and depth samples')
if __name__=='__main__':
    main()
