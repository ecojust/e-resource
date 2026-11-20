"""Cast rays at the two street elevations, the northeast chamfer and its stepped lantern."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

AUDIT=Path(__file__).resolve().parent
SOURCE=AUDIT.parents[2]/'source/precise/huangpu-cishu-building/footprint-review.json'
RAY=AUDIT.parents[2]/'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec=importlib.util.spec_from_file_location('triangle_intersection',RAY)
ray=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ray)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def elevation(vertices,a,b):
    t=np.asarray(b)-a;t=t/np.linalg.norm(t)
    inward=np.array([-t[1],t[0]])
    origin=(a+b)/2
    g=vertices.copy()
    g[:,:,0]=(vertices[:,:,[0,2]]-origin)@t
    g[:,:,2]=(vertices[:,:,[0,2]]-origin)@inward
    return g


def nearer(a,b,length):
    return a+(b-a)*length/np.linalg.norm(b-a)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--work',required=True,type=Path,help='retain the decode from verify-placement.py --work')
    cli.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
    args=cli.parse_args();r=json.loads(SOURCE.read_bytes());frame=r['local_frame']
    v=np.asarray(frame['source_vertices_relative_to_chamfer_midpoint_m'])-frame['origin_relative_to_chamfer_midpoint_m']
    east=nearer(v[2],v[3],3.46);north=nearer(v[1],v[0],3.58)
    GLASS='smoky blue window glass';SHOP='dark shopfront plate glass';STONE='carved pale stone'
    features={
        'corner':(v[2],v[1],[
            ('lower shop glass',.35,2.10,SHOP,.26,.34),('solid ground jamb',1.73,2.10,STONE,-.03,.03),
            ('lintel over shop',.27,4.25,'warm ivory facing stone',-.47,-.42),
            ('arched upper shop window',.25,6.68,SHOP,.27,.33),('gold fan below paired windows',0,8.22,'golden bronze ornament',-.125,-.095),
            ('left paired casement',-.39,10.33,GLASS,.27,.33),('right paired casement',.40,13.40,GLASS,.27,.33),
            ('right paired top light',.39,23.11,GLASS,.27,.33),('paired central stone rib',0,15.99,STONE,-.03,.03),
            ('top of octagonal shaft',0,29.87,'warm ivory facing stone',.70,.93),
            ('open metal ring at lantern',0,32.33,'muted bronze relief',.98,1.17),
            ('lantern glass behind ring',.18,32.12,'honey lantern glass',1.61,1.85),
            ('flagstaff',0,34.72,'aged dark steel sash',2.10,2.25)]),
    }
    for name,a,b,groups in [('Shandong',v[3],east,3),('Nanjing',north,v[0],1)]:
        pitch=np.linalg.norm(b-a)/groups
        features[name]=(a,b,[
            ('first narrow light',-1.5*pitch*.185,10.20,GLASS,.27,.33),
            ('second narrow light',-.5*pitch*.185,13.24,GLASS,.27,.33),
            ('third narrow light',.5*pitch*.185,16.56,GLASS,.27,.33),
            ('fourth narrow light',1.5*pitch*.185,22.96,GLASS,.27,.33),
            ('two-light arch',-pitch*.205+.16,6.2,SHOP,.27,.33),
            ('gold arch inlay',pitch*.205,8.22,'golden bronze ornament',-.125,-.095),
            ('upper bay spandrel',.5*pitch*.185,14.97,'grey recessed spandrels',-.066,-.008)])
    for name,a,b,sign in [('Shandong stepped shoulder',east,v[2],1),('Nanjing stepped shoulder',v[1],north,-1)]:
        width=np.linalg.norm(b-a)
        features[name]=(a,b,[
            ('first raised return',-.08*width*sign,26.20,STONE,-.075,-.032),
            ('second raised return',.26*width*sign,26.81,STONE,-.075,-.032),
            ('upper shoulder edge at tower junction',.49*width*sign,27.29,STONE,-.075,-.032)])
    results=[]
    for variant in json.loads((args.work/'delivered-decode.json').read_bytes()):
        vertices=np.fromfile(variant['triangle_file'],np.float64).reshape(-1,3,3);vertices[:,:,2]*=-1
        mats=np.fromfile(variant['triangle_material_ids_file'],np.uint16)
        rows=[]
        for side,(a,b,samples) in features.items():
            rotated=elevation(vertices,a,b)
            for item,u,h,mat,low,high in samples:
                actual,depth=ray.face_hit(rotated,mats,variant['material_names'],u,h)
                assert actual==mat and low<=depth<=high,(variant['variant'],side,item,actual,depth)
                rows.append({'side':side,'feature':item,'horizontal_m':u,'height_m':h,'first_inward_depth_m':depth,'material':actual})
        results.append({'variant':variant['variant'],'sha256':variant['sha256'],'rays':rows})
    args.report.write_text(json.dumps({'id':r['model_id'],'method':'First material and depth intersected from a point outside each registered street face. Rays include both flat walls and three distinct upper metal, glazing and mast components.','script_sha256':sha(Path(__file__)),'ray_math_sha256':sha(RAY),'variants':results},ensure_ascii=False,indent=2)+'\n')
    print('Verified',sum(len(r['rays'])for r in results),'independent facade and lantern material samples')
if __name__=='__main__':
    main()
