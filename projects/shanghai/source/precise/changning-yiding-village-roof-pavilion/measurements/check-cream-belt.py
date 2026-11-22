"""Compare unfitted image columns of the pale cornice with the exported projecting upper edge."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
project=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1').is_dir())
triangles=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
camera=json.loads((HERE/'roof-room-camera.json').read_bytes())
source=HERE/'antigng-roof-room.jpg'
im=np.asarray(Image.open(source),float)
P=np.array(camera['world_to_crop'])
def observations():
    luminance=im@np.array([.25,.59,.16])
    result=[]
    for u in range(198,826,29):
        # The broad pale masonry divider begins below the darker upper brick course.
        top=267+(u-153)*(132-267)/(863-153)
        window=np.arange(round(top+11),round(top+30))
        strip=luminance[:,u-3:u+4].mean(axis=1)
        change=np.mean([strip[window+k]for k in [1,2,3]],axis=0)-np.mean([strip[window-k]for k in [1,2,3]],axis=0)
        i=int(change.argmax())
        if change[i]>=20:result.append(dict(u=u,observed_v=int(window[i]),edge_contrast=float(change[i])))
    return result
def check(path,rows):
    tri,mi,names,asset=triangles(path);subset=(mi==names.index('Pale projecting ledge'))&(tri[:,:,2].min(axis=1)>1.86)&(tri[:,:,1].max(axis=1)<0)
    f=tri[subset];proj=np.concatenate([f,np.ones(f.shape[:2]+(1,))],axis=-1)@P.T
    xy=proj[:,:,:2]/proj[:,:,2,None];a=xy.reshape(-1,2);b=np.roll(xy,-1,axis=1).reshape(-1,2);tests=[]
    for r in rows:
        x=r['u'];mask=(np.minimum(a[:,0],b[:,0])<=x)&(np.maximum(a[:,0],b[:,0])>x)
        frac=(x-a[mask,0])/(b[mask,0]-a[mask,0])
        v=float((a[mask,1]+(b[mask,1]-a[mask,1])*frac).min())
        tests.append(dict(**r,predicted_v=v,residual_px=v-r['observed_v']))
    err=np.array([v['residual_px']for v in tests])
    return dict(sha256=asset['sha256'],inspected_ledge_triangles=len(f),samples=tests,rms_px=float(np.mean(err**2)**.5),max_abs_px=float(np.abs(err).max()))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['raw','full','lod','output']:ap.add_argument(n,type=Path)
    args=ap.parse_args();obs=observations();assert len(obs)>=16
    checks={r:check(getattr(args,r),obs)for r in ['raw','full','lod']}
    data=dict(original_sha256=camera['photo_sha256'],crop_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
              accepted_samples=len(obs),photo_columns_used_for_camera_fit=False,edge='upper edge of pale projecting divider on the front',
              models=checks)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(len(obs),[(k,r['rms_px'],r['max_abs_px'])for k,r in checks.items()])
