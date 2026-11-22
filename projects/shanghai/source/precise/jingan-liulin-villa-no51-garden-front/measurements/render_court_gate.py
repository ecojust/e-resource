"""Render the actual two delivery meshes at the registered 2014 No.51 gate viewpoint."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
RASTER=BASE/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(RASTER),str(BASE/'huangpu-zhengjia-lane-39-street-gate/measurements'),str(HERE.parent/'source')]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane
from court_gate import BRASS, INK, PIER, STEEL


def digest(path):
    with path.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()


def render(near,far,out,local=False):
    source=(HERE/'gate-plane-and-inscription.json') if local else (HERE/'no51-house-cameras.json')
    d=json.loads(source.read_text())
    p=np.array(d['P_native'] if local else d['source_poses']['gao05']['P'])
    board=Image.new('RGB',(1310,849),'#f7f3eb');draw=ImageDraw.Draw(board)
    def text(x,y,content,size,bold=False):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',size,index=2)
        draw.text((x,y),content,fill='#302a26',font=font)
    text(28,15,'柳林别墅51号院门',40,True)
    text(31,75,'上海市静安区愚园路532弄  ·  依2014年6月2日的门外实景复原',21)
    tiles=[(near,[0,225,4428,3266],(28,139),805,'院门与双柱的位置', [PIER,STEEL]),
           (far,[1695,780,3020,1585],(870,139),409,'卷草冠饰与浅弧上框', [STEEL]),
           (near,[3420,1103,3910,1468],(899,469),350,'右侧石柱门牌的两行铭字', [BRASS,INK])]
    sun=np.array([-.48,-.72,.52]);sun/=np.linalg.norm(sun);rows=[]
    with tempfile.TemporaryDirectory()as tmp:
        scratch=Path(tmp);so=scratch/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for i,(asset,crop,(x,y),width,title,materials) in enumerate(tiles):
            clipped=scratch/f'visible-{i}.glb'
            clipping=clip_near_plane(asset,clipped,p)
            img,review=raster(clipped,lib,round(width*1.28),p,crop,sun,[205,39])
            for mat in materials:
                if mat not in review['materials_visible_samples']:raise ValueError('Missing measured material '+mat)
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            board.paste(img.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            text(x,y+height+9,title,18,True)
            rows.append(dict(file=asset.name,sha256=digest(asset),crop_native_px=crop,normative_camera_sha256=digest(source),
                near_clipping=clipping,render=review))
    text(29,749,'两扇门的浅弧上框、卷草和尖饰由实体铁条构成。右侧门扇另含矩形小门。',18)
    text(29,788,'摄影测量据高参88所摄院门及主楼原照。图中房屋、铁件、石材与光影均取自产出的三维模型。',17)
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(views=rows,output_sha256=digest(out),image_size=list(board.size),source_photo_embedded=False,
        source_study='https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480101ilpi.html'),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('near',type=Path);parser.add_argument('far',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--local',action='store_true')
    args=parser.parse_args();render(args.near,args.far,args.output,args.local)
