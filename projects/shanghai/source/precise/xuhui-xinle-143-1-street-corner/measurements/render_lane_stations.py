"""Render the actual corner mesh at either registered street station without reading source photograph pixels."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[1]/'xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(SHARED))
engine=runpy.run_path(str(SHARED/'render_registered_entrance.py'))
lighting,raster=engine['ENGINE'],engine['RASTER']
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()
def render(mesh,out,width,grid,stations=('2018','1512-6')):
    out.mkdir(exist_ok=True,parents=True)
    path=HERE/'street-cameras.json';cameras=json.loads(path.read_bytes())['cameras']
    model=raster.read_glb(mesh)
    info={'mesh_sha256':digest(mesh),'camera_sha256':digest(path),'photos_embedded':False,'views':{}}
    panels=[]
    with tempfile.TemporaryDirectory(dir=out) as tmp:
        lib=lighting['make_library'](Path(tmp));painter=lighting['MaterialPass'](lib,model[1],model[2])
        views,ranges,depth=lighting['sky_maps'](model[0],lib,raster)
        lib.set_sky(lighting['SAMPLES'],lighting['DEPTH_RESOLUTION'],raster.ptr(views),raster.ptr(ranges),raster.ptr(depth))
        for key in stations:
            cam=cameras[key];w,h=cam['dimensions']
            projection=np.array(cam['P'],dtype=float)
            projection[:2]+=.5*projection[2]
            pic,flat,stats=engine['sample_view'](mesh,model,painter,lib,projection,(0,0,w,h),width,
                                 np.array([0.,-.8,.6],dtype='float32'),None,grid)
            label={'2018':'2018','1512-6':'2015'}.get(key,key)
            name='street-'+label+'-model.jpg'
            pic.save(out/name,quality=94,subsampling=0,optimize=True)
            info['views'][key]={'file':name,'sha256':digest(out/name),'source_dimensions':[w,h],
                                'dimensions':list(pic.size),'foreground':stats['zbuffer_foreground_pixels'],
                                'visible_materials':stats['materials_visible_samples']}
            tile=pic.copy();tile.thumbnail((500,315));panels.append((label,tile))
    sheet=Image.new('RGB',(510*len(panels),346),'#e6e1d8');d=ImageDraw.Draw(sheet)
    for i,(label,im) in enumerate(panels):
        sheet.paste(im,(i*510+(510-im.width)//2,4+(315-im.height)//2))
        d.text((i*510+12,324),'Registered model view / '+label,fill='#282724')
    f=out/'street-stations-model.jpg';sheet.save(f,quality=94,subsampling=0)
    info['sheet']={'file':f.name,'sha256':digest(f)}
    (out/'registered-renders.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    return info
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--width',default=900,type=int);p.add_argument('--grid',choices=[1,2,3],default=2,type=int)
    p.add_argument('--stations',nargs='+',default=['2018','1512-6']);a=p.parse_args();r=render(a.mesh,a.output,a.width,a.grid,a.stations)
    print(r['mesh_sha256'],r['sheet']['sha256'])
