"""Draw the reconstructed garden storefront through its two registered photographic projections."""
import argparse
import json
from pathlib import Path
import runpy
import numpy as np
from PIL import Image,ImageDraw,ImageFont

folder=Path(__file__).parent
methods=runpy.run_path(str(folder/'south-garden-check.py'))
SerialScene=methods['SerialScene']
COLOR={'cream roughcast':(213,208,184),'dressed pale stone':(193,184,157),'light soffit':(223,221,204),
       'grey streaked balcony facing':(158,157,146),'pale shop awning':(232,230,212),'cast iron':(66,69,65),
       'south shop glazing':(150,121,79),'south timber door glazing':(79,67,49),'oak entrance door':(74,63,50),
       'steel sash':(58,59,56),'weathered interlocking clay tiles':(157,91,64),'flushed red brick':(163,94,75),
       'dark gable timber':(78,60,54),'interior reveal':(48,46,42),'sandstone paving':(169,166,149),
       'shaded window glass':(86,100,103)}


def panel(scene,P,rectangle,frame):
    x0,y0,x1,y1=rectangle;w,h=frame
    eye=-np.linalg.solve(P[:,:3],P[:,3])
    tris=scene.tri
    uvh=tris@P[:,:3].T+P[:,3];uv=uvh[:,:,:2]/np.maximum(1e-8,uvh[:,:,2:])
    inside=(uvh[:,:,2]>.01).all(axis=1)&(uv[:,:,0].min(axis=1)<x1)&(uv[:,:,0].max(axis=1)>x0)&(uv[:,:,1].min(axis=1)<y1)&(uv[:,:,1].max(axis=1)>y0)
    ids=np.flatnonzero(inside)
    uv=uv*np.array([w/(x1-x0),h/(y1-y0)])-np.array([w*x0/(x1-x0),h*y0/(y1-y0)])
    frame=np.full((h,w,3),(225,226,222),dtype=np.uint8)
    depth=np.zeros((h,w))
    normal=scene.cross/np.maximum(np.linalg.norm(scene.cross,axis=1)[:,None],1e-12)
    light=np.array([-.45,.40,.80]);light/=np.linalg.norm(light)
    intensity=np.clip(.83+.19*(normal@light),.67,1.08)
    colors=np.array([COLOR.get(name.split('|')[-1].strip(),(140,136,125)) for name in scene.materials])
    tint=(colors[scene.mi]*intensity[:,None]).clip(0,255).astype(int)
    # The canopy, glazing and frames stand centimetres apart. A per-pixel depth
    # buffer preserves their order even when two long triangles intersect in projection.
    for i in ids:
        triangle=uv[i]
        xlo,ylo=np.maximum(np.floor(triangle.min(axis=0)).astype(int),0)
        xhi,yhi=np.minimum(np.ceil(triangle.max(axis=0)).astype(int),[w-1,h-1])
        if xhi<xlo or yhi<ylo:continue
        (x0,y0),(x1,y1),(x2,y2)=triangle
        det=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
        if abs(det)<1e-7:continue
        x=np.arange(xlo,xhi+1)[None,:]+.5
        y=np.arange(ylo,yhi+1)[:,None]+.5
        l0=((y1-y2)*(x-x2)+(x2-x1)*(y-y2))/det
        l1=((y2-y0)*(x-x2)+(x0-x2)*(y-y2))/det
        l2=1-l0-l1
        inverse=l0/uvh[i,0,2]+l1/uvh[i,1,2]+l2/uvh[i,2,2]
        buffer=depth[ylo:yhi+1,xlo:xhi+1]
        visible=(l0>=-1e-9)&(l1>=-1e-9)&(l2>=-1e-9)&(inverse>buffer)
        buffer[visible]=inverse[visible]
        frame[ylo:yhi+1,xlo:xhi+1][visible]=tint[i]
    return Image.fromarray(frame)


def main():
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('results',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();scene=SerialScene(args.mesh)
    data=json.loads((folder/'south-garden-two-photographs.json').read_bytes())
    results=json.loads(args.results.read_bytes())['reads'][args.mesh.name]['cameras']
    out=Image.new('RGB',(1216,840),(246,245,241));d=ImageDraw.Draw(out)
    font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    large=ImageFont.truetype(font,34,index=2);body=ImageFont.truetype(font,20,index=2);small=ImageFont.truetype(font,16,index=2)
    d.text((35,19),'武夷路174号　南园弧形阳台与折面玻璃',font=large,fill=(35,37,33))
    d.text((38,74),'2024年10月两幅照片的机位，投影为自主重建的模型。',font=body,fill=(70,70,62))
    views=[('8',(45,35,1000,1175),451,538,38,134),('0',(386,151,701,417),641,541,535,132)]
    for n,rect,w,h,x,y in views:
        P=methods['matrix'](data['views'][n]['camera_coefficients'])
        img=panel(scene,P,rect,(w*2,h*2)).resize((w,h),Image.Resampling.LANCZOS);out.paste(img,(x,y))
        d.rectangle([x,y,x+w,y+h],outline=(90,88,80))
        for row in results[n]['probes']:
            px,py=row['uv'];sx=x+(px-rect[0])*w/(rect[2]-rect[0]);sy=y+(py-rect[1])*h/(rect[3]-rect[1])
            col=(40,142,126) if row['matches'] else (185,65,43)
            d.ellipse((sx-3.5,sy-3.5,sx+3.5,sy+3.5),outline=col,width=2)
        label=('近正面 08' if n=='8' else '园门远视 00')+'　原像素首交 '+str(results[n]['matched'])+'/'+str(results[n]['count'])
        d.text((x,y+h+14),label,font=body,fill=(44,47,40))
    d.text((38,754),'青圈为原点命中标注材质。红圈保留偏差，细铁栏及钢梃另有邻近可见位置的距离记录。',font=small,fill=(44,48,42))
    d.text((38,790),'屋面首交与门后墙厚独立检查。图中文字和几何投影均为本项目制作。',font=small,fill=(75,78,70))
    out.save(args.output,quality=89,optimize=True)

if __name__=='__main__':main()
