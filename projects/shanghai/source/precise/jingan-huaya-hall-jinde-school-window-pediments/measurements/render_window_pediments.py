"""Draw only the delivered meshes using the two independently registered source cameras."""
import argparse
import ctypes
from hashlib import file_digest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image,ImageDraw,ImageFont
import numpy as np
HERE=Path(__file__).resolve().parent
RASTER=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(RASTER))
from photo_glb_raster import raster
def sha(p):
    with p.open('rb')as f:return file_digest(f,'sha256').hexdigest()
def board(near,far,output):
    register=HERE/'2016-two-window-cameras.json';photographs=json.loads(register.read_bytes())
    canvas=Image.new('RGB',(1440,1070),'#f6f3ed')
    d=ImageDraw.Draw(canvas)
    def words(x,y,s,size,weight='Regular',color='#2f2d29'):
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc',size,index=2)
        d.text((x,y),s,font=f,fill=color)
    words(34,15,'花雅堂三联百叶窗',44,'Bold')
    words(36,83,'上海静安 · 延安中路718号　｜　言衣草 2016 年 11 月 2 日正面及斜面原照，用于测量与机位配准。',21)
    arrangements=[
      ('正面：三窗、三组卷草山花与六根壁柱','front',[0,88,4074,2262],near,34,138,900),
      ('右端窗的斜面','oblique',[205,1230,1180,3000],near,985,138,398),
      ('中央山花只存左翼卷草','front',[1424,193,2795,750],near,34,720,532),
      ('右端山花，两翼卷草均可辨','front',[2745,259,4033,789],far,599,720,512)]
    with tempfile.TemporaryDirectory()as td:
        so=Path(td)/'photo-raster.so';subprocess.run(['cc','-O2','-shared','-fPIC',RASTER/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        sun=np.array([-.39,-.72,.56]);sun/=np.linalg.norm(sun)
        receipts=[]
        for label,key,crop,mesh,x,y,width in arrangements:
            P=np.array(photographs[key]['P'])
            im,details=raster(mesh,lib,width,P,crop,sun,[209,35])
            if key=='oblique':
                # Keep the slanting cornice and foliage-free central part of the third jamb.
                im.thumbnail((398,497))
            canvas.paste(im,(x,y));words(x,y+im.height+7,label,18,'Bold')
            receipts.append(dict(view=label,camera=key,crop=crop,mesh=mesh.name,mesh_sha256=sha(mesh),render=details))
    words(35,996,'每窗四扇；上段 11 道、下段 30 道百叶。右侧窗扇下部在原照中受植物遮挡，叶片重复量取自中窗。',19)
    words(35,1032,'全部图像取自原创几何与程序材质；2.40 米窗间轴距为建模比例假定。',16,color='#675d52')
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(sha256=sha(output),registration_sha256=sha(register),reference_pixels_in_output=False,views=receipts),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ('near','far','output'):ap.add_argument(n,type=Path)
    a=ap.parse_args();board(a.near,a.far,a.output)
