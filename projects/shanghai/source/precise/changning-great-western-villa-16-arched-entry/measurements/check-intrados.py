"""Compare independently sampled photograph columns with the front brick arch of each serialized export."""
from pathlib import Path
import argparse,hashlib,json,runpy,sys
import numpy as np
HERE=Path(__file__).absolute().parent;sys.path.insert(0,str(HERE.parent/'source'))
from registration import C,projected
sample=runpy.run_path(HERE/'measure-vault.py')
read=runpy.run_path(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
def edges(path):
    tri,mi,mats,_=read(path);names=['Salmon facing brick','Dusty red brick','Weathered orange brick','Dark russet brick']
    tri=tri[np.isin(mi,[mats.index(name)for name in names])]
    Y=C['outer_front_y_m'];a=json.loads((HERE/'vault-profile.json').read_bytes());cx,cz,rx,rz,tilt=a['conic_parameters']
    xz=tri[:,:,[0,2]];dx=(xz[:,:,0]-cx)/rx;dz=(xz[:,:,1]-cz-dx*tilt)/rz
    rad=dx*dx+dz*dz
    on=(abs(rad-1)<.000035)&(abs(tri[:,:,1]-Y+.001)<.00013)|(abs(rad-1)<.000035)&(abs(tri[:,:,1]-Y+.015)<.00013)
    pairs=[];seen=set()
    for t,f in zip(tri,on):
        if f.sum()!=2:continue
        v=t[f];uv=projected(v)
        if np.max(v[:,2])<.22 or abs(uv[0,0]-uv[1,0])<.01:continue
        key=tuple(sorted(map(tuple,v)))
        if key not in seen:seen.add(key);pairs.append(uv)
    return pairs
def check(path,observations):
    e=edges(path);points=[]
    for o in observations:
        x=o['x'];ys=[p[1]+(x-p[0])*(q[1]-p[1])/(q[0]-p[0])for p,q in e if min(p[0],q[0])<=x<=max(p[0],q[0])]
        if not ys:continue # Mortar between separate physical face bricks.
        y=min(ys);points.append(dict(x=x,observed=o['v'],serialized=y,error_original_px=(y-o['v'])*5.2))
    assert len(points)>=55
    er=np.array([j['error_original_px']for j in points])
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),compared_columns=len(points),rms_original_px=float(np.sqrt(np.mean(er**2))),median_absolute_original_px=float(np.median(abs(er))),
                maximum_absolute_original_px=max(abs(er)),evidence=points)
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    for k in ['photo','raw','full','lod','output']:ap.add_argument(k,type=Path)
    a=ap.parse_args();photo=sample['source'](a.photo);p=json.loads((HERE/'vault-profile.json').read_bytes())
    train=sample['TRAIN'];held=[c for x in range(235,610,2)if min(abs(x-i)for i in train)>=4 and (c:=sample['edge'](photo,x))]
    r={k:check(getattr(a,k),held)for k in ['raw','full','lod']}
    a.output.write_text(json.dumps(dict(photo_sha256=p['photo_sha256'],colour_edge_columns=len(held),foreground_exclusions=[[155,209],[220,231],[549,576]],held_out_odd_columns=True,excluded_training_columns=train,models=r),ensure_ascii=False,indent=2)+'\n')
    print(len(held),[(k,s['compared_columns'],round(s['rms_original_px'],3),round(s['maximum_absolute_original_px'],2))for k,s in r.items()])
