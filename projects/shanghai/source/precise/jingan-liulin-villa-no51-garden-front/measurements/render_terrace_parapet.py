"""Render the two measured upper-parapet meshes with Gao's second garden camera."""
import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from render_court_gate import HERE, RASTER, clip_near_plane, digest, raster
from terrace_parapet import BRICK, CAP, MORTAR

def draw_board(near, far, out):
    camera=HERE/'no51-house-cameras.json'
    P=np.array(json.loads(camera.read_text())['source_poses']['gao06']['P'])
    board=Image.new('RGB',(1340,962),'#f6f3ed')
    pen=ImageDraw.Draw(board)
    def label(x,y,value,size,bold=False):
        family='Bold' if bold else 'Regular'
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+family+'.ttc',size,index=2)
        pen.text((x,y),value,fill='#302a26',font=font)
    label(30,14,'柳林别墅51号弧形露台女儿墙',37,True)
    label(32,69,'高参88于2014年6月2日从院内拍摄的角度  ·  原创三维模型视图',20)
    rows=[]
    specs=[
        (near,[1190,395,3270,1045],(29,119),1282,'三层露台与两翼凸窗'),
        (near,[1870,688,2330,914],(29,594),609,'中段十五皮顺丁交替，第二皮竖缝错开半个周期'),
        (far,[2590,520,3085,766],(683,594),628,'弧墙右端、浅色压顶与侧翼窗边收口'),
    ]
    sun=np.array([-.48,-.72,.52]);sun/=np.linalg.norm(sun)
    with tempfile.TemporaryDirectory() as tmp:
        scratch=Path(tmp);so=scratch/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(RASTER/'photo_glb_raster.c'),'-o',str(so),'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        clipped={}
        for mesh, crop, (x,y), width, description in specs:
            if mesh not in clipped:
                path=scratch/(str(len(clipped))+'.glb')
                clipped[mesh]=(path,clip_near_plane(mesh,path,P))
            path,clipping=clipped[mesh]
            img,review=raster(path,lib,round(width*1.30),P,crop,sun,[205,39])
            colours=review['materials_visible_samples']
            assert MORTAR in colours and any(mat in colours for mat in BRICK)
            if len(rows)!=1:assert CAP in colours
            height=round(width*(crop[3]-crop[1])/(crop[2]-crop[0]))
            board.paste(img.resize((width,height),Image.Resampling.LANCZOS),(x,y))
            label(x,y+height+7,description,18,True)
            rows.append(dict(mesh=mesh.name,asset_sha256=digest(mesh),native_crop=crop,render=review,positive_clipping=clipping))
    out.parent.mkdir(parents=True,exist_ok=True);board.save(out,quality=93,optimize=True)
    out.with_suffix('.json').write_text(json.dumps(dict(source_camera='gao06',camera_sha256=digest(camera),
        glb_views=rows,image_size=list(board.size),source_photo_embedded=False,output_sha256=digest(out)),
        ensure_ascii=False,indent=1)+'\n')
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('near',type=Path);ap.add_argument('far',type=Path);ap.add_argument('output',type=Path)
    args=ap.parse_args();draw_board(args.near,args.far,args.output)
