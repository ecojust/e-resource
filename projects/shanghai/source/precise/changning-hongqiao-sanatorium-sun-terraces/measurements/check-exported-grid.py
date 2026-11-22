"""Reproject real corners shared across grout lines against floor observations excluded from camera fitting."""
from pathlib import Path
import hashlib,json,runpy,sys
import numpy as np
here=Path(__file__).resolve().parent;project=here.parents[3];load=lambda n:json.loads((here/n).read_bytes());reg=load('terrace-camera.json');floor=load('terrace-frame.json');obs=load('terrace-checker-grid.json')['held_out_rows']['points'];R=np.array(reg['camera_rows_right_down_forward']);eye=np.array(reg['eye']);reader=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
def check(path):
    tri,idx,names,_=reader(path);sel=tri[idx==names.index('Jointed two-tone terrace paving')];points=np.unique(sel.reshape(-1,3),axis=0);top=points[abs(points[:,2]-floor['floor_to_roof_z_m'][3]-.009)<1e-4];rows=[];p=floor['estimated_tile_pitch_m']
    for i,j,x,y in obs:
        nominal=(np.array([i,j])-[floor['grid_i_at_post_row'],floor['longitudinal_bounds_grid_j'][0]])*p
        corners=top[np.linalg.norm(top[:,:2]-nominal,axis=1)<.005];assert len(corners)==4
        c=corners.mean(axis=0);q=R@(c-eye);uv=q[:2]/q[2]*reg['focal_px']+reg['principal_xy_working'];r=np.asarray([x,y])-uv
        rows.append(dict(grid=[i,j],photo_working=[x,y],measured_model_joint=c.tolist(),projected_joint=uv.tolist(),error_px_original=float(np.linalg.norm(r*[945/660,685/478]))))
    err=np.array([r['error_px_original']for r in rows]);assert len(rows)==20 and np.sqrt(np.mean(err**2))<2.5
    f=Path(path);return dict(sha256=hashlib.sha256(f.read_bytes()).hexdigest(),joints=len(rows),original_rms_px=float(np.sqrt(np.mean(err**2))),original_max_px=float(err.max()),model_intersections=rows)
if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod']if len(args)==4 else['model'];assert len(args)==len(roles)+1
    result={k:check(f)for k,f in zip(roles,args)};args[-1].write_text(json.dumps(result,indent=2)+'\n');print([(k,v['joints'],v['original_rms_px'])for k,v in result.items()])
