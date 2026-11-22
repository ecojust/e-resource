"""Render the actual released street mesh and compare the same camera with Antigng's 2017 photograph."""
from argparse import ArgumentParser
from pathlib import Path
import ctypes,hashlib,json,subprocess,sys,tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster
def perspective(eye,look,width,height,focal):
    eye=np.array(eye,float);forward=np.array(look,float)-eye;forward/=np.linalg.norm(forward);side=np.cross(forward,[0,0,1.]);side/=np.linalg.norm(side);up=np.cross(side,forward)
    R=np.stack([side,up,forward]);k=np.array([[focal,0,width/2],[0,-focal,height/2],[0,0,1.]])
    return k@np.c_[R,-R@eye]
def image_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def draw(mesh,original,out):
    src=json.loads((HERE/'southern-lane-evidence.json').read_bytes())['commons']
    cal=json.loads((HERE/'commons-2017-street-registered.json').read_bytes());assert image_hash(original)==src['sha256']
    board=Image.new('RGB',(1380,970),'#f7f4ec');p=ImageDraw.Draw(board)
    def label(x,y,t,s=19,bold=False):
        f='/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc';p.text((x,y),t,font=ImageFont.truetype(f,s,index=2),fill='#273d3b')
    label(36,12,'荣康别墅　常熟路南弄门及两侧街屋',35,True)
    label(39,69,'上海市第五批优秀历史建筑  5B061　 /　 静安区常熟路 102–120 号',19)
    p.line((38,111,1342,111),fill='#8c9c92',width=2);records=[]
    light=np.array([-.49,-.73,.59]);light/=np.linalg.norm(light);angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    with tempfile.TemporaryDirectory()as td:
        so=Path(td)/'rk-raster.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        P=perspective([-4.1,-34.6,12.1],[0,.55,6.02],1305,454,1100)
        for key,M,bounds,width,place in [('publication-street-overview',P,[0,0,1305,454],1305,(38,120)),('2017-08-19 camera',np.array(cal['matrix']),[0,850,5312,2920],637,(704,637))]:
            shot,stats=raster(mesh,lib,width,M,bounds,light,angles);board.paste(shot,place);records.append({'view':key,'camera_projection':M.tolist(),'render':stats})
    # The empty sky at either end leaves room for the two measured height leaders.
    for x,heading,value,anchor,elbow in [(53,'南侧突出檐柱','约 12.4 米',[-4.80,.58,12.40],247),(1112,'北侧突出檐柱','约 11.9 米',[9.02,-.09,11.89],1090)]:
        label(x,148,heading,17);label(x,177,value,23,True)
        hh=perspective([-4.1,-34.6,12.1],[0,.55,6.02],1305,454,1100)@[*anchor,1.]
        a,b=tuple((hh[:2]/hh[2]+[38,120]).round().astype(int))
        right=x>700;start=(x-10 if right else x+148,184)
        p.line([start,(elbow,184),(elbow,b-10),(a,b-10),(a,b-2)],fill='#687e75',width=2)
        p.ellipse((a-3,b-3,a+3,b+3),fill='#46615a')
    label(40,574,'南侧街屋和红色房友门面',17,True);label(565,574,'双峰门额和收拢铁扇',17,True);label(1005,574,'北侧街屋及三块店招',17,True)
    label(39,599,'2017 年 8 月 19 日原照',21,True);label(703,599,'从同一拍摄位置看模型',21,True)
    crop=[0,850,5312,2920];im=Image.open(original).crop(crop);im.thumbnail((636,249),Image.Resampling.LANCZOS);board.paste(im,(39,637))
    label(39,894,'摄影 Antigng，《荣康别墅》，Wikimedia Commons，CC BY-SA 4.0。照片保留街树与店前设施。',16)
    label(39,921,'独立模型覆盖南弄门、两侧可辨街墙和可见回墙。窗框、屋顶高低段、商铺玻璃和沿街通道均来自实体网格。',16)
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(mesh_sha256=image_hash(mesh),board_sha256=image_hash(out),source=src['page'],photographer=src['author'],photo_sha256=src['sha256'],crop=crop,license='CC BY-SA 4.0',license_url=src['license_url'],renders=records),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    q=ArgumentParser();q.add_argument('mesh',type=Path);q.add_argument('commons',type=Path);q.add_argument('output',type=Path);a=q.parse_args();draw(a.mesh,a.commons,a.output)
