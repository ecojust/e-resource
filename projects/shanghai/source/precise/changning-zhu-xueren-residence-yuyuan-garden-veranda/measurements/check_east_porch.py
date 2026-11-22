"""Cast each observation through all actual triangles; report frontmost material and the nearest pixel tolerance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles

def read(name):
    return json.loads((HERE/name).read_bytes())

def cameras():
    wr=read('east-porch-five-view-world.json')['world'];c=wr['axis_spacing_m']
    world_to_local=np.array([[0,1/c,0,-wr['southern_column_Y']/c],[-1/c,0,0,wr['column_X']/c],[0,0,1/c,-wr['sill_Z']/c],[0,0,0,1.]])
    east=read('east-porch-three-photo-section.json')['cameras']
    return {name:np.array(cam['P'])@world_to_local for name,cam in east.items()}

def family(m):
    prefix=(m or '').lower()
    if 'east stair' in prefix:return 'paving'
    if 'east porch' in prefix:
        if 'oxide' in prefix or 'red moulding' in prefix:return 'post'
        return 'soffit' if 'soffit'in prefix else 'fascia'
    if 'east window' in prefix:return 'sash-glass' if 'pane'in prefix else 'sash-wood'
    if 'east door' in prefix:return 'door-glass' if 'glass'in prefix else 'door-timber'
    if 'east wall' in prefix:return 'render'
    return 'other'

def evaluate(tri,matids,mats):
    pts=read('east-porch-independent-photo-points.json')['probes'];ans={}
    a=tri[:,0];ed1=tri[:,1]-a;ed2=tri[:,2]-a
    for name,p in cameras().items():
        inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3];oc=eye-a;cr=np.cross(oc,ed1);ds=np.einsum('ij,ij->i',ed2,cr)
        projected=tri@p[:,:3].T+p[:,3];z=projected[:,:,2];uv=projected[:,:,:2]/np.where(abs(z)<1e-9,1e-9,z)[:,:,None]
        lo=np.min(uv,axis=1);hi=np.max(uv,axis=1);cross=z.min(axis=1)<0;front=z.max(axis=1)>0
        def ray(px):
            sel=np.flatnonzero(front&(((lo<=px).all(axis=1)&(hi>=px).all(axis=1))|cross))
            if len(sel)==0:return None
            v=inv@[*px,1.];v/=np.linalg.norm(v);h=np.cross(v,ed2[sel]);det=np.einsum('ij,ij->i',ed1[sel],h)
            ok=abs(det)>1e-10;den=np.where(ok,det,1);u=np.einsum('ij,ij->i',oc[sel],h)/den
            b=(cr[sel]@v)/den;t=ds[sel]/den;good=np.flatnonzero(ok&(u>=0)&(b>=0)&(u+b<=1)&(t>1e-5))
            return mats[matids[sel[good[np.argmin(t[good])]]]] if len(good)else None
        rows=[]
        for pt in (q for q in pts if q['photo']==name):
            uv=np.array(pt['working_uv']);mat=ray(uv);wants=pt['expected_families'];dist=0 if family(mat)in wants else None
            if dist is None:
                for radius in (1,2,3):
                    if any(family(ray(uv+radius*np.array([np.cos(t),np.sin(t)])))in wants for t in np.arange(8)*np.pi/4):
                        dist=radius;break
            rows.append(dict(feature=pt['feature'],working_uv=pt['working_uv'],expected=wants,first_material=mat,within_radius_px=dist))
        ans[name]=dict(total=len(rows),direct=sum(r['within_radius_px']==0 for r in rows),within_three=sum(r['within_radius_px']is not None for r in rows),samples=rows)
    return dict(triangles=len(tri),views=ans)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path);args=ap.parse_args()
    result=evaluate(*load_triangles(args.mesh)[:3]);result['sha256']=hashlib.sha256(args.mesh.read_bytes()).hexdigest();args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print([(k,d['direct'],d['within_three'],d['total'])for k,d in result['views'].items()])
