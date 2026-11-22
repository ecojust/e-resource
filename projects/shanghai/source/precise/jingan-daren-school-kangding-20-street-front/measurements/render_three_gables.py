"""Render an original model-only plate of the Daren School roof, using the recorded cameras."""
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
RENDER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(RENDER),str(HERE.parent/'source')]
from photo_glb_raster import raster
from daren_photo_plane import camera_matrix

def make(full,low,output):
    sheet=Image.new('RGB',(1376,855),'#f5f3ee');draw=ImageDraw.Draw(sheet)
    f=Path('/usr/share/fonts/opentype/noto')
    def text(x,y,s,size,bold=False):
        font=ImageFont.truetype(str(f/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')),size,index=2)
        draw.text((x,y),s,font=font,fill='#2d3537')
    text(36,23,'大任小学旧址屋顶三联山墙',41,True)
    text(39,88,'康定东路20号  ·  三座峰顶下各有一樘双扇窗，相邻谷部保留两只深色集水斗。',23)
    cases=[('video-cover',full,[745,2,1342,316],(36,148,847,582)),
           ('east20-peaks',low,[271,208,816,461],(875,196,1339,422)),
           ('centre20-peaks',full,[115,181,780,510],(37,622,560,827))]
    sun=np.array([-.38,-.72,.58],np.float32);sun/=np.linalg.norm(sun);records=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'raster.so';subprocess.run(['cc','-O2','-fPIC','-shared',str(RENDER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for cam,asset,box,place in cases:
            x,y,r,b=place;l,t,rr,bb=box;ratio=(r-x)/(b-y);wid=max(rr-l,(bb-t)*ratio);hi=wid/ratio
            crop=[(l+rr-wid)/2,(t+bb-hi)/2,(l+rr+wid)/2,(t+bb+hi)/2]
            im,record=raster(asset,lib,round((r-x)*1.35),camera_matrix(cam),crop,sun,[208,36])
            assert any('valley collector' in k for k in record['materials_visible_samples'])
            assert any('glazed' in k or 'glass' in k for k in record['materials_visible_samples'])
            sheet.paste(im.resize((r-x,b-y),Image.Resampling.LANCZOS),(x,y))
            records.append(dict(camera=cam,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),**record))
    text(877,149,'东侧视角 · 远档',25,True)
    text(878,446,'两道深色落水管位于峰谷下方，',21)
    text(878,480,'白色斜檐沿三幅灰色墙面相连。',21)
    text(590,625,'西侧视角 · 近档',25,True)
    text(591,673,'窗面距正墙约3.45米。东侧暗色回墙的深度可由',19)
    text(591,707,'两期街景量得。西端受树枝遮挡，按可见轮廓估计。',19)
    text(591,777,'三幅画面均由模型现场渲染，光照为展示设置。',18)
    output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(exclusively_new_model_pixels=True,frames=records),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('full',type=Path);p.add_argument('low',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();make(args.full,args.low,args.output)
