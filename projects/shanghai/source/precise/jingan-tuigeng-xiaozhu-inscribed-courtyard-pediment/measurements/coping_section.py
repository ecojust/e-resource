"""Read the real centre cross section of each delivered GLB and draw it at equal axis scales."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union
from PIL import Image, ImageDraw, ImageFont
here=Path(__file__).resolve().parent
project=next((p for p in here.parents if (p/'source/precise/hongkou-general-post-office').is_dir()),None)
if project is None:
    import os
    project=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(project/'source/precise/jingan-jiaozhou-450-garden-residence/measurements'))
from photo_glb_raster import read_glb

def section(mesh):
    parts,mats,_=read_glb(mesh)
    plane_x=0.00073
    outlines={}
    for vertices,_,__,indices,material,___ in parts:
        name=mats[material]['name']
        polys=vertices[indices.reshape(-1,3)].astype(np.float64)
        linework=outlines.setdefault(name,[])
        for triangle in polys[(polys[:,:,0].min(1)<plane_x)&(polys[:,:,0].max(1)>plane_x)]:
            yz=[]
            for p,q in zip(triangle,np.roll(triangle,-1,axis=0)):
                if (p[0]-plane_x)*(q[0]-plane_x)<0:
                    hit=p+(q-p)*((plane_x-p[0])/(q[0]-p[0]))
                    yz.append(tuple(round(float(v),6) for v in hit[1:]))
            if len(yz)==2 and yz[0]!=yz[1]:linework.append(LineString(yz))
    result={}
    for material,lines in outlines.items():
        if lines:
            faces=sorted(polygonize(unary_union(lines)),key=lambda p:-p.area)
            if not faces:raise ValueError(f'open section for {material}')
            result[material]=[dict(area_m2=round(p.area,7),loop=[list(i) for i in p.exterior.coords])for p in faces]
    crest=max(result['Cast stone | rounded arc moulding'],key=lambda x:max(p[1] for p in x['loop']))
    yz=np.array(crest['loop'])
    return dict(mesh=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),cut_x_m=plane_x,crest_depth_m=round(float(np.ptp(yz[:,0])),5),crest_height_m=round(float(np.ptp(yz[:,1])),5),profiles=result)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('meshes',nargs='+',type=Path)
    ap.add_argument('--board',type=Path,required=True)
    args=ap.parse_args()
    views=[section(p)for p in args.meshes]
    image=Image.new('RGB',(1112,750),'#f4efe5')
    draw=ImageDraw.Draw(image)
    def label(x,y,s,px,color='#322e27'):
        font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',px,index=2)
        draw.text((x,y),s,font=font,fill=color)
    label(40,24,'二进院墙弧檐 · 中央竖剖面',36)
    label(41,91,'两档成品沿同一竖面取交线。左侧朝院，右侧入墙。',21)
    def draw_section(v,anchor):
        loops=v['profiles']
        crest=max(loops['Cast stone | rounded arc moulding'],key=lambda x:max(z for _,z in x['loop']))
        peak=max(z for _,z in crest['loop']);scale=530
        def point(y,z):return int(anchor+(y+.14)*scale),int(192+(peak-z)*scale)
        for line in loops['Lime plaster | buff-grey wall']:
            draw.polygon([point(*p)for p in line['loop']],fill='#d4c7ae',outline='#655b49')
        draw.polygon([point(*p) for p in crest['loop']],fill='#ab9775',outline='#413a2d',width=3)
        low=min(z for _,z in crest['loop']);ref=point(.20,low)[1]
        draw.line((anchor,ref,anchor+88,ref),fill='#705c42',width=1)
        return crest
    draw_section(views[1],53);draw_section(views[-1],595)
    draw.rectangle((0,541,1111,750),fill='#f4efe5')
    for x,key,title in [(53,1,'近景'),(595,-1,'远景')]:
        v=views[key]
        label(x,545,title,24)
        label(x,587,f"截面深 {100*v['crest_depth_m']:.1f} 厘米　高 {100*v['crest_height_m']:.1f} 厘米",18)
        draw.line((x,646,x+53,646),fill='#4c453a',width=3)
        draw.line((x,639,x,653),fill='#4c453a',width=2)
        draw.line((x+53,639,x+53,653),fill='#4c453a',width=2)
        label(x+67,628,'模型 10 厘米',17)
    label(53,701,'相邻层以原照轮廓约束。檐口进深和墙厚为构造估计；图中尺寸基于题面宽 1.80 米的模型比例。',17)
    image.save(args.board,optimize=True)
    args.board.with_suffix('.json').write_text(json.dumps(dict(measure='metric section through delivered triangles',tablet_width_model_m=1.80,site_dimension_observed=False,sections=views,board_sha256=hashlib.sha256(args.board.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
