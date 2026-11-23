"""Render the two registered courtyard views with baked ambient visibility and the model's material maps."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from wing_frame import Camera

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[1]/'xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(SHARED))
engine=runpy.run_path(str(SHARED/'render_registered_entrance.py'))
lighting,raster=engine['ENGINE'],engine['RASTER']
VIEWS={'album':('album-1937-model.jpg','1937年《Eves》相册的视角',(286,470,670,656)),
       'design':('restoration-proposal-model.jpg','2014年修缮设计透视的视角',(58,103,403,252))}

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def render(model_path,out,width,grid):
    out.mkdir(exist_ok=True,parents=True)
    model=raster.read_glb(model_path)
    result={'mesh_sha256':digest(model_path),'camera_sha256':digest(HERE/'wing-cameras.json'),
            'source_pixels_embedded':False,'sample_grid':grid,'views':{}}
    panels=[]
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        lib=lighting['make_library'](Path(tmp));painter=lighting['MaterialPass'](lib,model[1],model[2])
        views,ranges,depth=lighting['sky_maps'](model[0],lib,raster)
        lib.set_sky(lighting['SAMPLES'],lighting['DEPTH_RESOLUTION'],raster.ptr(views),raster.ptr(ranges),raster.ptr(depth))
        for key,(name,label,crop) in VIEWS.items():
            cam=Camera(key);w,h=(573,323) if key=="design" else (1500,1222)
            projection=cam.K@cam.R@np.column_stack([np.eye(3),-cam.C]);projection[:2]+=.5*projection[2]
            pic,_,stats=engine['sample_view'](model_path,model,painter,lib,projection,crop,width,
                         np.array([-.32,-.70,.65],dtype='float32'),None,grid)
            pic.save(out/name,quality=94,subsampling=0)
            result['views'][key]={'file':name,'sha256':digest(out/name),'source_dimensions':[w,h],'source_crop':crop,
                                 'output_dimensions':list(pic.size),'foreground':stats['zbuffer_foreground_pixels'],
                                 'visible_materials':stats['materials_visible_samples']}
            tile=pic.copy();tile.thumbnail((450,406));panels.append((label,tile))
    content_h=max(im.height for _,im in panels)
    sh=Image.new('RGB',(462*len(panels),content_h+49),'#e6e3db');d=ImageDraw.Draw(sh)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',16,index=2)
    for i,(label,im) in enumerate(panels):
        sh.paste(im,(i*462+(462-im.width)//2,6+(content_h-im.height)//2))
        d.text((i*462+10,content_h+13),label,font=font,fill='#282724')
    f=out/'two-dated-views.jpg';sh.save(f,quality=94,subsampling=0)
    result['sheet']={'file':f.name,'sha256':digest(f)}
    (out/'registered-renders.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--width',type=int,default=770);p.add_argument('--grid',type=int,default=2,choices=(1,2,3))
    a=p.parse_args();render(a.model,a.output,a.width,a.grid)
