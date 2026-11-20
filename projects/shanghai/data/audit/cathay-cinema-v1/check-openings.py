"""Measure the Cathay tower and marquee lettering, glazing and brickwork in all three issued variants."""
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
BRICK=('claret face brick','rust coloured face brick','purple brown face brick','cream mortar')
BRONZE=('patinated sign bronze',)
SAMPLES=[
 ('left strip window',-4.30,7.18,('blue-grey smoked glass',),.305,.34),
 ('right strip window',4.55,7.18,('blue-grey smoked glass',),.305,.34),
 ('inner-left tall glass',-1.914,8.4,('blue-grey smoked glass',),.305,.34),
 ('inner-right tall glass',2.155,8.4,('blue-grey smoked glass',),.305,.34),
 ('high brick between two slots',3.07,10.67,BRICK,-.014,.002),
 ('stepped tower stone',.39,16.28,('carved pale stone',),-.585,-.55),
 ('recessed glazed entrance leaf',.94,1.59,('blue-grey smoked glass',),.89,.93),
 ('left poster window',-4.34,1.56,('blue-grey smoked glass',),.305,.34),
 ('plaster at mast race',.11,20.04,('carved pale stone',),-.54,-.505),
 ('raised Chinese name 国',-2.3446,4.5979,BRONZE,-1.7030,-1.6870),
 ('raised Chinese name 泰',-1.1347,4.4497,BRONZE,-1.7030,-1.6870),
 ('raised Chinese name 电',-0.0405,4.5621,BRONZE,-1.7030,-1.6870),
 ('raised Chinese name 影',0.9335,4.7555,BRONZE,-1.7030,-1.6870),
 ('raised Chinese name 院',2.4771,4.7639,BRONZE,-1.7030,-1.6870),
 ('horizontal CATHAY C',-2.766,3.6807,BRONZE,-1.7410,-1.7250),
 ('horizontal CATHAY A',-1.2556,3.6717,BRONZE,-1.7410,-1.7250),
 ('horizontal CATHAY T',-0.5284,3.6536,BRONZE,-1.7410,-1.7250),
 ('horizontal CATHAY H',0.5035,3.6932,BRONZE,-1.7410,-1.7250),
 ('horizontal CATHAY A',1.7514,3.6717,BRONZE,-1.7410,-1.7250),
 ('horizontal CATHAY Y',2.3475,3.6882,BRONZE,-1.7410,-1.7250),
 ('vertical CATHAY C',-0.1981,16.9315,BRONZE,-0.6580,-0.6420),
 ('vertical CATHAY A',0.1085,15.2397,BRONZE,-0.6580,-0.6420),
 ('vertical CATHAY T',0.0,13.5281,BRONZE,-0.6580,-0.6420),
 ('vertical CATHAY H',0.0,11.9508,BRONZE,-0.6580,-0.6420),
 ('vertical CATHAY A',0.1085,10.2297,BRONZE,-0.6580,-0.6420),
 ('vertical CATHAY Y',-0.0425,8.5886,BRONZE,-0.6580,-0.6420),
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
            x-=3.27  # Issued origin is east of the measured chamfer midpoint.
            material,y=ray.face_hit(t,m,names,x,z)
            assert material in materials and lo<=y<=hi,(label,r['variant'],material,y)
            records.append({'visible_feature':label,'x_m':x,'height_m':z,'first_y_m':y,'material':material})
        result.append({'variant':r['variant'],'sha256':r['sha256'],'rays':records})
    args.report.write_text(json.dumps({'id':'huangpu-cathay-cinema','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':result},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(r['rays'])for r in result),'material and depth samples')
if __name__=='__main__':
    main()
