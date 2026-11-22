"""Render only the historical crest at the measured photographic projection."""
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
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def draw(near,far,out):
    camera=HERE/'central-tablet-metric.json'
    P=np.array(json.loads(camera.read_text())['2018_P']);board=Image.new('RGB',(1140,803),'#f8f6f0');ink=ImageDraw.Draw(board)
    def title(point,word,n,bold=False):
        style='Bold' if bold else 'Regular'
        face=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{style}.ttc',n,index=2)
        ink.text(point,word,font=face,fill='#342f29')
    title((31,15),'程氏旧宅临街立面的八角石牌',36,True)
    title((33,75),'据历史旧貌与高参88于2018年拍摄的街面原照复原。石牌内的题字或纹样无法释读。',19)
    tiles=[(near,[1385,766,1746,1151],(32,133),564,'石牌、石额与下承石',['exposed aggregate','light cap','bottom stone']),
           (near,[1397,777,1738,923],(640,133),467,'石额两端下垂，正中留出阴影',['grey hood stone','light cap']),
           (far,[1440,988,1694,1143],(640,442),467,'左下削角、窄斜边与下承石',['exposed aggregate','bottom stone'])]
    sun=np.array([-.065,-.985,.162]);sun/=np.linalg.norm(sun);rows=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for asset,crop,(x,y),width,caption,required in tiles:
            img,review=raster(asset,lib,round(1.2*width),P,crop,sun,[184,9])
            assert all('Tablet | '+r in review['materials_visible_samples'] for r in required)
            h=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]));board.paste(img.resize((width,h),Image.Resampling.LANCZOS),(x,y));title((x,y+h+8),caption,18,True)
            rows.append({'asset':asset.name,'sha256':digest(asset),'render':review})
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=93,optimize=True)
    out.with_suffix('.json').write_text(json.dumps({'model_only':True,'native_photo_embedded':False,'camera_data_sha256':digest(camera),
        'source_view':'高参88，2018年6月27日','board_sha256':digest(out),'tiles':rows},ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('near','far','out'):p.add_argument(k,type=Path)
    a=p.parse_args();draw(a.near,a.far,a.out)
