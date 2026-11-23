"""Generate model-only street photographs from the recorded camera matrices and editable GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).absolute().parent
PRECISE=HERE.parents[1]
REFERENCE=PRECISE/'xuhui-huaihai-1230-rear-courtyard-entrance/measurements'
sys.path.insert(0,str(REFERENCE))
engine=runpy.run_path(str(REFERENCE/'render_registered_entrance.py'))
E,R=engine['ENGINE'],engine['RASTER']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def render(src,out,width,grid):
    out.mkdir(exist_ok=True,parents=True)
    records=json.loads((HERE/'street-cameras.json').read_bytes())['cameras']
    extra=HERE/'gate-station-cameras.json'
    if extra.is_file():
        records.update(json.loads(extra.read_bytes())['cameras'])
    model=R.read_glb(src)
    data={'mesh':sha(src),'camera_source':sha(HERE/'street-cameras.json'),'views':{},'materials':'Embedded GLB colors, UV textures, tangent normal maps and geometry occlusion from 18 sky directions. Model-only photographs. Winter views use diffuse sky; the 2017 model view uses diffuse sky for direct comparison.'}
    panels=[]
    with tempfile.TemporaryDirectory(dir=out)as temp:
        lib=E['make_library'](Path(temp))
        painter=E['MaterialPass'](lib, model[1], model[2])
        views,ds,depth=E['sky_maps'](model[0],lib,R)
        lib.set_sky(E['SAMPLES'],E['DEPTH_RESOLUTION'],R.ptr(views),R.ptr(ds),R.ptr(depth))
        for key,cam in records.items():
            if key not in ['2017','2015-12-front','2021-01-front','2015-12-east','2021-01-east','1512g','2101g']:
                continue
            cw,ch=cam.get('size',cam.get('dimensions',[1320,858]))
            projection=np.array(cam['P'],dtype=float)
            projection[:2]+=.5*projection[2]
            sun=np.array([0.,-.8,.6],dtype='float32')
            pic,flat,stats=engine['sample_view'](src,model,painter,lib,projection,(0,0,cw,ch),round(width*cw/max(cw,ch)),sun,None,grid)
            file=out/(key+'-model.jpg')
            pic.save(file,quality=94,subsampling=0,optimize=True)
            data['views'][key]=dict(file=file.name,sha256=sha(file),intrinsic_canvas=[cw,ch],size=list(pic.size),foreground=stats['zbuffer_foreground_pixels'],materials=stats['materials_visible_samples'])
            tile=pic.copy();tile.thumbnail((330,200));panels.append((key,tile))
    sheet=Image.new('RGB',(1002,228*((len(panels)+2)//3)),'#e4dfd6');d=ImageDraw.Draw(sheet)
    for i,(k,img) in enumerate(panels):
        x,y=(i%3)*334,(i//3)*228;sheet.paste(img,(x+2,y+1));d.text((x+8,y+204),k,fill='#262926')
    f=out/'registered-street-models.jpg';sheet.save(f,quality=94)
    data['sheet']=dict(file=f.name,sha256=sha(f));(out/'renders.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(data['mesh'],len(panels),sha(f),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--width',type=int,default=800);p.add_argument('--grid',type=int,choices=(1,2,3),default=2);args=p.parse_args()
    render(args.mesh,args.output,args.width,args.grid)
