"""Render and ray-check the gallery through its published photographs."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
from fit_gallery import GalleryPlane
RAY=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
MEASURE=PROJECT/'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(MEASURE))
ENGINE=runpy.run_path(str(MEASURE/'render_registered_entrance.py'))
CHECKS={
    'scalloped warm render':[(86,389),(284,400),(315,537),(520,517),(677,524),(815,475),(857,452)],
    'fired barrel tile':[(166,264),(317,265),(445,270),(593,283),(721,298),(805,312)],
    'ochre red timber':[(451,348),(535,354),(609,356),(680,362),(747,371),(810,381),(871,380),(406,376),(579,387)],
    'charcoal rainwater metal':[(271,403),(884,430)],
    'smoked window glass':[(78,324),(310,474),(844,482)],
    'through opening':[(180,511)],
}
def test_mesh(path,projection,types):
    scene=runpy.run_path(str(RAY))['SerialScene'](path)
    inv=np.linalg.inv(projection[:,:3]);eye=-inv@projection[:,3]
    rows=[]
    for expected,picks in types.items():
        for uv in picks:
            d=inv@[*uv,1];d/=np.linalg.norm(d);hit=scene.ray(eye,d,300)
            m=hit['material'] if hit else None
            valid=m is None if expected=='through opening' else (m is not None and expected in m)
            rows.append(dict(uv=uv,from_photo=expected,first_hit=m,matched=bool(valid)))
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),direct=sum(r['matched'] for r in rows),count=len(rows),points=rows)
def render(path,destination,matrix,crop):
    lighting,raster=ENGINE['ENGINE'],ENGINE['RASTER']
    model=raster.read_glb(path)
    with tempfile.TemporaryDirectory(dir=destination.parent)as temp:
        lib=lighting['make_library'](Path(temp));painter=lighting['MaterialPass'](lib,model[1],model[2])
        views,ranges,depth=lighting['sky_maps'](model[0],lib,raster)
        lib.set_sky(lighting['SAMPLES'],lighting['DEPTH_RESOLUTION'],raster.ptr(views),raster.ptr(ranges),raster.ptr(depth))
        projection=matrix.copy();projection[:2]+=.5*projection[2]
        im,_,stats=ENGINE['sample_view'](path,model,painter,lib,projection,crop,900,np.array([-.38,-.70,.61],dtype='float32'),None,2)
        im.save(destination,quality=94,subsampling=0)
        return dict(sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),size=list(im.size),foreground=stats['zbuffer_foreground_pixels'],materials=stats['materials_visible_samples'])
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path);cli.add_argument('--render',action='store_true');a=cli.parse_args()
    a.out.mkdir(exist_ok=True,parents=True);p=GalleryPlane().matrix;j=test_mesh(a.mesh,p,CHECKS)
    if a.render:j['render']=render(a.mesh,a.out/'arcade-model.jpg',p,(12,188,925,604))
    (a.out/(a.mesh.stem+'-points.json')).write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
    print(j['direct'],j['count'])
