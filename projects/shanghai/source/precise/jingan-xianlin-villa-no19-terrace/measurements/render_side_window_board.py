"""Assemble source-photo and same-camera GLB crops of the three courtyard-side windows."""
import argparse
import ctypes
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence'/'measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(HELPER)]
from courtyard_photo_plane import CAMERA,P
from photo_glb_raster import raster

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('decoded_full',type=Path);ap.add_argument('source_photo',type=Path);ap.add_argument('output',type=Path)
    q=ap.parse_args()
    photo=Image.open(q.source_photo).convert('RGB')
    assert hashlib.sha256(q.source_photo.read_bytes()).hexdigest()==CAMERA['image_sha256']
    paper=Image.new('RGB',(1320,888),'#fbf9f3');d=ImageDraw.Draw(paper)
    font_dir=Path('/usr/share/fonts/opentype/noto')
    def label(x,y,content,size,bold=False,fill='#333a35'):
        ff=font_dir/('NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc')
        d.text((x,y),content,font=ImageFont.truetype(str(ff),size,index=2),fill=fill)
    label(39,21,'贤邻别墅19号　庭院长墙上的三组窗',39,True)
    label(42,84,'每组左为2015年原照局部，右为近档模型的同机位视图。',23)
    panels=[('上层蓝色玻璃窗',(529,310,664,566),'上亮、两片高窗和下部矮亮分格。'),
            ('红窗上亮的两枚圆饰',(427,493,569,749),'左前窗侧壁遮住了部分深色下扇。'),
            ('小格上亮与成对红扇',(705,532,890,834),'底部窗裙带有凸起的矩形边线。')]
    sun=np.array([-.70,-.45,.55],np.float32);sun/=np.linalg.norm(sun)
    records=[]
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'window-render.so';subprocess.run(['cc','-O2','-fPIC','-shared',str(HELPER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for index,(title,crop,note) in enumerate(panels):
            x=38+index*426
            label(x,172,title,25,True)
            l,t,r,b=crop;aspect=201/441
            width=max(r-l,(b-t)*aspect);height=width/aspect
            crop=[(l+r-width)/2,(t+b-height)/2,(l+r+width)/2,(t+b+height)/2]
            original=photo.transform((402,882),Image.Transform.EXTENT,crop,Image.Resampling.BICUBIC)
            rendered,info=raster(q.decoded_full,lib,402,P,crop,sun,[237.3,33.5])
            assert info['zbuffer_foreground_pixels']>500
            for j,im in enumerate((original,rendered)):
                paper.paste(im.resize((201,441),Image.Resampling.LANCZOS),(x+j*207,231))
            label(x,694,note,16)
            records.append(dict(subject=title,**info))
    label(41,777,'摄影：Fayhoo，2015年12月26日，《Xianlin Bieshu.JPG》，Wikimedia Commons。',18)
    label(41,815,'原图截取、模型图版与编排：CC BY-SA 3.0。来源及许可链接见同名数据文件。',17)
    q.output.parent.mkdir(parents=True,exist_ok=True);paper.save(q.output,quality=92,optimize=True)
    q.output.with_suffix('.json').write_text(json.dumps(dict(asset_sha256=hashlib.sha256(q.decoded_full.read_bytes()).hexdigest(),
        source_photo=CAMERA['source'],source_photo_sha256=CAMERA['image_sha256'],photographer='Fayhoo',licence='https://creativecommons.org/licenses/by-sa/3.0/',
        changes='Cropped and resampled source photographs paired with new depth-tested model views, designed labels and panel layout.',
        harvested_pixels='Left image in each pair only.',observations=records),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    main()
