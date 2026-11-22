"""Compare the actual roof rim triangles with unused source-image columns on both eaves."""
import argparse,hashlib,json,runpy,sys
from pathlib import Path
import numpy as np
from PIL import Image
here=Path(__file__).absolute().parent
project=next(p for p in here.parents if (p/'data/audit/postal-office-v1').is_dir())
sys.path.insert(0,str(here.parent/'source'));from projection import photo,DATA
get_mesh=runpy.run_path(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['load_triangles']
trained=[187,207,230,249,269,282,289,295,325,357,381,400,420,429]
def read_rim(source):
    assert hashlib.sha256(source.read_bytes()).hexdigest()==DATA['source_sha256']
    im=np.asarray(Image.open(source).convert('L'),float)
    rows=[]
    for u in range(190,420,3):
        if min(abs(u-x)for x in trained)<3:continue
        # Two broad source-only search regions exclude cables well above the roof.
        coarse=np.interp(u,[187,289,345,395,420],[258,82,123,155,162]);start,end=int(coarse-11),int(coarse+12)
        candidates=[]
        for v in range(start,end):
            if im[v,u]<190 and im[v:v+6,u].mean()<178 and im[v-4:v,u].mean()>195:
                candidates.append(v)
        if candidates:rows.append(dict(u=u,v=candidates[0],local_luminance_change=float(im[candidates[0]-4:candidates[0],u].mean()-im[candidates[0]:candidates[0]+6,u].mean())))
    return rows
def compare(path,rows):
    tri,mi,names,meta=get_mesh(path);t=tri[mi==names.index('Weathered grey roof rim')]
    uv=photo(t.reshape(-1,3)).reshape(-1,3,2);a=uv.reshape(-1,2);b=np.roll(uv,-1,axis=1).reshape(-1,2)
    vals=[]
    for row in rows:
        u=row['u'];mask=(np.minimum(a[:,0],b[:,0])<=u)&(u<np.maximum(a[:,0],b[:,0]))
        slab=a[mask];delta=b[mask]-slab;v=float(np.min(slab[:,1]+(u-slab[:,0])/delta[:,0]*delta[:,1]))
        vals.append(dict(**row,projected_v=v,error_px=v-row['v']))
    residual=np.array([v['error_px']for v in vals])
    return dict(sha256=meta['sha256'],roof_rim_triangles=len(t),rms_original_px=float(np.mean(residual**2)**.5),
                max_absolute_px=float(np.max(np.abs(residual))),samples=vals)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('photograph','raw','full','lod','output'):parser.add_argument(n,type=Path)
    args=parser.parse_args();rows=read_rim(args.photograph);assert len(rows)>38
    obj=dict(original_photo_sha256=DATA['source_sha256'],source_size_px=[608,686],excluded_training_columns=trained,
             minimum_distance_from_training_column_px=3,number_of_held_out_columns=len(rows),
             models={k:compare(getattr(args,k),rows)for k in ('raw','full','lod')})
    args.output.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(len(rows),[(k,r['rms_original_px'],r['max_absolute_px'])for k,r in obj['models'].items()])
