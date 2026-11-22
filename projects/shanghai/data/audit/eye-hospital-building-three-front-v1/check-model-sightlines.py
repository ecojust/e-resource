"""Test first visible triangle at photographed courtyard bay, balcony, pilasters and gable details in the shipped near and distant meshes."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np
from trimesh.triangles import closest_point

from measured_targets import TARGETS

def first_hit(eye,point,mesh):
    direction=point-eye;length=np.linalg.norm(direction);direction=direction/length
    a,e1,e2,mi=mesh
    cross=np.cross(direction,e2);det=(e1*cross).sum(1)
    front=det>1e-10;ts=eye-a
    u=(ts*cross).sum(1);front&=(u>=-1e-9)&(u<=det+1e-9)
    cross2=np.cross(ts,e1);v=cross2@direction
    front&=(v>=-1e-9)&(u+v<=det+1e-9)
    distance=(e2*cross2).sum(1)/np.where(front,det,1.)
    front&=(distance>1e-5)&(distance<length+.05)
    if not np.any(front):return None
    choices=np.flatnonzero(front);idx=choices[distance[front].argmin()]
    return idx,abs(distance[idx]-length)

def main():
    c=argparse.ArgumentParser(description=__doc__)
    for n in ('contract','cameras','decoded','out'):c.add_argument('--'+n,required=True,type=Path)
    args=c.parse_args();contract=json.loads(args.contract.read_bytes());cameras=json.loads(args.cameras.read_bytes())
    angle=math.radians(contract['heading']);co,si=math.cos(angle),math.sin(angle)
    variants=[]
    for item in json.loads(args.decoded.read_bytes()):
        file=Path(item['actual_read_path'])
        assert hashlib.sha256(file.read_bytes()).hexdigest()==item['sha256']==contract['model_geometry_sha256'][item['variant']]
        mesh_g=np.fromfile(item['triangle_file'],np.float64).reshape(-1,3,3)
        # GLTF [x,z,-y] -> model [x,y,z], preserving the original winding.
        triangles=mesh_g[:,:,[0,2,1]]*[1,-1,1]
        materials=np.fromfile(item['triangle_material_ids_file'],np.uint16);names=item['material_names']
        cent=triangles.mean(1);a=triangles[:,0];mesh=a,triangles[:,1]-a,triangles[:,2]-a,materials
        views=[]
        for cam in cameras['views']:
            east,north,z=cam['camera_enu'];eye=np.array([east*co-north*si,east*si+north*co,z]);rows=[]
            for name,target,rad,mats in TARGETS:
                target=np.asarray(target);rad=np.asarray(rad)
                mask=np.isin(materials,[names.index(m)for m in mats])
                mask&=np.all(triangles.max(1)>=target-rad,axis=1)&np.all(triangles.min(1)<=target+rad,axis=1)
                ids=np.flatnonzero(mask);assert len(ids),(name,mats)
                surf=closest_point(triangles[ids],np.repeat(target[None,:],len(ids),axis=0))
                points=.94*surf+.06*cent[ids];quality=np.linalg.norm((points-target)/rad,axis=1)
                options=[]
                for j in np.argsort(quality)[:55]:
                    for point in [points[j],cent[ids[j]]]:
                        if np.any(np.abs(point-target)>rad*1.04):continue
                        options.append(point)
                result=None
                for attempt,point in enumerate(options):
                    r=first_hit(eye,point,mesh)
                    if r:
                        ix,miss=r
                        if miss<.011 and names[materials[ix]]in mats:
                            result=dict(triangle=int(ix),first_material=names[materials[ix]],physical_endpoint_m=point.round(5).tolist(),first_hit_distance_error_m=round(float(miss),7),attempt=attempt+1);break
                rows.append(dict(feature=name,visible=result is not None,hit=result))
            views.append(dict(view=cam['view'],local_camera_eye=eye.tolist(),targets=rows,clear=sum(r['visible']for r in rows)))
        variants.append(dict(role=item['variant'],file_sha256=item['sha256'],triangles=len(triangles),views=views))
    out=dict(method='Nearest front-facing original triangle along each physical camera ray. Every accepted sample is at most 11 mm behind the first hit and uses a listed photographed material.',contract_sha256=hashlib.sha256(args.contract.read_bytes()).hexdigest(),camera_receipt_sha256=hashlib.sha256(args.cameras.read_bytes()).hexdigest(),geometry=variants)
    args.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    for v in variants:
        print(v['role'],[(u['view'],u['clear'],[h['feature']for h in u['targets']if not h['visible']])for u in v['views']],flush=True)
if __name__=='__main__': main()
