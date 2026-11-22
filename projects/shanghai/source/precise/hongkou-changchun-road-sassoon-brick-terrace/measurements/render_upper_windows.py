"""Render the eight window axes from the registered 2023 and 2015 cameras."""
import argparse, ctypes, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(RASTER)]
from frontage_coordinates import FRONT_CAMERA,EARLIER_CAMERA
from photo_glb_raster import raster

def plate(near,far,out,record):
    page=Image.new('RGB',(1220,886),'#f8f5ee')
    draw=ImageDraw.Draw(page)
    def caption(x,y,message,size,bold=False):
        path='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc'
        font=ImageFont.truetype(path,size,index=2);draw.text((x,y),message,font=font,fill='#2d312d')
    caption(40,20,'长春路　八开间的十六组窗',39,True)
    caption(41,83,'三楼中段的浅弧压低了上亮。二楼的圆券下可辨放射窗梃、小内弧和不同的分扇。',21)
    sun=np.array([-.52,-.78,.74]);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    receipts=[]
    views=[(near,FRONT_CAMERA,[54,163,855,379],(40,135),1140,'2023年正照机位 · 八开间'),
           (near,FRONT_CAMERA,[164,286,345,376],(40,536),400,'中间小弧及放射梃 · 近景'),
           (far,FRONT_CAMERA,[709,166,828,242],(468,536),305,'外开扇与上亮 · 远景'),
           (near,EARLIER_CAMERA,[985,410,1784,1012],(803,536),377,'2015年斜照机位 · 近景')]
    with tempfile.TemporaryDirectory()as td:
        so=Path(td)/'render.so';subprocess.run(['cc','-shared','-O2','-fPIC',RASTER/'photo_glb_raster.c','-lm','-o',so],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for asset,camera,src,where,width,name in views:
            image,meta=raster(asset,lib,round(width*1.35),camera,src,sun,angles)
            height=round(width*image.height/image.width);page.paste(image.resize((width,height),Image.Resampling.LANCZOS),where)
            if where[1]==135:caption(where[0],453,name,19)
            else:caption(where[0],497,name,18,True)
            receipts.append(dict(label=name,asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),**meta))
    caption(40,832,'取景据上海虹口2023年正照、高参88摄于2015年4月25日的斜照。画面均由本项目真实网格生成。',18)
    page.save(out,quality=92,optimize=True)
    record.write_text(json.dumps(dict(views=receipts,plate_sha256=hashlib.sha256(out.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__)
    for n in ('near','far','out','record'):a.add_argument(n,type=Path)
    v=a.parse_args();plate(v.near,v.far,v.out,v.record)
