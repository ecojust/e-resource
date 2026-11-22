"""Compare exported curved coping with held-out high-contrast sky edges in the original photograph."""
import argparse,hashlib,json,runpy
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
project=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1').is_dir())
get_mesh=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
camera=json.loads((HERE/'curved-corner-camera.json').read_bytes())
source=HERE/'antigng-rounded-street-front.jpg';assert hashlib.sha256(source.read_bytes()).hexdigest()==camera['crop_sha256']
K=np.array(camera['world_to_working_image']);trained=[v['u'] for v in camera['trained_coping_samples']]
image=Image.open(source).crop((0,0,2970,2632)).resize((900,798),Image.Resampling.LANCZOS)
lum=np.asarray(image)@np.array([.299,.587,.114])
def read_edges():
    result=[]
    for u in range(137,617,7):
        if min(abs(u-x)for x in trained)<6:continue
        part=lum[6:142,u-1:u+2].mean(axis=1)
        contrast=part[:-2]-part[2:]
        i=int(contrast.argmax())
        if contrast[i]>=70:
            result.append(dict(u=u,source_v=i+7,contrast=float(contrast[i])))
    return result
def compare(path,rows):
    tr,mi,names,info=get_mesh(path);t=tr[mi==names.index('Weathered dark cap')]
    p=np.concatenate([t,np.ones(t.shape[:2]+(1,))],axis=2)@K.T
    uv=p[:,:,:2]/p[:,:,2,None];a=uv.reshape(-1,2);b=np.roll(uv,-1,axis=1).reshape(-1,2)
    records=[]
    for row in rows:
        u=row['u'];keep=(np.minimum(a[:,0],b[:,0])<=u)&(u<np.maximum(a[:,0],b[:,0]))
        frac=(u-a[keep,0])/(b[keep,0]-a[keep,0]);v=float((a[keep,1]+(b[keep,1]-a[keep,1])*frac).min())
        records.append(dict(**row,projected_v=v,error_working_px=v-row['source_v']))
    err=np.array([v['error_working_px']for v in records])
    return dict(sha256=info['sha256'],rim_triangles=len(t),samples=records,rms_working_px=float(np.mean(err**2)**.5),
                max_abs_working_px=float(np.abs(err).max()),rms_original_photo_px=float(np.mean(err**2)**.5*2632/798))
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['raw','full','lod','output']:ap.add_argument(key,type=Path)
    args=ap.parse_args();rows=read_edges();assert len(rows)>=42
    models={r:compare(getattr(args,r),rows)for r in ['raw','full','lod']}
    obj=dict(original_photo_sha256=camera['original_photo_sha256'],crop_sha256=camera['crop_sha256'],source_working_size=[900,798],
             scaled_original_region=[2970,2632],training_columns_excluded=trained,training_exclusion_radius_px=6,
             independent_columns=len(rows),models=models)
    args.output.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),[(k,x['rms_working_px'],x['rms_original_photo_px'],x['max_abs_working_px'])for k,x in models.items()])
