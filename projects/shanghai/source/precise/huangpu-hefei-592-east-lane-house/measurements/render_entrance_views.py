"""Render the Hefei entrance from surveyed street cameras without distributing street photographs."""
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
SIBLINGS=HERE.parents[1]
RASTER=SIBLINGS/'huangpu-yuanmingyuan-apartments-street-front/measurements'
sys.path[:0]=[str(RASTER),str(SIBLINGS/'huangpu-world-book-company-fuzhou-front/measurements')]
from photo_glb_raster import raster
from fuzhou_skylight import SurfaceCapture,horizon_shading


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def font(size,bold=False):
    face='NotoSansCJK-Bold.ttc'if bold else'NotoSansCJK-Regular.ttc'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+face,size,index=2)


def make_plate(mesh,file,mode):
    gate=json.loads((HERE/'hefei-lane-gate-survey.json').read_bytes())['cameras']
    wall=json.loads((HERE/'hefei-street-cameras.json').read_bytes())['cameras']
    # A roughly midday February light is used illustratively. The panoramas
    # record the sample day but have no verified scene exposure in local time.
    sun=np.array([-.47,-.59,.657],dtype='float32');sun/=np.linalg.norm(sun)
    paper=Image.new('RGB',(1750,1415),(245,244,239));d=ImageDraw.Draw(paper)
    ink=(38,48,44);soft=(85,94,88)
    d.text((43,20),'合肥路 592 弄 · 弄口与东侧山墙',fill=ink,font=font(44,True))
    d.text((46,91),'上海黄浦　｜　2015 年 2 月街道机位　｜　'+('近景模型'if mode=='full'else'轻量模型'),fill=soft,font=font(23))
    areas=[
      ('沿合肥路向东看弄口',wall['2015_oblique'],[99,110,895,694],(43,186,1018,901)),
      ('东门扇外挑的上部铁格',gate['root-gate-feb-west'],[620,119,801,459],(1074,186,1370,742)),
      ('西柱的 592 弄牌与砖齿',gate['root-gate-feb-west'],[304,73,447,342],(1417,186,1707,732)),
      ('门柱与展开的铁门',gate['root-gate-feb-west'],[240,18,900,453],(43,958,613,1334)),
      ('向弄内看的三处百叶',wall['2015_west'],[142,163,381,492],(677,958,950,1334)),
      ('降缘石、人行道与弄口铺地',gate['root-gate-feb-east'],[113,336,882,708],(1001,958,1707,1300)),
    ]
    meta=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'hefei-raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC','-o',str(so),str(RASTER/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for title,view,rect,box in areas:
            c=np.array(view['projection']);x,y,X,Y=box;scale=1.4;ss=round((X-x)*scale)
            capture=SurfaceCapture(lib,mesh)
            im,info=raster(mesh,capture,ss,c,rect,sun,None)
            im,horizon=horizon_shading(im,capture.depth,c,rect)
            d.text((x,y-48),title,fill=ink,font=font(23,True))
            paper.paste(im.resize((X-x,Y-y),Image.Resampling.LANCZOS),(x,y))
            meta.append({'view':title,'camera_station':view.get('id',view.get('station')),'crop':rect,
                         'triangles':info['triangles'],'model_pixels':info['zbuffer_foreground_pixels'],
                         'near_field_skylight':horizon})
    d.text((1074,789),'两扇铁门的上缘合计约 3 米。',fill=soft,font=font(22))
    d.text((1074,832),'东扇上格比下框伸出约 0.5 米。',fill=soft,font=font(22))
    d.line((43,1353,1707,1353),fill=(193,193,184),width=2)
    d.text((45,1366),'本图各视角均由交付模型绘制。弄内 19、22 号位于后排，街景无法辨认其立面。',fill=soft,font=font(19))
    paper.save(file,quality=93,optimize=True,subsampling=0)
    file.with_suffix('.json').write_text(json.dumps({'input_mesh_sha256':sha(mesh),'geometry':mode,
       'image_sha256':sha(file),'views':meta,'illumination':'Illustrative February midday; exact exposure unresolved.',
       'sources':'February 2015 street cameras; contemporary field images are not present in this plate.',
       'calibration_sha256':sha(HERE/'hefei-street-cameras.json'),'entrance_survey_sha256':sha(HERE/'hefei-lane-gate-survey.json')},
       indent=1,ensure_ascii=False)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--mode',choices=['full','lod'],required=True);args=ap.parse_args()
    make_plate(args.mesh,args.output,args.mode)
