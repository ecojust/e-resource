"""Place the licensed 2015 crop and a corresponding projection of the measured three arches on one plate."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles,material_appearance

CROP=(262,458,990,677)
SCALE=1.75
PAPER=(248,246,237)


def font(size,bold=False):
    family='Bold' if bold else 'Regular'
    return ImageFont.truetype(f'/usr/share/fonts/opentype/noto/NotoSansCJK-{family}.ttc',size,index=2)


def register_render(path,P,rect,scale):
    triangles,ids,names,asset=load_triangles(path)
    materials=material_appearance(path)['materials']
    select=np.isin(ids,[i for i,n in enumerate(names) if n.startswith(('Shanyin arch |','Shanyin sash |'))])
    if len(set(ids[select]))!=9:
        raise ValueError('The measured radial bricks, joints, casing, glazing bars and glass must all be present')
    tri,ids=triangles[select],ids[select]
    rgba=np.array([materials[n]['baseColorFactor'][:3] if n in materials else [1,1,1] for n in names])
    srgb=np.where(rgba<.0031308,12.92*rgba,1.055*np.maximum(0,rgba)**(1/2.4)-.055)*255.
    width=round((rect[2]-rect[0])*scale);height=round((rect[3]-rect[1])*scale)
    paper=np.full((height,width,3),PAPER,np.uint8)
    buffer=np.full((height,width),-np.inf)
    projected=tri@P[:,:3].T+P[:,3]
    image=(projected[:,:,:2]/projected[:,:,2,None]-rect[:2])*scale
    # The z-buffer stores reciprocal camera depth, linear after perspective projection.
    inv=1/projected[:,:,2]
    light=np.array([-.37,-.79,.49]);light=light/np.linalg.norm(light)
    camera=-np.linalg.solve(P[:,:3],P[:,3])
    normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    area=np.linalg.norm(normals,axis=1)
    normals=normals/np.maximum(area,1e-20)[:,None]
    alpha=np.clip(.78+.22*np.maximum(0.,normals@light),0,1)
    colors=np.clip(srgb[ids]*alpha[:,None],0,255).astype('uint8')
    visible=(area>1e-10)&(np.einsum('ij,ij->i',normals,camera-tri[:,0])>0)
    for t,q,color in zip(image[visible],inv[visible],colors[visible]):
        xmin,ymin=np.maximum(0,np.floor(t.min(axis=0)).astype(int))
        xmax,ymax=np.minimum((width,height),np.ceil(t.max(axis=0)).astype(int)+1)
        if xmin>=xmax or ymin>=ymax:continue
        xx,yy=np.arange(xmin,xmax)+.5,np.arange(ymin,ymax)[:,None]+.5
        ax,ay=t[0];bx,by=t[1];cx,cy=t[2]
        det=(bx-ax)*(cy-ay)-(cx-ax)*(by-ay)
        if abs(det)<1e-9:continue
        v=((xx-ax)*(cy-ay)-(cx-ax)*(yy-ay))/det
        k=((bx-ax)*(yy-ay)-(xx-ax)*(by-ay))/det
        value=q[0]+v*(q[1]-q[0])+k*(q[2]-q[0])
        buf=buffer[ymin:ymax,xmin:xmax]
        use=(v>=0)&(k>=0)&(v+k<=1)&(value>buf)
        buf[use]=value[use];paper[ymin:ymax,xmin:xmax][use]=color
    return Image.fromarray(paper),asset


def draw(model,layout_path,photo,output):
    layout=json.loads(layout_path.read_bytes())
    reference=json.loads((HERE/'three-fanlight-photograph.json').read_bytes())['source']
    if sha256(photo.read_bytes()).hexdigest()!=reference['sha256']:
        raise ValueError('The source must be the original Fayhoo photograph')
    mesh,asset=register_render(model,np.asarray(layout['camera_P']),CROP,SCALE)
    with Image.open(photo) as src:
        assert list(src.size)==reference['size']
        crop=src.convert('RGB').crop(CROP).resize(mesh.size,Image.Resampling.LANCZOS)
    left=54; width=mesh.width+2*left; height=mesh.height*2+325
    sheet=Image.new('RGB',(width,height),PAPER);d=ImageDraw.Draw(sheet)
    def title(x,y,t,size,bold=False,color='#363931'):
        d.text((x,y),t,font=font(size,bold),fill=color)
    title(left,22,'山阴路209弄　红砖圆券与扇形上亮',37,True)
    title(left,80,'2015年4月12日摄　上层三窗',20,True)
    sheet.paste(crop,(left,119));y=119+mesh.height
    d.line((left,y+18,width-left,y+18),fill='#c7c4b5',width=2)
    title(left,y+34,'同一画幅投影　砖券、白漆窗框与玻璃',20,True)
    sheet.paste(mesh,(left,y+76));y+=76+mesh.height
    d.line((left,y+14,width-left,y+14),fill='#c7c4b5',width=2)
    title(left,y+24,'中央小弧与三根放射窗条连接外弧。横框下四块玻璃宽度不等，三窗的分格各自取样。',20)
    title(left,y+62,'摄影 Fayhoo，2015。原作 Shanyinlu 209 Long Zhuzhai.JPG，Wikimedia Commons。上图裁切，未移除遮挡物。',15)
    title(left,y+87,'原照与本对照板采用 CC BY-SA 3.0。下图以本项目输出的三角网重投；色彩与纵深按照片估计。',15)
    title(left,y+111,'creativecommons.org/licenses/by-sa/3.0/     ·     commons.wikimedia.org/wiki/File:Shanyinlu_209_Long_Zhuzhai.JPG',12,color='#666a60')
    sheet.save(output,quality=90,subsampling=0,optimize=True)
    out=dict(file=output.name,sha256=sha256(output.read_bytes()).hexdigest(),source_mesh=asset,
             reference=reference,crop=list(CROP),native_image_size=reference['size'],uniform_scale=SCALE,
             method='Unaltered crop paired with a perspective projection of the arch and sash triangles using the registered wall camera. The original photograph includes temporary objects and foreground branches.',
             rendering='Flat original model materials with directional shading and a reciprocal-depth buffer.',
             license='CC BY-SA 3.0',license_url=reference['terms'])
    output.with_suffix('.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('model','layout','original_photo','output'):p.add_argument(key,type=Path)
    a=p.parse_args();result=draw(a.model,a.layout,a.original_photo,a.output);print(result['sha256'])
