"""Compare actual visible surface materials with independently sampled points in the photographed brickwork."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image

def photo_stations(photo, methods):
    witnesses=[]
    with Image.open(photo) as img:
        for tier, d in methods['TIERS'].items():
            left, top, right, bottom = d['crop']
            crop=np.asarray(img.crop(d['crop']),dtype=np.int16)
            origin,scale=methods['registration'](d)
            outer,inner=(methods['controls'](d[k]) for k in ('outer','inner'))
            # Equally spaced stations are independent of the model's traced
            # mortar divisions. Within each small station choose the most uniform
            # brick-colour patch, skipping cables, pale mortar and cut stone.
            for s in np.arange(13,1110,30):
                if 465<s<570:continue
                for depth in (.39,.78):
                    choices=[]
                    for dx in range(-4,5,2):
                        t=(s+dx)/80
                        a,b=(methods['evaluate'](curve,t)for curve in (outer,inner))
                        x,y=np.rint(scale*(a+depth*(b-a))).astype(int)
                        square=crop[y-2:y+3,x-2:x+3].reshape(-1,3)
                        if len(square)!=25:continue
                        median=np.median(square,axis=0)
                        if min(median)<48 or max(median)>156:continue
                        red,green,blue=median
                        if red-blue>31 and red-green>15: expected='Red radial arch brick'
                        elif abs(red-blue)<14 and abs(green-blue)<10: expected='Blue-grey radial arch brick'
                        else: continue
                        scatter=float(np.median(np.max(abs(square-median),axis=1)))
                        if scatter>5:continue
                        choices.append((scatter,abs(dx),[int(x+left),int(y+top)],expected,median.astype(int).tolist()))
                    if choices:
                        _,_,xy,expected,rgb=min(choices)
                        witnesses.append(dict(tier=tier,zone='face',xy=xy,expected=expected,rgb=rgb))
            key=np.array(d['key']);c=np.mean(key,axis=0)
            for fraction in (0,.43):
                pts=key if fraction else [c]
                for pt in pts:
                    x,y=np.rint((c+(pt-c)*fraction)*scale).astype(int)
                    witnesses.append(dict(tier=tier,zone='key',xy=[int(x+left),int(y+top)],expected='Pale keystone and skewbacks',rgb=crop[y,x].tolist()))
    return witnesses

def verify(project, source, mesh, witnesses):
    sys.path.insert(0,str(source))
    from photo_plane import D,H,position
    tools=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    triangles,indices,names,info=tools['load_triangles'](mesh)
    materials=tools['material_appearance'](mesh)['materials']
    double=np.array([materials[n]['doubleSided']for n in names])[indices]
    normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    p=triangles.reshape(-1,3)
    h=np.column_stack((p[:,0],p[:,2],np.ones(len(p))))@H.T + p[:,1,None]*D
    # No triangle crosses the focal plane of this exterior camera.
    if np.min(h[:,2])*np.max(h[:,2])<=0: raise ValueError('Projection crosses camera')
    screen=(h[:,:2]/h[:,2,None]).reshape(-1,3,2)
    bounds_min,bounds_max=np.min(screen,axis=1)-.01,np.max(screen,axis=1)+.01
    results=[]
    for point in witnesses:
        u,v=point['xy'];origin=position(u,v,-1.8);ray=position(u,v,.9)-origin;ray/=np.linalg.norm(ray)
        idx=np.flatnonzero((bounds_min[:,0]<=u)&(bounds_min[:,1]<=v)&(bounds_max[:,0]>=u)&(bounds_max[:,1]>=v))
        idx=idx[double[idx] | ((normals[idx]@ray)<-1e-12)]
        hit=None
        if len(idx):
            i,distance,xyz=tools['first_hit'](triangles[idx],origin,ray)
            if np.isfinite(distance):hit=names[indices[idx[i]]]
        results.append(dict(**point,observed=hit,passed=hit==point['expected']))
    return dict(mesh_sha256=info['sha256'],count=len(results),passed_count=sum(p['passed']for p in results),points=results)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ['project','source','photo','mesh','output']:parser.add_argument('--'+k,required=True,type=Path)
    a=parser.parse_args()
    lib=runpy.run_path(Path(__file__).with_name('measure-voussoirs.py'))
    tests=photo_stations(a.photo,lib)
    result=verify(a.project,a.source,a.mesh,tests)
    result['photo_sha256']=hashlib.sha256(a.photo.read_bytes()).hexdigest()
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['passed_count'],'/',result['count'],[(r['tier'],r['xy'],r['expected'],r['observed'])for r in result['points']if not r['passed']])
if __name__=='__main__':
    main()
