"""Render the 1912—1936 roof cartouche and two of its legible details from a real mesh."""
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
CLIP=HERE.parents[1]/'huangpu-zhengjia-lane-39-street-gate/measurements'
sys.path[:0]=[str(RASTER),str(CLIP),str(HERE.parent/'source')]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane
from dated_cartouche import reference_frame

def camera_from_surface(tracing,view,layout):
    """Constrain the visible pale face by a measured homography; extrapolate only the shallow rim."""
    width,height,point=reference_frame(layout)
    center=np.asarray(point(0,0,.0165)); cx,cy,cz=center
    image=np.linalg.inv(np.array(tracing['image_to_rectified'][view]))
    grid=np.array([[647/width,0,323.5-647*cx/width],[0,-119/height,59.5+119*cz/height],[0,0,1.]])
    plane=image@grid
    # This roof-face crop determines a homography. A nearby camera height and stand-off cannot be recovered absolutely.
    eye_x=cx-width*(.35 if view=='2017_close'else .12);eye_y=cy-9*width;eye_z=cz-2.0*width
    depth=-(plane[:,0]*eye_x+plane[:,1]*eye_z+plane[:,2])/(eye_y-cy)
    matrix=np.column_stack((plane[:,0],depth,plane[:,1],plane[:,2]-depth*cy))
    matrix/=np.linalg.norm(matrix[2,:3])
    if (matrix@np.r_[center,1])[2]<0:matrix=-matrix
    return matrix

def make_board(model,out,layout):
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    data=json.loads((HERE/'dated-cartouche-tracings.json').read_bytes())
    board=Image.new('RGB',(1100,801),'#f6f3ed');pen=ImageDraw.Draw(board)
    def label(x,y,t,n,bold=False):
        family='Bold'if bold else'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+family+'.ttc',n,index=2)
        pen.text((x,y),t,font=font,fill='#222421')
    label(32,17,'塘沽路公寓楼冠纪年匾',34,True)
    label(34,72,'1912—1936',26)
    label(258,80,'两张不同时期的公开照片均可辨认这八个数字及中央长横。',17)
    specs=[
        ('2017_close',[207,61,372,112],(33,143),1033,'近照视角下的整幅匾面'),
        ('2017_close',[221,74,262,108],(34,494),267,'左截角、内沿与数字1'),
        ('2017_close',[306,66,356,100],(337,494),312,'右侧9、3、6与笔画内孔'),
        ('2015_press',[347,78,424,101],(710,494),356,'2015年报道照片的独立视角')]
    sun=np.array([-.47,-.67,.58],np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    # Each panel gets a strict crop of the historical decoration.
    records=[]
    with tempfile.TemporaryDirectory() as work:
        tmp=Path(work);libpath=tmp/'paint.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-lm','-o',str(libpath)],check=True)
        lib=ctypes.CDLL(str(libpath));lib.paint.restype=lib.shadow_depth.restype=None
        for view,crop,xy,span,title in specs:
            P=camera_from_surface(data,view,layout);part=tmp/'clipped.glb'
            clipped=clip_near_plane(model,part,P)
            im,record=raster(part,lib,round(span*1.30),P,crop,sun,angles)
            dest_height=round(span*im.height/im.width)
            board.paste(im.resize((span,dest_height),Image.Resampling.LANCZOS),xy)
            label(xy[0],xy[1]-30,title,18,True)
            records.append(dict(source_view=view,crop=crop,plane_camera=P.tolist(),render=record,clipping=clipped))
    # Keep explanatory copy below the full-height detail images.
    canvas=board
    label(34,735,'匾宽取4个展示单位，高宽比约0.181。浅底、深色周边与数字分别建模，凸出厚度据明暗关系估计。',16)
    label(34,766,'原始观察来自2015年人民网报道和2017年沂蒙生活转载图集。本图由可编辑模型渲染。',16)
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=90,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(model_sha256=sha(model),render_sha256=sha(out),measurements_sha256=sha(HERE/'dated-cartouche-tracings.json'),layout=layout,panels=records),ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('asset',type=Path);parser.add_argument('image',type=Path);parser.add_argument('--layout',type=Path,default=HERE/'cartouche-layout.json')
    args=parser.parse_args();make_board(args.asset,args.image,json.loads(args.layout.read_bytes()))
