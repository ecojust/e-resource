"""Rectify Fayhoo's licensed photo and project the actual carved surface at the same scale."""
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles
COLOURS={'Wujin | red relief ground':(135,71,54),'Wujin | carved brick':(158,80,58),
         'Wujin | raised leaf face':(161,83,60)}

def project(path,row,size):
    triangles,indices,names,source=load_triangles(path)
    w,h=size;span=row['x1']-row['x0'];ht=row['z1']-row['z0']
    zbuf=np.full((h,w),np.inf);pixels=np.empty((h,w,3));pixels[:]=[120,67,52]
    light=np.array([-.39,-.57,.72]);light/=np.linalg.norm(light)
    used=0
    for i,material in enumerate(names):
        if material not in COLOURS:continue
        selected=triangles[indices==i];used+=len(selected)
        points=selected.copy();points[:,:,0]=(selected[:,:,0]-row['x0'])*w/span
        points[:,:,1]=(row['z1']-selected[:,:,2])*h/ht;points[:,:,2]=selected[:,:,1]
        normals=np.cross(selected[:,1]-selected[:,0],selected[:,2]-selected[:,0])
        normals/=np.linalg.norm(normals,axis=1)[:,None].clip(1e-22)
        tones=(.53+.83*np.maximum(0,normals@light))[:,None]*np.array(COLOURS[material])
        for tri,normal,colour in zip(points,normals,tones):
            if normal[1]>=-1e-7:continue
            (x,y,z),(s,t,u),(v,q,r)=tri
            x0=max(0,int(np.floor(min(x,s,v))));x1=min(w-1,int(np.ceil(max(x,s,v))))
            y0=max(0,int(np.floor(min(y,t,q))));y1=min(h-1,int(np.ceil(max(y,t,q))))
            det=(t-q)*(x-v)+(v-s)*(y-q)
            if abs(det)<1e-9 or x0>x1 or y0>y1:continue
            Y,X=np.ogrid[y0:y1+1,x0:x1+1];X=X+.5;Y=Y+.5
            a=((t-q)*(X-v)+(v-s)*(Y-q))/det;b=((q-y)*(X-v)+(x-v)*(Y-q))/det
            depth=a*z+b*u+(1-a-b)*r;interval=zbuf[y0:y1+1,x0:x1+1]
            inside=(a>=0)&(b>=0)&(a+b<=1)&(depth<interval)
            interval[inside]=depth[inside];pixels[y0:y1+1,x0:x1+1][inside]=colour
    if not used:raise ValueError('No acanthus triangles in the supplied model')
    # One shadow test per visible pixel, stepped towards the directional light.
    shadow=np.zeros_like(zbuf,dtype=bool);valid=np.isfinite(zbuf)
    for offset in range(2,max(6,round(.07*w)),2):
        dx=-round(.48*offset);dy=-offset
        if dy<=-h or dx<=-w:break
        bottom=zbuf[-dy:,-dx:];block=zbuf[:h+dy,:w+dx]
        shadow[-dy:,-dx:] |= block < bottom-offset*(ht/h)*.66-.0005*span
    pixels[shadow&valid]*=.70
    return Image.fromarray(np.uint8(np.clip(pixels,0,255))),source,used

def board(photo,model,row,output):
    notes=json.loads((HERE/'acanthus-photographs.json').read_bytes());source=notes['primary']
    check=hashlib.sha256(photo.read_bytes()).hexdigest()
    if check!=source['file_sha256']:raise ValueError('Expected the credited original photograph')
    width=630;h=max(170,round(width*(row['z1']-row['z0'])/(row['x1']-row['x0'])))
    H=np.asarray(source['metric_rectangle_to_original'])@np.diag([720/width,370/h,1])
    i=Image.open(photo).convert('RGB').transform((width,h),Image.Transform.PERSPECTIVE,tuple((H/H[2,2]).ravel()[:8]),Image.Resampling.BICUBIC)
    rendered,scene,used=project(model,row,(width,h))
    canvas=Image.new('RGB',(1340,h+224),(247,244,237));d=ImageDraw.Draw(canvas)
    def font(size,bold=False):
        name='NotoSansCJK-'+('Bold.ttc' if bold else 'Regular.ttc')
        return ImageFont.truetype('/usr/share/fonts/opentype/noto/'+name,size,index=2)
    d.text((30,14),'武进路225弄住宅山墙的卷草砖雕',font=font(35,True),fill=(56,38,32))
    d.text((32,67),'2016年实照局部 · 按砖墙平面校正透视',font=font(21),fill=(76,58,49))
    d.text((673,67),'实网正投影 · 左上方照明',font=font(21),fill=(76,58,49))
    canvas.paste(i,(32,110));canvas.paste(rendered,(675,110))
    d.text((32,h+123),'四个上卷、四个下卷和中央扇叶可逐一对照。原照片保留画面中的细线。',
           font=font(20),fill=(61,48,41))
    d.text((32,h+164),'照片与本对照图按 CC BY-SA 3.0 许可使用。摄影：Fayhoo，2016-02-09，Wikimedia Commons。',
           font=font(17),fill=(92,74,63))
    canvas.save(output,quality=93)
    output.with_suffix('.json').write_text(json.dumps(dict(model=scene,projected_triangles=used,
        input_photograph_sha256=check,photograph=source['source'],license=source['license'],
        model_panel_metric_rectangle=row,projection='model true orthographic and matching photo-plane rectification',
        comparison_board_sha256=hashlib.sha256(output.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for field in ('photo','model','row','output'):p.add_argument(field,type=Path)
    a=p.parse_args();board(a.photo,a.model,json.loads(a.row.read_bytes()),a.output)
