"""Check independently traced roof, external wall returns, level step and aperture rays of a delivered GLB."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np
from shapely.geometry import Point, Polygon

from plan_points import load
from register_courtyard import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from courtyard_shell import envelope, strip
SerialScene=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']


def check(mesh):
    scene=SerialScene(mesh)
    v={k:np.asarray(a)for k,a in envelope().items()}
    keys=['p00','p01','p02','p03','p04','p05','s06','p06','p07','p08','p09','p10']
    ring=Polygon([v[k]for k in keys])
    projection=Polygon([v[k]for k in ('p06','p07','p08','p09')])
    raised_ledge=projection.union(strip(v['p06'],v['p09'],.15))
    results=[]
    def ray(name,origin,direction,length,accepted,z=None):
        hit=scene.ray(origin,direction,length)
        ok=bool(hit and any(item in hit['material']for item in accepted))
        if ok and z is not None:ok=abs(hit['point_enu_m'][2]-z)<.022
        results.append(dict(control=name,origin=np.asarray(origin).tolist(),direction=np.asarray(direction).tolist(),hit=hit,expected_material_fragments=accepted,expected_z=z,passed=ok))
    for j,k in zip(keys,keys[1:]+keys[:1]):
        a,c=v[j],v[k]
        t=(c-a)/np.linalg.norm(c-a); inside=np.array([t[1],-t[0]])
        for f in (.16,.50,.84):
            p=(1-f)*a+f*c+.46*inside
            if ring.boundary.distance(Point(p))<.38 or not ring.contains(Point(p)):continue
            z=11.91 if raised_ledge.covers(Point(p)) else 11.04
            ray(f'roof inside {j}–{k} {f}',[*p,15],[0,0,-1],5,['flat concrete'],z)
    a,c=v['p06'],v['p09'];t=(c-a)/np.linalg.norm(c-a);normal=np.array([t[1],-t[0]])
    for f in (.16,.32,.50,.68,.84):
        p=(1-f)*a+f*c
        ray('internal roof step '+str(f),[*(p+.39*normal),11.51],[*(-normal),0],.8,['flat concrete'])
    for j,k in [('p00','p01'),('p01','p02'),('p02','p03'),('s06','p06')]:
        a,c=v[j],v[k];t=(c-a)/np.linalg.norm(c-a);inside=np.array([t[1],-t[0]])
        for z in (.5,5.4,10.7):
            p=(a+c)/2-.19*inside
            ray(f'{j}–{k} wall {z}',[*p,z],[*inside,0],.32,['courtyard render'])
    for x in (.83,.85,.875,.90,.92):
        ray('north window panel to return '+str(x),[x,4.46,6],[0,-1,0],.28,['courtyard render'])
    plan=load()
    # Two secondary apertures in the courtyard wings must be reached without
    # intersecting the enclosing shell or the plinth behind their photographed planes.
    for key,picks in [('case1',[(424,120),(455,171),(508,169)]),('case2',[(326,91),(385,110),(488,125)])]:
        cam=Camera(key);pose=np.array(plan['facade_frames'][key]['local_to_ENU'])
        eye=(pose@[*cam.c,1])[:3]
        for uv in picks:ray(key+' photographed pane '+str(uv),eye,pose[:3,:3]@cam.ray(uv),50,['glass','reflection'])
    return {'asset':scene.asset,'coordinate_system':'local ENU, metres','passed':all(x['passed']for x in results),'counts':[sum(x['passed']for x in results),len(results)],'tests':results}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();r=check(args.mesh);args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print(r['counts'],[(x['control'],x['hit'] and x['hit']['material']) for x in r['tests']if not x['passed']]);sys.exit(int(not r['passed']))
