"""Render two Chinese garden-arcade plates from the actual exported GLBs.

Supply --full, --lod and --out. The helper uses NumPy, Pillow, Noto CJK and cc.
The two photo matrices are numeric only. No source photographs are used in the plates.
"""
import argparse
import ctypes
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image,ImageDraw,ImageFont
from photo_glb_raster import raster

HERE=Path(__file__).resolve().parent
INK='#282b26'
GREY='#635e54'
RUST='#8f513f'
RULE='#c6b7a5'
PAPER='#fbf8f1'
SIZE=(1480,1080)


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def camera(eye,subject):
    eye=np.array(eye,dtype=float)
    axis=np.asarray(subject)-eye
    axis/=np.linalg.norm(axis)
    right=np.cross(axis,[0,0,1])
    right/=np.linalg.norm(right)
    down=np.cross(axis,right)
    a=np.array([right*1300,down*1300,axis])
    return np.column_stack((a,-a@eye))


def projected_box(matrix,x_bounds,y_bounds,z_bounds):
    corners=np.array([[*p,1.] for p in product(x_bounds,y_bounds,z_bounds)])
    projected=corners@matrix.T
    xy=projected[:,:2]/projected[:,2,None]
    return [*xy.min(axis=0),*xy.max(axis=0)]


def frame(rect,size):
    x0,y0,x1,y1=rect
    w=max(x1-x0,(y1-y0)*size[0]/size[1]);h=w*size[1]/size[0]
    x=(x0+x1)/2;y=(y0+y1)/2
    return [float(x-w/2),float(y-h/2),float(x+w/2),float(y+h/2)]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--full',required=True,type=Path)
    ap.add_argument('--lod',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--font-dir',type=Path,default=Path('/usr/share/fonts/opentype/noto'))
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    section_file=HERE/'garden-arcade-sections.json';camera_file=HERE/'arcade-cameras.json'
    back_file=HERE/'porch-back-wall-registration.json'
    sections=json.loads(section_file.read_bytes())
    registration=json.loads(back_file.read_bytes())
    original=json.loads(camera_file.read_bytes())
    matrices={k:np.asarray(original[k]['P']) for k in ('13','8')}
    blocks=[len(x['brick_tone']) for x in sections['arcades']]
    assert blocks==[97,100,101,96]
    rails=sections['balustrade']
    assert rails['visible_first_three_spans']==[7,7,7] and rails['west_return']['count']==6
    assert registration['camera_sha256']==sha(camera_file)
    sun=np.array([-.48,-.79,.38],dtype=np.float32);sun/=np.linalg.norm(sun)
    light=[211.3,22.4]
    panels={}

    @lru_cache(maxsize=16)
    def font(size,weight='regular'):
        family='NotoSerifCJK' if weight=='title' else 'NotoSansCJK'
        bold=weight in ('title','bold')
        return ImageFont.truetype(str(args.font_dir/(family+('-Bold' if bold else '-Regular')+'.ttc')),size,index=2)

    def write(d,xy,words,size=22,weight='regular',color=INK):
        d.text(xy,words,font=font(size,weight),fill=color,anchor='la')

    def sheet(name,sub):
        sheet=Image.new('RGB',SIZE,PAPER);d=ImageDraw.Draw(sheet)
        write(d,(50,27),'上海静安  ／  胶州路450号',23,'bold',RUST)
        write(d,(47,62),name,50,'title')
        write(d,(50,138),sub,22,'regular',GREY)
        d.line((50,185,1430,185),fill=RULE,width=2)
        return sheet,d

    def foot(d,label):
        d.line((50,1003,1430,1003),fill=RULE,width=2)
        write(d,(50,1021),label,19,'regular',GREY)

    def render(sheet,key,mesh,matrix,rect,dst):
        x,y,width,height=dst
        crop=frame(rect,(width,height))
        view,info=raster(mesh,lib,round(width*1.35),matrix,crop,sun,light)
        assert info['textured_triangles'] and info['zbuffer_foreground_pixels']>1000
        sheet.paste(view.resize((width,height),Image.Resampling.LANCZOS),(x,y))
        panels[key]={'mesh_sha256':sha(mesh),'projection':matrix.tolist(),**info}
        return info

    with tempfile.TemporaryDirectory(prefix='garden-arcade-boards-') as scratch:
        so=Path(scratch)/'raster.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',HERE/'photo_glb_raster.c','-o',so,'-lm'],check=True)
        lib=ctypes.CDLL(str(so));lib.paint.restype=lib.shadow_depth.restype=None
        sheet1,d=sheet('园侧四跨砖拱廊','四跨券洞承托露台。砖券从两侧起拱，一块块径向砖沿弧线转向券顶。')
        front=camera((8.2,-28.6,3.82),(8.42,.18,3.10))
        r=projected_box(front,(-.23,17.18),(-.12,.46),(-.05,6.55))
        render(sheet1,'whole arcade and terrace',args.full,front,r,(50,207,1380,407))
        x_min,_,x_max,_=frame(r,(1380,407))
        for i,(arch,n) in enumerate(zip(sections['arcades'],blocks)):
            point=front@[(arch['left']+arch['right'])/2,0.,2.6,1.]
            cx=50+1380*(point[0]/point[2]-x_min)/(x_max-x_min)
            label=f'第{("一","二","三","四")[i]}跨  ·  {n}块券砖'
            d.text((round(cx),628),label,font=font(23,'bold'),fill=INK,anchor='ma')
        d.line((50,686,1430,686),fill=RULE,width=2)
        write(d,(50,701),'券顶的扇形接缝',26,'bold')
        render(sheet1,'first arch radial joints',args.full,matrices['13'],[227,751,412,858],(50,754,365,216))
        write(d,(442,761),'前两跨的轮廓均有双照可读。',20)
        write(d,(442,804),'第三跨东侧下段被车辆遮挡。',20)
        write(d,(442,847),'第四跨仅西起券和部分栏杆入镜，',20)
        write(d,(442,882),'其余按同排砖距和弧线估计。',20)
        write(d,(850,701),'露台西端折回的六根栏杆',26,'bold')
        side=camera((-17.3,1.73,6.4),(.0,1.80,5.53))
        r=projected_box(side,(-.12,.24),(.24,3.78),(4.93,6.29))
        render(sheet1,'six west-return balusters',args.lod,side,r,(850,754,580,216))
        foot(d,'正面前三段各有七根瓶形栏杆；西侧折回的栏杆可在2020年双照中数出六根。图中建筑与砖纹均取自原创模型。')
        sheet1.save(args.out/'garden-four-arches.png',optimize=True)

        sheet2,d=sheet('由砖券看廊后门窗','沿庭院看入，原照13的左门带上亮，中窗显出左缘。换到图8机位，可从另一券洞看见中窗右缘。')
        write(d,(50,205),'图13机位  ·  西门与浅色封板',25,'bold')
        render(sheet2,'figure13 two doors behind two arches',args.full,matrices['13'],[124,817,745,1162],(50,257,674,399))
        write(d,(759,205),'图8机位  ·  中窗的另一半',25,'bold')
        render(sheet2,'figure8 central framed window',args.full,matrices['8'],[36,494,466,700],(759,257,671,399))
        d.line((50,680,1430,680),fill=RULE,width=2)
        write(d,(50,697),'廊后墙平面与可见门口',26,'bold')
        x0,y0=90,917;scale=63
        def col(x):return round(x0+x*scale)
        def row(y):return round(y0-y*29)
        d.line((col(0),row(0),col(10.7),row(0)),fill='#a36c53',width=7)
        arches=sections['arcades']
        piers=[(0,arches[0]['left'])]+[(west['right'],east['left']) for west,east in zip(arches[:2],arches[1:3])]
        for l,r in piers:
            d.rectangle((col(l),row(sections['arcade_depth_m']),col(r),row(0)),fill='#a36c53')
        for l,r in [(0,1.17),(3.09,4.68),(6.58,8.16),(10.23,10.70)]:
            d.rectangle((col(l),row(4.2),col(r),row(3.72)),fill='#865d49')
        for l,r,y in [(1.17,3.09,3.75),(4.68,6.58,3.85),(8.43,10.14,4.13)]:
            d.line((col(l),row(y),col(r),row(y)),fill='#465555',width=4)
        for x,z in [(1.16,'深门'),(4.82,'中窗'),(8.54,'浅色封板')]:
            write(d,(col(x),742),z,20)
        write(d,(88,942),'庭院一侧　　平面示意，横向与进深非等比',18,'regular',GREY)
        write(d,(818,732),'两扇门分别用各自竖梃在两照中的位置定位。',21)
        write(d,(818,784),'西门东梃约3.73米，右侧浅板西缘约4.17米。',21)
        write(d,(818,836),'以廊前砖面为起点。中窗退口按两侧可见轮廓估计。',19)
        write(d,(818,888),'浅板高度采用图13，图8中板上深色部分较高。',19)
        foot(d,'机位取蒂芬格恩2020年发表的园侧照片。参考上海静安2024年外侧报道。门扇和玻璃的颜色由模型材质绘出。')
        sheet2.save(args.out/'garden-porch-doorways.png',optimize=True)
    names=['garden-four-arches.png','garden-porch-doorways.png']
    receipt={'parts_masonry_blocks':blocks,'front_counts':rails['visible_first_three_spans'],'west_return_count':rails['west_return']['count'],
             'images':{n:sha(args.out/n) for n in names},'inputs':{'full':sha(args.full),'lod':sha(args.lod)},
             'measurements':{p.name:sha(p) for p in (section_file,camera_file,back_file)},
             'renderer':{p.name:sha(p) for p in (Path(__file__),HERE/'photo_glb_raster.c',HERE/'photo_glb_raster.py')},'panels':panels}
    (args.out/'arcade-board-render.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(receipt['images'])


if __name__=='__main__':
    main()
