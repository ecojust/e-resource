"""Check the photographed front of the 362 entrance against a component or the complete court."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import sys
from collections import Counter
import numpy as np

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def site_points(door):
    return [
      ('left open leaf',door.PAINT,(76,148),(.05,.12)),('left front upright',door.PAINT,(75,515),(.05,.12)),
      ('left intermediate upright',door.PAINT,(163,342),(.69,.81)),('left far upright',door.PAINT,(231,532),(1.39,1.47)),
      ('right open leaf',door.PAINT,(798,124),(.05,.12)),('right front upright',door.PAINT,(801,485),(.05,.12)),
      ('right far upright',door.PAINT,(755,524),(1.39,1.47)),('right jamb stone',door.AGG,(840,112),(-.05,.01)),
      ('right jamb stone',door.AGG,(843,439),(-.05,.01)),('pale base',door.WASH,(842,622),(-.05,.01)),
      ('green enamel',door.BOARD,(884,78),(-.023,-.020)),('green enamel',door.BOARD,(947,90),(-.023,-.020)),
      ('digit 2 upper stroke',door.TYPE,(945,70),(-.025,-.023)),('white number stroke',door.TYPE,(934,68),(-.025,-.023)),('open space between the two leaves',None,(485,320),None)]

def check_role(path,scene_cls,reg,door,origin,xaxis,yaxis,scale):
    scene=scene_cls(path);t=np.eye(3);t[:2,0]=xaxis;t[:2,1]=yaxis
    local_eye=np.array(reg['camera']['eye']);P=np.array(reg['camera']['P'])
    global_eye=t@(scale*local_eye)+origin
    rows=[]
    for group,material,px,depth in site_points(door):
        direction=np.linalg.solve(P[:,:3],np.r_[px,1.]);direction/=np.linalg.norm(direction)
        limit=(1.5-local_eye[1])/direction[1]*scale
        hit=scene.ray(global_eye,t@direction,limit)
        actual_depth=None if hit is None else float((np.linalg.solve(t,np.array(hit['point_enu_m'])-origin)/scale)[1])
        ok=hit is None if material is None else hit is not None and hit['material']==material and depth[0]<=actual_depth<=depth[1]
        rows.append(dict(feature=group,photo_pixel=px,expected_material=material,expected_depth_at_reference_scale=depth,first_depth_at_reference_scale=actual_depth,actual_hit=hit,passed=bool(ok)))
    return dict(file=path.name,sha256=digest(path),passed=sum(x['passed']for x in rows),total=len(rows),results=rows)

def topology(build,door,lod):
    b=build.Builder({**build.PALETTE,**door.PALETTE});door.add_entrance(b,lod);bad=[];volumes=[]
    for part in b.parts:
        verts=np.array(part['vertices']);tri=np.array(part['triangles']);xyz=verts[tri]
        vol=np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6
        _,inv=np.unique(np.round(verts,8),axis=0,return_inverse=True)
        edges=Counter(tuple(edge)for a in inv[tri]for edge in zip(a,np.roll(a,-1)))
        if vol<=0 or not all(count==1 and edges[(c,a)]==1 for (a,c),count in edges.items()):bad.append(part['label'])
        volumes.append(vol)
    return dict(pieces=len(b.parts),triangles=sum(len(q['triangles']) for q in b.parts),minimum_signed_volume=float(min(volumes)),failures=bad)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('files',type=Path,nargs='+');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--project',type=Path,default=Path.cwd());ap.add_argument('--origin',type=float,nargs=3,default=[0,0,0]);ap.add_argument('--xaxis',type=float,nargs=2,default=[1,0]);ap.add_argument('--yaxis',type=float,nargs=2,default=[0,1]);ap.add_argument('--width',type=float,default=2.8);args=ap.parse_args()
    here=Path(__file__).absolute().parent;sys.path.insert(0,str(here.parent/'source'))
    import west_entrance as door
    import build_model as build
    read=runpy.run_path(str(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
    reg=json.loads((here/'west-entrance-photo-fit.json').read_bytes())
    assert np.allclose(np.array([args.xaxis,args.yaxis])@np.array([args.xaxis,args.yaxis]).T,np.eye(2))
    shells=[topology(build,door,lod)for lod in [False,True]]
    roles=[check_role(p,read,reg,door,np.array(args.origin),args.xaxis,args.yaxis,args.width/2.8)for p in args.files]
    result=dict(source_photo_sha256=reg['sha256'],source_pixels=reg['dimensions_px'],opening_scale_m=args.width,placement=dict(origin=args.origin,xaxis=args.xaxis,yaxis=args.yaxis),editable_checks=shells,roles=roles)
    args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print([(a['pieces'],a['failures']) for a in shells],[(a['file'],a['passed'],a['total'])for a in roles])
    if any(a['failures'] for a in shells) or any(a['passed']!=a['total']for a in roles):raise SystemExit(1)
if __name__=='__main__':main()
