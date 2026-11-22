"""Independently intersect the exported lower moulding edge with reserved photograph columns."""
import argparse,hashlib,json,sys,runpy
from pathlib import Path
import numpy as np
here=Path(__file__).absolute().parent;sys.path.insert(0,str(here.parent/'source'))
from geometry_reference import project,DATA
src=runpy.run_path(here/'measure-slab-and-rack.py')
project_dir=here.parents[3]
read=runpy.run_path(project_dir/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
def compare(mesh,samples):
    tri,mi,names,meta=read(mesh);slab=tri[mi==names.index('Pale concrete moulding')]
    normal=np.cross(slab[:,1]-slab[:,0],slab[:,2]-slab[:,0])
    face=slab[(abs(normal[:,1])>abs(normal[:,0])*2)&(abs(normal[:,1])>abs(normal[:,2])*2)]
    edges=[]
    for t in face:
        base=t[abs(t[:,2]+.37)<.00001]
        if len(base)==2 and max(base[:,1])<.35:
            edges.append(project(base))
    a,b=np.array(edges).transpose(1,0,2)
    obs=[]
    for s in samples:
        x=s['u'];inside=(np.minimum(a[:,0],b[:,0])<=x)&(x<np.maximum(a[:,0],b[:,0]))
        u=a[inside];v=b[inside];cross=u[:,1]+(x-u[:,0])*(v[:,1]-u[:,1])/(v[:,0]-u[:,0])
        assert len(cross)==1,(x,cross)
        error=float(cross[0]-s['v'])
        obs.append(dict(**s,projected_working_v=float(cross[0]),residual_original_y_px=error*2988/597))
    errors=np.array([r['residual_original_y_px']for r in obs])
    return dict(sha256=meta['sha256'],observations=obs,selected_mesh_edges=len(edges),
         rms_original_y_px=float(np.mean(errors**2)**.5),max_absolute_original_y_px=float(max(abs(errors))))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['photograph','raw','full','lod','output']:ap.add_argument(n,type=Path)
    a=ap.parse_args();im=src['load'](a.photograph);trained=src['TRAIN'];samples=[]
    for u in range(408,758,4):
        if min(abs(u-v)for v in trained)<5:continue
        r=src['lower_bead'](im,u)
        if r['contrast']>=25:samples.append(r)
    assert len(samples)>=45
    out=dict(original_source_sha256=DATA['photo_sha256'],excluded_training_columns=trained,
             held_out_columns=len(samples),minimum_distance_from_training_px=5,minimum_local_contrast=25,
             models={n:compare(getattr(a,n),samples)for n in ['raw','full','lod']})
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(len(samples),[(n,r['rms_original_y_px'],r['max_absolute_original_y_px'])for n,r in out['models'].items()])
