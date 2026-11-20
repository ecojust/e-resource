"""Inspect first-hit glazing, rustication, brackets, shell scrolls and attic setbacks in every delivery GLB."""
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
STONE='dressed limestone'
GLASS='smoky blue street glass'
LIGHT='pale cement ornament'
PANEL='ebonised metal spandrels'
SAND='weathered buff stucco'
STEEL='black steel mullions'
SAMPLES=[
 ('recessed granite tread',.45,.45,('dark granite entrance treads',),.92,.98),
 ('opaque lower door panel',.7,.93,(PANEL,),1.105,1.16),
 ('upper door glazing',.75,1.65,(GLASS,),1.105,1.16),
 ('arched shop sash',-9.67,2.02,(GLASS,),.29,.35),
 ('rusticated wall adjoining a northern arch',6.95,2.33,('scored grey cement blocks',),-.08,-.04),
 ('projecting keystone at the arch crown',4.90,4.32,(STONE,),-.20,-.16),
 ('second-storey window',-4.71,6.21,(GLASS,),.29,.35),
 ('three-storey southern window',-9.47,9.84,(GLASS,),.29,.35),
 ('first intermediate spandrel',-9.87,11.55,(PANEL,),.075,.12),
 ('full-density mullion or distant glazing',-5.91,16.75,(STEEL,GLASS),.17,.34),
 ('three-storey northern window',9.73,17.51,(GLASS,),.29,.35),
 ('north fluted giant shaft',2.51,13.14,(STONE,),-.78,-.73),
 ('south fluted giant shaft',-2.49,16.15,(STONE,),-.76,-.71),
 ('present rounded south corbel',-2.46,7.04,(STONE,),-.85,-.78),
 ('projecting central balcony parapet',.42,7.77,(STONE,),-.91,-.84),
 ('secondary pilaster capital',-7.36,19.1,(SAND,),-.43,-.38),
 ('Corinthian north leaf carving',2.48,19.07,(LIGHT,),-1.27,-1.10),
 ('north capital volute',3.01,19.37,(LIGHT,),-1.29,-1.22),
 ('crested pediment shell',.25,21.92,(LIGHT,),-.89,-.73),
 ('inner scallop-shell ribs',.05,22.21,(LIGHT,),-.86,-.73),
 ('inset triangular tympanum',.29,20.76,(SAND,),-.94,-.86),
 ('right-hand scroll beside shell',1.66,21.19,(LIGHT,),-.85,-.77),
 ('outer sixth-floor sash',-9.74,22.19,(GLASS,),.415,.46),
 ('set-back central sixth-floor sash',4.67,22.12,(GLASS,),1.015,1.065),
 ('set-back central seventh-floor transom',.22,26.47,(STEEL,),1.18,1.25),
 ('glass above seventh-floor transom',.22,26.65,(GLASS,),1.31,1.37),
 ('outer seventh-floor sash',9.70,26.71,(GLASS,),.65,.71),
 ('flagstaff above crest',0,30.5,('patinated bronze metal',),.67,.75)]


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
    args.report.write_text(json.dumps({'id':'huangpu-brunner-mond-building','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':variants},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(v['rays'])for v in variants),'street-side surface and depth probes')
if __name__=='__main__':
    main()
