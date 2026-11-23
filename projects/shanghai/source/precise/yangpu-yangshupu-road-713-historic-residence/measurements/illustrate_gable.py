"""Compare a licensed 2015 photograph with a rendering of the actual GLB in its image chart."""
from pathlib import Path
import argparse,hashlib,json,math,runpy,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import distance_transform_edt,binary_erosion
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import PROJECT
from ornament_chart import P
from finishes import BRICK,STONE,RED,DARK_RED,METAL,BACK
COLOURS={BRICK:(155,76,58),STONE:(179,178,169),RED:(177,75,55),DARK_RED:(119,49,41),METAL:(85,85,80),BACK:(37,34,33)}
FONT=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
FONT_BOLD=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc')
def font(sz,heavy=False):
    return ImageFont.truetype(str(FONT_BOLD if heavy else FONT),sz,index=2)
def render(scene,crop,scale):
    xmin,ymin,xmax,ymax=crop;shape=(int((xmax-xmin)*scale),int((ymax-ymin)*scale))
    image=np.full((shape[1],shape[0],3),[230,226,216],dtype=np.uint8)
    labels=np.zeros(image.shape[:2],np.uint8);zbuffer=np.full(image.shape[:2],np.inf)
    tri=scene.tri;v=np.concatenate((tri,np.ones((*tri.shape[:-1],1))),axis=2)@P.T
    xy=(v[:,:,:2]/v[:,:,2:3]-[xmin,ymin])*scale
    normals=scene.cross/(2*scene.areas[:,None]);light=np.array([-.36,-.68,.64])
    textures={mat:np.asarray(Image.open(HERE.parent/'source'/file)) for mat,file in [(BRICK,'facing-brick.png'),(STONE,'warm-grey-stone.png')]}
    for j,points in enumerate(xy):
        x0,y0=np.maximum(np.floor(points.min(0)).astype(int),0)
        x1,y1=np.minimum(np.ceil(points.max(0)).astype(int)+1,shape)
        if x0>=x1 or y0>=y1:continue
        a,b,c=points
        det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det)<1e-10:continue
        yy,xx=np.mgrid[y0:y1,x0:x1];xx=xx+.5-c[0];yy=yy+.5-c[1]
        w1=((b[1]-c[1])*xx+(c[0]-b[0])*yy)/det
        w2=((c[1]-a[1])*xx+(a[0]-c[0])*yy)/det
        w3=1-w1-w2;world_w=np.stack((w1,w2,w3),axis=2)/v[j,:,2]
        depth=1./world_w.sum(2);z=zbuffer[y0:y1,x0:x1]
        valid=(np.minimum(np.minimum(w1,w2),w3)>-1e-6)&(depth<z)
        if not np.any(valid):continue
        z[valid]=depth[valid];n=normals[j];mat=scene.materials[scene.mi[j]]
        col=np.asarray(COLOURS[mat]);factor=.79+.25*max(0,float(n@light))
        if mat in textures:
            pos=(world_w[valid]*depth[valid,None])@tri[j]
            if abs(n[2])>.9:tangent=np.array([1.,0.,0.]);up=np.array([0.,1.,0.])
            else:
                tangent=np.array([-n[1],n[0],0.]);tangent/=np.linalg.norm(tangent);up=np.cross(n,tangent)
            period=(1.92,1.056) if mat==BRICK else (.83,.83)
            u,vv=(pos@tangent)/period[0],(pos@up)/period[1]
            tex=textures[mat];th,tw=tex.shape[:2]
            col=tex[((vv%1)*th).astype(int)%th,((u%1)*tw).astype(int)%tw]
        image[y0:y1,x0:x1][valid]=(col*factor).clip(0,255).astype(np.uint8)
        labels[y0:y1,x0:x1][valid]=1+list(COLOURS).index(mat)
    return Image.fromarray(image),labels
def main(photo,model,out,marks):
    assert hashlib.sha256(photo.read_bytes()).hexdigest()=='050cf49f380c8e19fd67397519ee6ddff5d6767d392e8ab659e6a2594a2f3e45'
    scene=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](model)
    orig=Image.open(photo)
    board=Image.new('RGB',(1440,923),(247,244,236));d=ImageDraw.Draw(board)
    d.text((34,24),'杨树浦路713号住宅的红砖山花',font=font(36,True),fill='#332d25')
    d.text((36,86),'左列为2015年照片局部，右列为同照点投影的实网表面。',font=font(21),fill='#685348')
    for k,(crop,scale,label,y,height) in enumerate([((626,504,990,696),1.82,'双坡线脚与右端折头',144,350),
                     ((752,507,818,560),3.65,'半圆顶饰与底座',547,194),((756,590,801,641),3.65,'四键石圈与百叶',547,187)]):
        r,_=render(scene,crop,scale);img=orig.crop(crop).resize(r.size,Image.Resampling.LANCZOS)
        if k==0:
            board.paste(img,(35,y));board.paste(r,(740,y))
            d.text((36,y+height+4),'Fayhoo · 2015-04-06',font=font(19),fill='#714f3d')
            d.text((741,y+height+4),'山花实网 · '+label,font=font(19),fill='#714f3d')
        else:
            x=35+(k-1)*715;board.paste(img,(x,y));board.paste(r,(x+r.width+12,y))
            d.text((x,y+height+4),label,font=font(21,True),fill='#554538')
    d.text((35,815),'斜拍可读半圆正面、右缘厚度和石圈四处凸饰。电线、树枝及遮住山花左脚的前景栏杆可在原照中辨出。',font=font(19),fill='#504942')
    d.text((35,860),'摄影 Fayhoo / Wikimedia Commons，CC BY-SA 3.0。照片裁切、缩放和本对照图按同许可共享。模型与程序纹理为原创。',font=font(18),fill='#655f57')
    board.save(out,quality=91,optimize=True)
    crop=(620,500,985,691);scale=4;_,mask=render(scene,crop,scale)
    ext=mask>0;dist=distance_transform_edt(~(ext & ~binary_erosion(ext))) /scale
    stone=mask==2;dk=distance_transform_edt(~(stone & ~binary_erosion(stone)))/scale
    evidence=json.loads((HERE/'independent-ornament-lines.json').read_text());data=[]
    for name,pts in evidence['marks_in_crop_pixels'].items():
        for u,v in pts:
            x,y=(400+u-crop[0])*scale,(475+v-crop[1])*scale
            data.append(dict(part=name,uv_original=[400+u,475+v],visible_stone_edge_px=round(float(dk[y,x]),2),silhouette_px=round(float(dist[y,x]),2)))
    marks.write_text(json.dumps(dict(source_file=model.name,sha256=hashlib.sha256(model.read_bytes()).hexdigest(),notes='Distances to actual projected grey-detail edges and to the exterior silhouette. Base and ventilator are interior features. Wires and hidden faces are excluded.',points=data),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('photo','glb','output','measurements'):p.add_argument(n,type=Path)
    a=p.parse_args();main(a.photo,a.glb,a.output,a.measurements)
