"""Render the garden dormer from both recorded viewpoints using the exported complete building."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from photo_glb_raster import raster

HERE=Path(__file__).resolve().parent

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('full',type=Path);ap.add_argument('lod',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args()
    cameras=json.loads((HERE/'dormer-registration.json').read_text())['camera_models']
    sheet=Image.new('RGB',(1380,919),'#faf8f3')
    d=ImageDraw.Draw(sheet)
    fonts=Path('/usr/share/fonts/opentype/noto')
    def write(x,y,content,size,bold=False):
        f=ImageFont.truetype(str(fonts/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')),size,index=2)
        d.text((x,y),content,font=f,fill='#27302c')
    write(42,22,'胶州路450号住宅  ·  园侧单坡老虎窗',39,True)
    write(43,87,'六扇木百叶分成左右两组；每扇二十道，中间保留两块浅色实墙。',23)
    cases=[('13',args.full,[375,244,970,586],(38,158,811,602)),
           ('8',args.lod,[328,184,596,291],(841,236,1341,435)),
           ('8',args.full,[339,208,588,286],(38,625,1342,853))]
    sun=np.array([-.35,-.8,.54],np.float32);sun/=np.linalg.norm(sun)
    records=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'paint.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(HERE/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for cam,asset,crop,(x,y,r,b) in cases:
            # Preserve the native camera aspect ratio and centre the crop within its panel.
            ratio=(r-x)/(b-y);l,t,rr,bb=crop;wid=max(rr-l,(bb-t)*ratio);hei=wid/ratio
            crop=[(l+rr-wid)/2,(t+bb-hei)/2,(l+rr+wid)/2,(t+bb+hei)/2]
            image,record=raster(asset,lib,round(1.3*(r-x)),np.array(cameras[cam]),crop,sun,[204,32])
            assert record['textured_triangles'] and record['zbuffer_foreground_pixels']>1000
            assert any('louvre blades' in k for k in record['materials_visible_samples'])
            sheet.paste(image.resize((r-x,b-y),Image.Resampling.LANCZOS),(x,y))
            records.append(dict(view=cam,mesh_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),**record))
    write(840,164,'较正的院中视角',29,True)
    write(840,453,'远档保留逐片通透的百叶，',22)
    write(840,489,'可从檐下分辨两块中央墙板。',22)
    write(41,869,'上左为斜向仰视，下图为窗面近档。取景依据2020年庭院照片；画面由三维模型生成。',20)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(args.output,quality=92,optimize=True)
    args.output.with_suffix('.json').write_text(json.dumps(dict(rendered_from_model=True,frames=records),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    main()
