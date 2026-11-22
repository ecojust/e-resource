"""Compare the CC-licensed 2015 photograph and the mesh from the same camera."""
from pathlib import Path
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster

def plate(near,far,photo,out,camera):
    native=json.loads((HERE/'ground-arcade-source.json').read_bytes())['photograph']
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==native['sha256']
    p=np.asarray(camera['ground_camera_P'],float);im=Image.open(photo).convert('RGB')
    board=Image.new('RGB',(1328,887),'#f6f2e9');ink=ImageDraw.Draw(board)
    def label(x,y,text,size,bold=False):
        face='Bold'if bold else'Regular'
        font=ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{face}.ttc',size,index=2)
        ink.text((x,y),text,font=font,fill='#282722')
    label(30,12,'山阴路209弄3号 · 底层砖券花园廊',36,True)
    label(32,69,'2015年同一取景中的三道券、灰砖墩与左侧扇形铁罩',22)
    light=np.asarray([-.40,-.76,.70]);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    reports=[]
    with tempfile.TemporaryDirectory() as temp:
        so=Path(temp)/'arch-render.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',RASTER/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for row,(mesh,crop,w,h,top,descriptors) in enumerate([
           (near,[266,789,1003,1145],620,300,145,('2015年4月 · 原片局部','近景网格 · 同一视线')),
           (far,[285,805,560,942],620,307,504,('左券 · 放射铁条、折回栅面及柱头','远景网格 · 砖券与铁罩保持通透'))]):
            label(31,top-32,descriptors[0],20,True);label(675,top-32,descriptors[1],20,True)
            b=im.crop(tuple(crop)).resize((w,h),Image.Resampling.LANCZOS)
            board.paste(b,(32,top))
            view,record=raster(mesh,lib,w*2,p,crop,light,angles)
            board.paste(view.resize((w,h),Image.Resampling.LANCZOS),(675,top))
            reports.append(dict(mode='full'if not row else'lod',mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),crop=crop,raster=record))
    secondary=json.loads((HERE/'ground-arcade-second-photo.json').read_bytes())
    label(32,818,'另据2022年发表的3–4号合照，两处柱头与两道券顶在第二张照片中相差1.5–2.6像素。',16)
    label(32,850,'摄影 Fayhoo，2015 · Wikimedia Commons，CC BY-SA 3.0（裁切）；同机位模型图与整版按相同许可分享。',15)
    out.parent.mkdir(exist_ok=True,parents=True);board.save(out,quality=91,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(photo=native,independent_geometry_source={'title':secondary['target'],'url':secondary['article'],'sha256':secondary['independent_image_sha256'],'date_published':secondary['secondary_publication_utc'],'holdouts':secondary['held_out'],'off_plane_grille':secondary['off_plane_grille']},license='CC BY-SA 3.0',cropped=True,views=reports,image_sha256=hashlib.sha256(out.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('near',type=Path);a.add_argument('far',type=Path);a.add_argument('photo',type=Path);a.add_argument('out',type=Path);a.add_argument('--camera',type=Path,default=HERE/'ground-arcade-camera.json')
    o=a.parse_args();d=json.loads(o.camera.read_bytes());plate(o.near,o.far,o.photo,o.out,{'ground_camera_P':d.get('ground_camera_P',d.get('camera_P'))})
