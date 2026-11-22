"""Compare the pictured upper windows with the mesh at the same recorded photo crop."""
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
R=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(R),str(HERE.parent/'source')]
from photo_glb_raster import raster
from changde_photo_plane import camera_matrix
from paired_tower_windows import TIMBER,BRICK,KEY,GLASS

SOURCE='https://commons.wikimedia.org/wiki/File:Changde_Rd_and_Beijing_W_Rd_-_panoramio.jpg'
LICENSE='https://creativecommons.org/licenses/by/3.0/'
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def make(full,low,photo,output):
    info=json.loads((HERE/'tower-front-cameras.json').read_text())
    assert digest(photo)==info['images']['cc-panorama']['source_sha256']
    plate=Image.new('RGB',(1350,892),'#f6f4ef');draw=ImageDraw.Draw(plate)
    def note(pos,words,size,bold=False):
        style='Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+style+'.ttc',size,index=2)
        draw.text(pos,words,font=font,fill='#323629')
    note((36,20),'常德路310号信义会住宅',42,True)
    note((38,85),'塔楼双联券窗  ·  顶层实照与同机位近景模型',24)
    area=[1337,492,1639,798];sz=(493,500)
    with Image.open(photo) as original:
        plate.paste(original.crop(area).resize(sz,Image.Resampling.LANCZOS),(35,152))
    note((36,662),'2000年4月16日  ·  向院内斜看顶层窗',20,True)
    samples=[('cc-panorama',full,area,(557,152),sz),('gao-09',low,[402,209,550,397],(1070,231),(252,320))]
    records=[];sun=np.array([-.43,-.73,.57],np.float32);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'raster.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(R/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for cam,mesh,box,origin,size in samples:
            im,record=raster(mesh,lib,round(size[0]*1.4),camera_matrix(cam),box,sun,[209,34])
            visible=record['materials_visible_samples']
            for material in (BRICK,KEY,TIMBER):assert material in visible
            plate.paste(im.resize(size,Image.Resampling.LANCZOS),origin)
            records.append(dict(camera=cam,source_box_native=box,mesh_sha256=digest(mesh),**record))
    note((560,662),'同一视角  ·  近景模型',20,True)
    note((1071,173),'下一层的窗扇',25,True)
    note((1071,570),'上部另有两格横窗，',20)
    note((1071,607),'下部每扇分为四格。',20)
    note((38,748),'原照中的窗券有两道凸线，拱顶正中的楔石向外挑出。木窗退在券口内，窗台石伸出砖面。',23)
    note((38,829),'左图摄影 CyberCop，CC BY 3.0，局部裁切自《Changde Rd and Beijing W Rd》。模型光照为展示设置。',17)
    output.parent.mkdir(parents=True,exist_ok=True);plate.save(output,quality=92,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(credit='CyberCop',license='CC BY 3.0',license_url=LICENSE,
        source_url=SOURCE,photo_sha256=digest(photo),crop_native=area,modifications='Crop and scale only.',renders=records),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('full','low','photo','output'):ap.add_argument(k,type=Path)
    a=ap.parse_args();make(a.full,a.low,a.photo,a.output)
