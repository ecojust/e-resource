"""Render two independently calibrated source views of the actual GLBs and a grille detail."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
COMMON=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(COMMON),str(HERE.parent/'source'),str(HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements')]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane
from guanghua_gate_camera import camera_matrix
from garden_gate_leaves import IRON,SKIN,LOCK

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def render(full,low,output):
    board=Image.new('RGB',(1168,810),'#faf7f1');d=ImageDraw.Draw(board)
    def note(x,y,text,size,weight='Regular'):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc',size,index=2)
        d.text((x,y),text,font=font,fill='#342e29')
    note(30,19,'光华里13号院门',40,'Bold')
    note(31,79,'巨鹿路786弄  ·  依2016年与2018年两次实地摄影复原',22)
    angles=[206,35];sun=np.array([-.43,-.71,.57],np.float32);sun/=np.linalg.norm(sun)
    samples=[('gao05',full,[278,85,550,477],(30,152),370,'2016年1月  ·  朝向门槛的视角'),
             ('yan04',low,[860,1375,2160,3595],(443,152),302,'2018年10月  ·  双扇远景网'),
             ('yan04',full,[1540,1705,1995,2175],(809,206),317,'右扇两端带折返短格')]
    records=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(COMMON/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for key,asset,crop,location,width,title in samples:
            projection=camera_matrix(key)
            visible_mesh=Path(tmp)/'camera-visible.glb'
            clipping=clip_near_plane(asset,visible_mesh,projection)
            out,row=raster(visible_mesh,lib,round(width*1.35),projection,crop,sun,angles)
            row['near_clipping']=clipping
            if IRON not in row['materials_visible_samples'] or SKIN not in row['materials_visible_samples']:
                raise ValueError('Photo crop misses the gate or grille.')
            if key=='gao05' and LOCK not in row['materials_visible_samples']:
                raise ValueError('Upper circular lock is missing.')
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            board.paste(out.resize((width,height),Image.Resampling.LANCZOS),location)
            note(location[0],location[1]+height+12,title,17,'Bold')
            records.append(dict(camera=key,glb_sha256=sha(asset),**row))
    note(810,608,'两根竖梃贯通，五道短横格',18)
    note(810,643,'在窗中央留有开口。',18)
    note(32,754,'模型按两扇门上的玻璃亮窗、信槽、两枚锁钮及石门槛实测。米制比例由门柱砖皮估算。',17)
    output.parent.mkdir(parents=True,exist_ok=True);board.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(cameras_source='no13-garden-gate-cameras.json',metrics='no13-gate-details.json',original_photograph_pixels_in_board=0,records=records),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for key in ['full','lod','output']:ap.add_argument(key,type=Path)
    a=ap.parse_args();render(a.full,a.lod,a.output)
