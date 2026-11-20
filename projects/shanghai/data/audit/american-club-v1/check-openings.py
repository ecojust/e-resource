"""Verify the American Club portico, window and masonry depths in all three delivered meshes."""
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
BRICK=('dark chocolate pressed brick','purple brown pressed brick','warm chocolate pressed brick','weathered mortar')
SAMPLES=[
 ('recessed fanlight',.27,4.11,('recessed blue-grey glass',),.30,.33),
 ('paired door light',.58,2.0,('recessed blue-grey glass',),.24,.29),
 ('solid paired timber leaf',.59,1.0,('stained entrance timbers',),.33,.37),
 ('Tuscan column base',1.65,1.1,('warm white marble',),-1.24,-1.18),
 ('portico entablature',.38,5.68,('carved pale stone',),-1.38,-1.28),
 ('portico continuous top rail',.38,6.85,('painted wrought iron',),-1.35,-1.29),
 ('middle seven-bay balcony glazing',.27,7.45,('recessed blue-grey glass',),.30,.34),
 ('lower side bay glazing',6.84,2.76,('recessed blue-grey glass',),.30,.34),
 ('brown spandrel masonry',2.25,13.67,BRICK,-.02,.005),
 ('east lower office glazing',-9.68,11.78,('recessed blue-grey glass',),.30,.34),
 ('west upper office glazing',10.11,18.61,('recessed blue-grey glass',),.30,.34),
 ('upper arch glazing',.27,23.76,('recessed blue-grey glass',),.30,.34),
 ('white attic paired pilaster',1.78,23.17,('warm white marble',),-.18,-.14),
 ('first office centre keystone',.11,13.31,('warm white marble',),-.17,-.15),
 ('east eaves cross the corner without an open joint',-12.15,25.52,('warm white marble',),-.83,-.81),
 ('west eaves cross the corner without an open joint',12.15,25.52,('warm white marble',),-.83,-.81),
 ('crown projecting cornice',.18,25.52,('warm white marble',),-.83,-.81),
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
    args.report.write_text(json.dumps({'id':'huangpu-american-club','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(r['rays'])for r in result),'material and depth samples')
if __name__=='__main__':
    main()
