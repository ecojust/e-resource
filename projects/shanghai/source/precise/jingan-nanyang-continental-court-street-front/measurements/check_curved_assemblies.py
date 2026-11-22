"""Fire street-normal rays through the full curved layout and check the first hit."""
import gzip,hashlib,json,sys
from pathlib import Path
import numpy as np
project = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
outdir = Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project.parents[2]/'data/audit/nanyang-continental-court-street-front-v1/sashes'
outdir.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(project/'source'))
from continental_window_sashes import add_sash
from continental_street_wall import Bay,SCHEDULE

class Mesh:
    def __init__(self):self.parts=[]
    def add(self,verts,faces,material,label):
        v=np.asarray(verts);faces=np.asarray(faces)
        tri=np.vstack((faces[:,[0,1,2]],faces[:,[0,2,3]]))
        self.parts.append(dict(tri=v[tri],label=label,material=material))

def first_hit(mesh,origin,direction):
    found=[]
    for part in mesh.parts:
        a,b,c=part['tri'].transpose((1,0,2))
        ab,ac=b-a,c-a;p=np.cross(direction,ac)
        den=np.einsum('ij,ij->i',ab,p)
        valid=np.flatnonzero(abs(den)>1e-10)
        f=1/den[valid];t=origin-a[valid];q=np.cross(t,ab[valid])
        u=np.einsum('ij,ij->i',t,p[valid])*f
        v=q@direction*f
        d=np.einsum('ij,ij->i',ac[valid],q)*f
        mask=(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(d>0)
        if mask.any():found.append((d[mask].min(),part['label']))
    return min(found) if found else None

result=[]
trace=[]
for lod in (False,True):
    distances=[];empty=0;checks=0
    for row in SCHEDULE:
        i=row['bay'];bay=Bay(i)
        for fl in row['floors']:
            lo,hi=fl['sill_z'],fl['head_z']
            front=fl['face_depth_m']+fl['sash_recess_m']
            mesh=Mesh()
            for k,(a,b) in enumerate(fl['openings_u_m']):
                args={'strip_index':k} if fl['configuration']=='three-light' else {}
                add_sash(mesh,lod,bay.point,i,fl['floor'],k,a,b,lo,hi,front,**args)
            def ray(u,z):
                eye=np.array(bay.point(u,-1.8,z))
                frontpoint=np.array(bay.point(u,front,z))
                length=np.linalg.norm(frontpoint-eye);normal=(frontpoint-eye)/length
                hit=first_hit(mesh,eye,normal)
                trace.append([lod,i,fl['floor'],round(u,6),round(z,6),np.round(eye,6).tolist(),np.round(normal,7).tolist(),None if hit is None else [round(float(hit[0]),6),hit[1]]])
                return hit,length
            for a,b in fl['openings_u_m']:
                for x,z in ((a+.026,lo+.39),(b-.025,hi-.26),(a+(b-a)*.31,hi-.026)):
                    hit,d=ray(x,z);assert hit and 'fixed jamb and head' in hit[1]
                    distances.append(abs(hit[0]-d));checks+=1
            for first,second in zip(fl['openings_u_m'],fl['openings_u_m'][1:]):
                mid=(first[1]+second[0])/2
                for z in (lo+.29, hi-.39):
                    assert ray(mid,z)[0] is None,(i,fl['floor'],mid,z)
                    empty+=1;checks+=1
            if i==7 and fl['floor']==4:
                a,b=fl['openings_u_m'][0]
                for fraction in (.42,.54):
                    assert ray(a+(b-a)*fraction,lo+.81)[0] is None
                    empty+=1;checks+=1
    assert max(distances)<.02
    result.append(dict(lod='distant' if lod else 'near',world_ray_checks=checks,frame_hits=len(distances),clear_rays=empty,worst_frame_plane_offset_m=round(float(max(distances)),6)))
paths={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [project/'source/continental_street_wall.py',project/'source/continental_window_sashes.py',project/'measurements/street-window-schedule.json']}
(outdir/'world-sash-rays.json.gz').write_bytes(gzip.compress(json.dumps(trace,separators=(',',':')).encode(),mtime=0))
assert len(trace)==sum(r['world_ray_checks'] for r in result)
(outdir/'curved-bay-checks.json').write_text(json.dumps(dict(inputs=paths,trace_fields=['distant','bay','storey','u_m','z_m','origin_east_north_up','unit_direction','first_hit_radius_m_and_group'],results=result),indent=2)+'\n')
print(result)
