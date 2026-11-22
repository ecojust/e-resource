"""Check untrained photograph rows against the outer edge of the serialized green gable."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from registration import projected
method=runpy.run_path(HERE/'measure-green-gable.py')
load=runpy.run_path(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
def evaluate(mesh,obs,H):
    tri,mat,ids,_=load(mesh);tri=tri[mat==ids.index('Weathered green roughcast')]
    edges=[]
    for t in tri:
        # One return triangle across the thickness has two vertices on the street skin.
        flags=abs(t[:,1]+.48)<.001
        if sum(flags)!=2:continue
        side=t[flags]
        if min(side[:,0])<1.4:continue
        uv=method['transform'](projected(side),np.linalg.inv(H))
        if abs(uv[1,1]-uv[0,1])>.01:edges.append(uv)
    assert len(edges)>12
    measured=[]
    for row in obs:
        y=row['v']
        xs=[a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1])for a,b in edges if min(a[1],b[1])<=y<max(a[1],b[1])]
        assert xs,y
        pred=max(xs);measured.append(dict(v=y,observed_u=row['u'],mesh_u=pred,error_original_px=float((pred-row['u'])*780/639)))
    err=np.array([e['error_original_px']for e in measured])
    return dict(sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),rms_original_x_px=float(np.sqrt(np.mean(err**2))),max_original_x_px=float(max(abs(err))),held_out=measured)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('district','raw','full','lod','output'):ap.add_argument(k,type=Path)
    a=ap.parse_args();img=method['read'](a.district)
    profile=json.loads((HERE/'green-gable-profile.json').read_bytes());training=[v['v']for v in profile['training']]
    held=[m for y in range(109,342,2)if min(abs(y-q)for q in training)>=5 and (m:=method['measure'](img,y))]
    assert len(held)>=50
    H=np.array(profile['district_to_street_gable_only'])
    rows={k:evaluate(getattr(a,k),held,H)for k in ('raw','full','lod')}
    a.output.write_text(json.dumps(dict(district_sha256=profile['district_sha256'],held_out_rows=len(held),excluded_training_rows=training,local_to_original_x=780/639,models=rows),ensure_ascii=False,indent=2)+'\n')
    print(len(held),[(k,v['rms_original_x_px'],v['max_original_x_px'])for k,v in rows.items()]);assert all(v['rms_original_x_px']<2.0 and v['max_original_x_px']<6 for v in rows.values())
