"""Check positions along each rake against the source photograph and serialized GLBs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
Rectify=runpy.run_path(HERE/'fit-front.py')['metric']
Scene=runpy.run_path(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene']
# Each position refers to an intermediate edge on the original file. The three
# vertex controls used by the construction are deliberately outside this list.
MARKS=[(398,339.4),(408,332.1),(418,325.4),(428,318.7),(438,311.6),(448,304.4),
       (458,297.1),(468,290.1),(478,283.6),(503,288.3),(513,297.5),(523,307.0),
       (533,316.3),(543,325.3),(553,335.2),(563,344.2),(573,353.5)]

def verify(photo,models):
    info=json.loads((HERE/'signed-photograph.json').read_bytes())
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==info['sha256']
    rgb=np.asarray(Image.open(photo).convert('RGB'),dtype=float)
    result={}
    for role,path in models.items():
        scene=Scene(path)
        rows=[]
        for u,v in MARKS:
            x,z=Rectify([u,v]);hit=scene.ray([x,-.146,10.2],[0,0,-1],9.)
            assert hit and hit['material']=='Whitened plaster band',hit
            row=round(v);column=int(u)
            patch=rgb[row-2:row+3,column-1:column+2]
            model=float(hit['point_enu_m'][2])
            rows.append(dict(photo_px=[u,v],local_x_m=x,photo_z_m=z,model_z_m=model,error_m=round(model-z,5),
                             five_row_patch_mean_rgb=np.round(patch.mean(axis=1)).astype(int).tolist(),
                             signed_mesh_material=hit['material']))
        err=np.array([r['error_m'] for r in rows]);result[role]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
               samples=rows,rms_m=round(float(np.mean(err**2)**.5),6),max_abs_m=round(float(max(abs(err))),6))
    return dict(photograph_sha256=info['sha256'],samples_per_model=len(MARKS),scale_assumption_m=1.32,
                method='在2005年原照的两条檐斜边上另读17个中间位置，投至正面平面。在每个横坐标对实际文件直接向下求交。局部尺度来自一个窗宽假设，阴影和压缩限制了读点精度。',models=result)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ['photo','raw','full','lod','output']:parser.add_argument(n,type=Path)
    opt=parser.parse_args();data=verify(opt.photo,{k:getattr(opt,k)for k in ['raw','full','lod']})
    opt.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print([(k,r['rms_m'],r['max_abs_m'])for k,r in data['models'].items()])
