"""Draw a registered photograph/GLB pair and an independent garden-view projection."""
import argparse,ctypes,hashlib,json,os,subprocess,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
BACKEND=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(BACKEND))
from photo_glb_raster import raster

def draw(photo,mesh,output):
    layout=json.loads((HERE/'garden-front-layout.json').read_bytes())
    color=(44,49,46);accent=(133,66,43);bg=(246,244,236);quiet=(75,82,74)
    board=Image.new('RGB',(1464,771),bg);d=ImageDraw.Draw(board)
    typefile=next(p for p in [Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'),Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')] if p.exists())
    def text(x,y,s,n=17,ink=color):d.text((x,y),s,font=ImageFont.truetype(str(typefile),n),fill=ink)
    fd=os.memfd_create('garden-front-raster',0);target='/proc/self/fd/'+str(fd)
    subprocess.run(['cc','-O2','-shared','-fPIC',str(BACKEND/'photo_glb_raster.c'),'-lm','-o',target],pass_fds=(fd,),check=True)
    lib=ctypes.CDLL(target);lib.paint.restype=lib.shadow_depth.restype=None
    sun=np.array([-.51,-.70,.58],dtype=np.float32);sun/=np.linalg.norm(sun)
    crop=[205,88,1040,1196];w=431;h=round((crop[3]-crop[1])*w/(crop[2]-crop[0]))
    orig=Image.open(photo).convert('RGB');assert hashlib.sha256(photo.read_bytes()).hexdigest()=='e01c70ff00fa37bff3202cf71a1f6e0ea6270a9ac2f2ebc205a78c632ce3eeb4'
    render,first=raster(mesh,lib,w,np.asarray(layout['camera_P']),crop,sun,[216,36])
    secondary,second=raster(mesh,lib,506,np.asarray(layout['second_camera_P']),[0,10,358,324],sun,[216,36])
    text(27,12,'山阴路209弄3号 · 花园正面',33)
    text(29,62,'Fayhoo · 2015年原照',20,accent);text(480,62,'同一机位 · 三维复原',20,accent);text(936,62,'第二张照片的机位 · 三维复原',20,accent)
    board.paste(orig.crop(crop).resize((w,h),Image.Resampling.LANCZOS),(27,107));board.paste(render,(478,107));board.paste(secondary,(934,107))
    text(936,568,'瓦面与廊檐',23)
    for y,t in [(615,'两幅照片共同约束了正檐和两扇屋窗的位置。'),(645,'前方瓦坡约29°，后部较高瓦面的进深仍属估计。'),(675,'同一保护记录下的229弄另有建筑与门号。')]:text(936,y,t,17,quiet)
    d.line((27,713,1438,713),fill=(180,179,161))
    text(27,725,'照片及改绘图板  © Fayhoo / CC BY-SA 3.0  ·  Commons “Shanyinlu 209 Long Zhuzhai.JPG”  ·  2022年所刊第二机位只用于几何测量',16,quiet)
    output.parent.mkdir(parents=True,exist_ok=True);board.save(output,quality=90,optimize=True)
    report=dict(source_photo='https://commons.wikimedia.org/wiki/File:Shanyinlu_209_Long_Zhuzhai.JPG',
                photographer='Fayhoo',license='https://creativecommons.org/licenses/by-sa/3.0/',source_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),
                mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),comparison_jpg_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),first=first,second=second)
    output.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('photo','mesh','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();draw(args.photo,args.mesh,args.output)
