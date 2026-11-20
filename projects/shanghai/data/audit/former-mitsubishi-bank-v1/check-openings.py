"""Check the projected portico shafts, two lions, five-bay glazing, door leaf, lettering support and attic against all three meshes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

AUDIT=Path(__file__).resolve().parent
RAY=AUDIT.parents[2]/'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec=importlib.util.spec_from_file_location('first_surface',RAY)
ray=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ray)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
STONE='light dressed granite';CUT='carved capital stone';GLASS='smoky bronze glass';IRON='dark metal window grilles';DOOR='dark bronze entrance';BRONZE='patinated cast bronze';BASE='dark granite foundation'
SAMPLES=[
 ('west round shaft',-6.55,5.6,(STONE,),-1.04,-.78),
 ('west middle shaft',-2.19,6.50,(STONE,),-.94,-.78),
 ('east middle shaft',2.19,9.1,(STONE,),-.89,-.75),
 ('east round shaft',6.55,6.22,(STONE,),-.95,-.75),
 ('square capital abacus',2.19,12.55,(CUT,),-1.18,-1.00),
 ('shaft base moulding',6.55,1.07,(STONE,),-1.16,-.90),
 ('recessed vestibule glass',-4.21,8.25,(GLASS,),1.98,2.16),
 ('east vestibule glass',4.57,8.25,(GLASS,),1.98,2.16),
 ('central tall window glass',.19,9.24,(GLASS,),1.98,2.16),
 ('west outer window',-10.98,11.46,(GLASS,),.19,.30),
 ('east outer window',11.53,8.11,(GLASS,),.18,.32),
 ('central entrance left door',-1.074,1.56,(DOOR,),2.19,2.29),
 ('central entrance glass',.75,2.64,(GLASS,),2.15,2.27),
 ('west secondary doorway',-11.12,1.10,(DOOR,),.45,.52),
 ('door inscription tablet',.47,3.94,(STONE,),1.54,1.71),
 ('unobstructed pavement side wall',-13.40,5.4,(STONE,),-.02,.02),
 ('west attic window',-11.13,18.33,(GLASS,),.77,.88),
 ('central attic glass',.11,18.39,(GLASS,),.77,.88),
 ('main cornice',2.94,17.018,(CUT,),-.64,-.53),
 ('front name beam backing',7.3,13.12,(CUT,),-.22,-.18),
 ('upper granite facing',2.7,19.76,(STONE,),.54,.61),
 ('west lion torso',-4.73,1.14,(BRONZE,),-.81,-.46),
 ('east lion torso',4.73,1.14,(BRONZE,),-.81,-.46),
 ('street front lowest stair',.38,.09,(BASE,),-1.25,-1.17)]

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
    args=cli.parse_args();variants=[]
    for record in json.loads((args.work/'delivered-decode.json').read_bytes()):
        tri=np.fromfile(record['triangle_file'],np.float64).reshape(-1,3,3);tri[:,:,2]*=-1
        ids=np.fromfile(record['triangle_material_ids_file'],np.uint16);hits=[]
        for label,x,height,materials,low,high in SAMPLES:
            mat,depth=ray.face_hit(tri,ids,record['material_names'],x,height)
            assert mat in materials and low<=depth<=high,(record['variant'],label,mat,depth)
            hits.append({'feature':label,'x_m':x,'height_m':height,'material':mat,'first_y_m':depth})
        variants.append({'variant':record['variant'],'sha256':record['sha256'],'rays':hits})
    args.report.write_text(json.dumps({'id':'huangpu-former-mitsubishi-bank','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':variants},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(v['rays'])for v in variants),'street-side surface and depth probes')
if __name__=='__main__':
    main()
