"""Original model-only plate for the two windows, from the measured Gao 04 camera."""
from pathlib import Path
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster

def plate(near,far,out,notes):
    camera=np.array(json.loads((HERE/'upper-window-observations.json').read_bytes())['camera_P'])
    page=Image.new('RGB',(1140,847),'#f7f4ed');d=ImageDraw.Draw(page)
    def label(x,y,s,n,bold=False):
        ft=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',n,index=2)
        d.text((x,y),s,font=ft,fill='#302f2b')
    label(34,16,'武进路225弄　双门上窗',39,True)
    label(36,79,'左为9号闭合白框窗，右为11号外开木窗。两处小篷按2015年院内照片复原。',21)
    label(35,136,'9号　蓝色平篷、双短上亮和两扇长窗',21,True)
    label(593,136,'11号　绿色波纹篷、三格外开木扇',21,True)
    light=np.array([-.44,-.76,.79]);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    receipts=[]
    with tempfile.TemporaryDirectory()as td:
        so=Path(td)/'renderer.so';subprocess.run(['cc','-shared','-O2','-fPIC',RASTER/'photo_glb_raster.c','-lm','-o',so],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        for asset,clip,where,siz,caption in [
          (near,[280,410,1240,1458],(35,185),(518,566),'9号 · 近景'),
          (far,[1540,28,2850,1460],(591,185),(518,566),'11号 · 远景')]:
            im,rec=raster(asset,lib,1036,camera,clip,light,angles)
            page.paste(im.resize(siz,Image.Resampling.LANCZOS),where)
            receipts.append(dict(model=caption,sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),**rec))
    label(35,768,'取景据高参88《武进路225弄9号、11号一对经典的双门》，2015年7月24日。两幅均为模型渲染。',19)
    label(35,808,'右窗红扇自由边伸出约0.35米，白扇约0.55米。尺寸以9号门净宽1.43米为参照。',17)
    page.save(out,quality=91,optimize=True)
    notes.write_text(json.dumps(dict(views=receipts,plate_sha256=hashlib.sha256(out.read_bytes()).hexdigest()),ensure_ascii=False,indent=1)+'\n')

if __name__=='__main__':
    a=argparse.ArgumentParser()
    for n in ['near','far','output','record']:a.add_argument(n,type=Path)
    v=a.parse_args();plate(v.near,v.far,v.output,v.record)
