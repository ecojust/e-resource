"""Render three documented exterior viewpoints using only original model surfaces."""
import argparse,ctypes,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE=Path(__file__).resolve().parent
TOOLS=HERE.parents[1]/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path.insert(0,str(TOOLS))
from photo_glb_raster import raster

def render(near,far,output):
    front=json.loads((HERE/'registered-courtyard-cameras.json').read_bytes())['cameras']['front-b']
    rear=json.loads((HERE/'lane-and-rear-cameras.json').read_bytes())['sources']['04']
    pf=np.array(front['P']);pf[:2]*=950/front['working_size'][1]
    pr=np.array(rear['P'])
    layout=[('庭院楼上',near,pf,(113,303,441,458),(30,120),(678,320),(-.4,-.92,.80)),
            ('后角两面的螺旋柱',near,pr,(31,533,478,782),(743,120),(453,320),(-.73,.51,.55)),
            ('庭院木门与拱形上亮',near,pf,(322,495,469,735),(30,521),(265,325),(.23,-.89,.59)),
            ('巷侧圆券、通透铁花与窗台',far,pr,(351,551,555,766),(339,521),(365,325),(-.78,.55,.82)),
            ('二层木扇与玻璃分格',far,pr,(301,267,472,451),(736,521),(460,325),(-.88,.41,.75))]
    sheet=Image.new('RGB',(1230,954),'#f9f7ee');draw=ImageDraw.Draw(sheet)
    def label(x,y,msg,size=20,bold=False):
        f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',size,index=2)
        draw.text((x,y),msg,font=f,fill='#26343b')
    label(30,15,'东体育会路119弄老3号住宅   ·   木扇与螺旋柱',35,True)
    label(30,70,'原照片拍于2015年10月6日，以下各图均从整栋模型按照片机位渲染。',21)
    records=[]
    with tempfile.TemporaryDirectory() as t:
        so=Path(t)/'render.so';subprocess.run(['cc','-O2','-fPIC','-shared',TOOLS/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.shadow_depth.restype=lib.paint.restype=None
        for caption,asset,P,crop,loc,size,light in layout:
            # Preserve the aspect ratio of the registered camera crop.
            ix,iy=loc;sw,sh=size
            aspect=sw/sh;cx=(crop[0]+crop[2])/2;cy=(crop[1]+crop[3])/2
            w=max(crop[2]-crop[0],(crop[3]-crop[1])*aspect);h=w/aspect
            rect=(cx-w/2,cy-h/2,cx+w/2,cy+h/2)
            s=np.array(light,dtype='float32');s/=np.linalg.norm(s)
            pic,meta=raster(asset,lib,round(sw*1.15),P,rect,s,[])
            assert meta['zbuffer_foreground_pixels']>2000
            sheet.paste(pic.resize(size,Image.Resampling.LANCZOS),loc)
            label(ix,iy+sh+5,caption,21,True)
            records.append(dict(caption=caption,sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),crop=rect,P=P.tolist(),**meta))
    label(30,906,'图中墙面与木扇的比例按庭面宽8.40个模型单位归一；巷面四樘上窗受树叶、设备遮挡。',19)
    output.parent.mkdir(parents=True,exist_ok=True);sheet.save(output,quality=90,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(views=records,rights='Original GLB renders. Original photography supplied image coordinates only.'),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();render(a.near,a.far,a.output)
