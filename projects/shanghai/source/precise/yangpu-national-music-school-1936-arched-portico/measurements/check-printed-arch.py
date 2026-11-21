"""Measure the independent dark-to-light edge of the arch in the 1936 printed plate."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
metric=runpy.run_path(HERE/'fit-portal.py')['metric']
Scene=runpy.run_path(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene']
LEFT=929;TOP=610
def measure(photo,models):
    crop=Image.open(photo).convert('L')
    assert crop.size==(480,463)
    ink=gaussian_filter(np.asarray(crop,dtype=float),1.3)
    points=[]
    # Offset from the three construction anchors. The photocopied ink edge
    # is read by interpolation at the first sustained dark band in each column.
    for x in [156,158,160,162,164,166,168,170,172,174,176,178,180,182,184,190,192,194,196,198,200,202,204,206,208,210,212,214,216,218]:
        yy=next(i for i in range(202,257)if ink[i,x]<=66<ink[i-1,x]and np.max(ink[i:i+3,x])<70)
        y=yy-1+(66-ink[yy-1,x])/(ink[yy,x]-ink[yy-1,x])
        points.append(dict(photo_px=[LEFT+x,round(TOP+y,3)],local_px=[x,round(y,3)],plane_xz_m=metric([x,y])))
    results={}
    for key,path in models.items():
        scene=Scene(path);rows=[]
        for point in points:
            x,z=point['plane_xz_m'];hit=scene.ray([x,.018,3.62],[0,0,1],2.9)
            assert hit and hit['material']=='Music School archival plaster',hit
            rows.append(dict(**point,serialized_height_m=hit['point_enu_m'][2],difference_m=round(hit['point_enu_m'][2]-z,5)))
        delta=np.array([v['difference_m']for v in rows]);results[key]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=rows,
                     rms_m=round(float(np.mean(delta**2)**.5),6),max_abs_m=round(float(max(abs(delta))),6))
    return dict(crop_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),samples=len(points),ink_threshold_8bit=66,blur_sigma_px=1.3,
       methodology='在1936年印本第17页原图的30个列位置，从浅色券面向门洞寻找墨色跃变，再由三个实际模型内的垂直射线测量券内壁。券口净宽假设2.64米，结果表示同一照片中的相对符合程度。',models=results)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ['photo','raw','full','lod','output']:p.add_argument(k,type=Path)
    opt=p.parse_args();r=measure(opt.photo,{k:getattr(opt,k)for k in ['raw','full','lod']})
    opt.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print([(k,v['rms_m'],v['max_abs_m'])for k,v in r['models'].items()])
