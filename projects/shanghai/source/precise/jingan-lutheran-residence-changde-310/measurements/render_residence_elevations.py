"""Render the camera-registered facade, recessed wing, tower and front porch."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence'/'measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(HELPER)]
from changde_photo_plane import camera_matrix
from photo_glb_raster import raster

def draw(mesh,out):
    sun=np.array([-.62,-.54,1.],dtype='float32');sun/=np.linalg.norm(sun)
    views=[('gao-01',(44,-23,569,450),'沿街灰砖塔、红券与坡屋顶'),
           ('nina-13',(570,80,2980,1870),'庭院斜看凸窗、南翼转折与陶饰'),
           ('gao-09',(52,235,377,391),'两樘宽券窗、窗楣和气窗'),
           ('nina-03',(197,99,2590,1830),'曲栏、成对石柱与木门')]
    board=Image.new('RGB',(1454,970),'#f7f4ee');d=ImageDraw.Draw(board)
    font=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
    d.text((26,14),'常德路310号　信义会住宅',font=font(34),fill='#292923')
    d.text((27,68),'临街灰砖红券、转角塔楼与庭院石柱门廊',font=font(22),fill='#514c44')
    places=[(26,134,690,406),(739,134,690,406),(26,590,690,306),(739,590,690,306)];rows=[]
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'raster.so';subprocess.run(['cc','-O2','-fPIC','-shared',str(HELPER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for (name,crop,title),(x,y,w,h) in zip(views,places):
            im,detail=raster(mesh,lib,800,(np.array(json.loads((HERE/'south-wing-camera.json').read_text())['P']) if name=='nina-13' else camera_matrix(name)),crop,sun,(145,25))
            im.thumbnail((w,h));d.text((x,y-31),title,font=font(19),fill='#37362d')
            board.paste(im,(x,y+(h-im.height)//2));rows.append(dict(camera=name,crop=crop,render=detail))
    d.text((26,920),'四个方向均由整栋三维模型绘制。南翼进深与背坡取自照片估形，局部尺寸可在测量表中复算。',font=font(19),fill='#514c44')
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=90,optimize=True)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    out.with_suffix('.json').write_text(json.dumps(dict(model_sha256=sha(mesh),board_sha256=sha(out),views=rows,sources=['https://www.meipian.cn/3f5icwhf','tower-front-cameras.json','south-wing-camera.json'],images='All pixels are rendered from the supplied model geometry.'),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();draw(a.mesh,a.out)
