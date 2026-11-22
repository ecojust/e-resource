"""Render the released gatehouse from its surveyed street and detail cameras."""
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
sys.path[:0]=[str(RASTER),str(SIBLINGS/'huangpu-world-book-company-fuzhou-front/measurements'),str(HERE.parent/'source')]
from photo_glb_raster import raster
from fuzhou_skylight import SurfaceCapture,horizon_shading
from yongjia_photo_plane import matrix

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def font(size,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',size,index=2)

def build(mesh,out,mode):
    v=json.loads((HERE/'gatehouse-sign-readings.json').read_bytes())['views']
    deep=json.loads((HERE/'gatehouse-passage-readings.json').read_bytes())['source_views']['passage-depth-2017']
    def close(record):
        return np.linalg.solve(record['to_reference'],matrix(record['reference']))
    # Source rectangles of noticeably different proportions retain their own aspect ratio.
    views=[('共用门屋的街面',matrix('center15'),[170,19,563,495],(41,192,659)),
           ('19 弄 · 西愛邨',close(v['west']),[217,114,512,675],(701,192,963)),
           ('21 弄 · 恒愛里',close(v['east']),[227,32,550,584],(1007,192,1292)),
           ('入口门头的阶肩',close(deep),[170,252,550,354],(1333,192,1725)),
           ('收在墙边的铁门与值班室双窗',close(deep),[188,355,453,570],(703,766,1233)),
           ('门洞的铺地与圆形井盖',matrix('center20'),[407,471,610,548],(1282,766,1725))]
    ink=(46,48,43);muted=(83,88,77);bg=(246,245,239)
    paper=Image.new('RGB',(1769,1270),bg);d=ImageDraw.Draw(paper)
    d.text((40,16),'永嘉路 19、21 弄 · 西爱村与恒爱里共用门屋',font=font(42,True),fill=ink)
    d.text((43,87),'上海黄浦　｜　登记编号 5A060　｜　'+('近景模型'if mode=='full'else'轻量模型'),font=font(23),fill=muted)
    sun=np.array([-.30,-.64,.70]);sun/=np.linalg.norm(sun);meta=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'gatehouse.so'
        subprocess.run(['cc','-O2','-shared','-fPIC','-o',str(so),str(RASTER/'photo_glb_raster.c'),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for label,cam,crop,(x,y,right) in views:
            screen=SurfaceCapture(lib,mesh);w=right-x;h=round(w*(crop[3]-crop[1])/(crop[2]-crop[0]))
            im,data=raster(mesh,screen,round(w*1.58),cam,crop,sun,None)
            im,ao=horizon_shading(im,screen.depth,cam,crop)
            d.text((x,y-45),label,fill=ink,font=font(22,True))
            paper.paste(im.resize((w,h),Image.Resampling.LANCZOS),(x,y))
            meta.append(dict(view=label,crop=crop,pixels=data['zbuffer_foreground_pixels'],triangles=data['triangles'],skylight=ao))
    for i,line in enumerate(['两弄共用一处门洞。','西侧 19 弄下方另挂较宽的号牌；','东侧 21 弄牌旁有一根浅色落水管。']):
        d.text((1333,337+38*i),line,font=font(19),fill=muted)
    for i,line in enumerate(['门屋和开启的窗扇取自 2015 年街景。','铭牌的文字、号数按 2020 年影像排列。','门洞后方保留通行空间。']):
        d.text((42,992+41*i),line,font=font(21),fill=muted)
    d.line((41,1207,1725,1207),fill=(190,190,180),width=2)
    d.text((42,1224),'各视角由模型在实景机位绘制。值班室窗框依据 2017 年斜视图，门洞进深、牌面字形与光照为估计。',font=font(19),fill=muted)
    paper.save(out,quality=93,optimize=True,subsampling=0)
    out.with_suffix('.json').write_text(json.dumps({'mesh_sha256':sha(mesh),'image_sha256':sha(out),'level':mode,'views':meta,'source_calibration_sha256':sha(HERE/'yongjia-street-cameras.json'),'street_photos_embedded':False},ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--mode',choices=['full','lod'],required=True)
    a=parser.parse_args();build(a.mesh,a.output,a.mode)
