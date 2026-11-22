"""Render the six August 2017 shop panels with the licensed native photograph and actual mesh."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_lintel import RASTER, clip_near_plane, raster

HERE=Path(__file__).resolve().parent
CROPS=[
 ('房友 Fangyou.com',[660,2170,1740,2360]),
 ('Jill’s Nail Salon',[3197,2183,3661,2352]),
 ('风尚服饰',[3670,2200,4351,2355]),
 ('红袖添厢',[4370,2217,4895,2364])]
BLUE=[('左柱',[312,2411,553,2988]),('右柱',[1294,2410,1478,2988])]


def draw(photo,mesh,out):
    record=json.loads((HERE/'commons-2017-street-registered.json').read_bytes())
    P=np.array(record['matrix'])
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if digest(photo)!=record['native_sha256']:raise ValueError('Unexpected source photograph')
    src=Image.open(photo)
    page=Image.new('RGB',(1190,1070),'#f7f4ed')
    pen=ImageDraw.Draw(page)
    def label(x,y,title,size,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)
        pen.text((x,y),title,font=font,fill='#373028')
    label(30,12,'荣康别墅南弄口两侧的店招',37,True)
    label(30,70,'常熟路，2017年8月19日。街树遮住北侧部分字面，9月3日另一机位可辨。',18)
    label(31,114,'Antigng 原照',20,True);label(622,114,'同一机位的街面模型',20,True)
    sun=np.array([-.44,-.75,.49],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    renders=[]
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        temp=Path(tmp);so=temp/'r.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        clipped=temp/'visible.glb'
        stat=clip_near_plane(mesh,clipped,P)
        def pair(box,x,y,w,h):
            ratio=min(w/(box[2]-box[0]),h/(box[3]-box[1]));sz=(round(ratio*(box[2]-box[0])),round(ratio*(box[3]-box[1])))
            page.paste(src.crop(box).resize(sz,Image.Resampling.LANCZOS),(x,y))
            panel,rec=raster(clipped,lib,round(sz[0]*1.30),P,box,sun,angles)
            page.paste(panel.resize(sz,Image.Resampling.LANCZOS),(x+590,y))
            renders.append({'native_crop':box,'render':rec})
        for (name,box),y in zip(CROPS,[157,290,435,577]):
            label(32,y,name,17,True)
            pair(box,32,y+31,528,107)
        label(32,723,'两侧店柱　易居臣信',20,True)
        label(622,723,'按两次拍摄的位置复原',20,True)
        for (title,box),x in zip(BLUE,[31,263]):
            label(x,762,title,15)
            pair(box,x,793,90,193)
        label(32,1002,'蓝字在8月照片中受遮挡，「信」字笔画按9月可见字框配用思源黑体同源的 Noto Sans CJK SC Bold。',15)
        label(32,1037,'照片 Antigng／Wikimedia Commons，照片裁图和图板 CC BY-SA 4.0。',15)
    page.save(out,quality=89,optimize=True)
    out.with_suffix('.json').write_text(json.dumps({'photographer':'Antigng','source_page':record['source'],
       'photograph_sha256':digest(photo),'model_sha256':digest(mesh),'license':'CC BY-SA 4.0','license_url':'https://creativecommons.org/licenses/by-sa/4.0/',
       'camera':record['matrix'],'clip':stat,'renders':renders,'board_sha256':digest(out)},ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('photo','mesh','output'):p.add_argument(arg,type=Path)
    a=p.parse_args();a.output.parent.mkdir(parents=True,exist_ok=True);draw(a.photo,a.mesh,a.output)
