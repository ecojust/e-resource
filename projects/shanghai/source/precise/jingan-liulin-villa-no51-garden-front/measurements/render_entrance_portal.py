"""Render the delivered close and low meshes from the registered garden camera; input photos are never opened."""
import argparse
import ctypes
from hashlib import file_digest
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
RASTER=BASE/'jingan-jiaozhou-450-garden-residence/measurements'
sys.path[:0]=[str(RASTER),str(BASE/'huangpu-zhengjia-lane-39-street-gate/measurements')]
from photo_glb_raster import raster
from clip_courtyard_camera import clip_near_plane

def digest(p):
    with p.open('rb') as stream:return file_digest(stream,'sha256').hexdigest()

def render(near,far,output):
    camera_file=HERE/'no51-house-cameras.json'
    camera=np.asarray(json.loads(camera_file.read_bytes())['source_poses']['gao06']['P'])
    bg='#f4f0e7';ink='#302923';muted='#5f544a'
    board=Image.new('RGB',(1400,990),bg);draw=ImageDraw.Draw(board)
    def text(x,y,value,size,weight='Regular',color=ink):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+weight+'.ttc',size,index=2)
        draw.text((x,y),value,font=font,fill=color)
    text(34,18,'柳林别墅51号 · 柱后主入口',43,'Bold')
    text(36,81,'愚园路532弄　｜　依据高参88的两幅园侧原照测量，以下各图取自交付模型。',21,color=muted)
    sun=np.array([-.36,-.77,.53]);sun/=np.linalg.norm(sun)
    panels=[('柱后的门与两侧窄窗',near,(1595,1910,2885,2785),(36,143),858),
            ('左门框上的卷叶、绶结与齿饰',near,(1991,1950,2152,2391),(934,143),171),
            ('右扇外开时的暗缝',far,(2195,2080,2440,2600),(1146,143),203),
            ('石级鼻口与立板',near,(1514,2611,2575,2821),(55,783),544)]
    views=[]
    with tempfile.TemporaryDirectory() as tmp:
        folder=Path(tmp);so=folder/'raster.so'
        subprocess.run(['cc','-O2','-fPIC','-shared',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        inputs={}
        for mesh in (near,far):
            clipped=folder/(mesh.stem+'-facing.glb')
            report=clip_near_plane(mesh,clipped,camera)
            inputs[mesh]=(clipped,report)
        for label,mesh,crop,(x,y),width in panels:
            clipped,clip_report=inputs[mesh]
            im,details=raster(clipped,lib,width,camera,list(crop),sun,[205,34])
            if details['zbuffer_foreground_pixels']<=0:raise ValueError(label)
            board.paste(im,(x,y));text(x,y+im.height+5,label,17,'Bold')
            views.append(dict(title=label,mesh=mesh.name,sha256=digest(mesh),native_crop=crop,
                              camera='gao06',clipping=clip_report,render=details))
    text(925,662,'每侧窄窗的两扇木窗各分八格。',19)
    text(925,698,'主门上部各分六格，下部保留凸起的木框。',18)
    text(653,791,'从院地到门廊，三级石阶分别升至',23,'Bold')
    text(655,841,'0.177 米、0.348 米、0.523 米。',24)
    text(655,899,'左端被花盆遮住，端部形状按露出的石边续接。',17,color=muted)
    text(35,947,'木纹与石粒为原创程序材质。拍摄资料仅用于测量与比对。',16,color=muted)
    output.parent.mkdir(parents=True,exist_ok=True);board.save(output,quality=91,optimize=True)
    output.with_suffix('.json').write_text(json.dumps(dict(image=output.name,sha256=digest(output),camera_sha256=digest(camera_file),
            image_dimensions=list(board.size),photographic_pixels_in_board=False,panels=views),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path)
    a=ap.parse_args();render(a.near,a.far,a.output)
