"""Render the school from three documented cameras, using only the editable geometry."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
HELPER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence'/'measurements'
sys.path[:0]=[str(HERE.parent/'source'),str(HELPER)]
from daren_photo_plane import camera_matrix
from photo_glb_raster import raster

def draw(mesh,out):
    sun=np.array([-.62,-.54,1.],dtype='float32');sun/=np.linalg.norm(sun)
    views=[('video-4.28',(35,35,922,562),'2026年街景写生视频的取景方向'),
           ('old15-corner',(0,45,996,550),'2015年从西侧看转角、平檐与屋坡'),
           ('video-4.28',(96,180,840,317),'钢窗长廊的十四个开口'),
           ('video-4.28',(334,346,852,529),'门前石露台与园界三道盲券')]
    board=Image.new('RGB',(1454,970),'#f7f4ee');d=ImageDraw.Draw(board)
    font=lambda n:ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',n)
    d.text((26,14),'康定东路20号　原大任小学校',font=font(34),fill='#292923')
    d.text((27,68),'临街钢窗与砖券、四坡红瓦顶和前院露台',font=font(22),fill='#514c44')
    places=[(26,134,690,406),(739,134,690,406),(26,590,690,306),(739,590,690,306)];rows=[]
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'raster.so';subprocess.run(['cc','-O2','-fPIC','-shared',str(HELPER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for (name,crop,title),(x,y,w,h) in zip(views,places):
            im,detail=raster(mesh,lib,800,camera_matrix(name),crop,sun,(145,25))
            im.thumbnail((w,h));d.text((x,y-31),title,font=font(19),fill='#37362d')
            board.paste(im,(x,y+(h-im.height)//2));rows.append(dict(camera=name,crop=crop,render=detail))
    d.text((26,920),'四个视图均由模型绘制。前院东侧屏墙以2026年影像定形，远端位置的跨期估计相差约1.5米。',font=font(19),fill='#514c44')
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=90,optimize=True)
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    out.with_suffix('.json').write_text(json.dumps(dict(model_sha256=sha(mesh),board_sha256=sha(out),views=rows,sources=['https://www.bilibili.com/video/BV1MeFVzqEiJ','2015-west-corner-exterior.json','street-front-cameras.json'],images='All pixels are rendered from the supplied model geometry.'),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);a=p.parse_args();draw(a.mesh,a.out)
