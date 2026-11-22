"""Create an original public plate from the warehouse and the two actual component meshes."""
from pathlib import Path
import argparse,sys,json
from PIL import Image,ImageDraw,ImageFont
import numpy as np
from roof_flagstaff import STEEL,STONE

def font(n,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold' if bold else 'Regular')+'.ttc',n,index=2)

def panel(parts,target,eye,width,height,scale):
    # Orthographic ENU projection, painter sorted at twice display resolution.
    im=Image.new('RGB',(2*width,2*height),'#e8e7e1');d=ImageDraw.Draw(im)
    facing=np.asarray(eye,float);facing/=np.linalg.norm(facing)
    right=np.cross([0,0,1],facing);right/=np.linalg.norm(right);up=np.cross(facing,right)
    lamp=np.array([.29,-.56,.78]);lamp/=np.linalg.norm(lamp)
    allfaces=[]
    for vertices,col,style in parts:
        delta=vertices-np.asarray(target)
        depths=np.mean(delta@facing,axis=1)
        normal=np.cross(vertices[:,1]-vertices[:,0],vertices[:,2]-vertices[:,0])
        lengths=np.linalg.norm(normal,axis=1);mask=(normal@facing>1e-11)&(lengths>1e-12)
        for tr,dep,n in zip(delta[mask],depths[mask],normal[mask]/lengths[mask,None]):
            xy=np.stack([width+2*scale*(tr@right),height-2*scale*(tr@up)],axis=-1)
            if xy[:,0].max()<0 or xy[:,0].min()>2*width or xy[:,1].max()<0 or xy[:,1].min()>2*height:continue
            intensity=.69+.31*max(0,float(n@lamp))
            color=tuple(min(255,int(v*intensity)) for v in col)
            allfaces.append((dep,xy,color))
    for dep,xy,color in sorted(allfaces,key=lambda a:a[0]):
        d.polygon([tuple(v) for v in xy],fill=color)
    return im.resize((width,height),Image.Resampling.LANCZOS)

def render(project,mesh,house,out):
    sys.path.insert(0,str(project/'source/precise/xuhui-pathe-records-office/measurements/city-contact'))
    from glb_triangles import load_triangles
    t,m,l,_=load_triangles(mesh)
    pole=t[m==l.index(STEEL)];foot=t[m==l.index(STONE)]
    alltri,_,_,_=load_triangles(house)
    c=alltri.mean(1)
    selected=(c[:,0]>-6.6)&(c[:,0]<6.6)&(c[:,1]>-3)&(c[:,1]<2.0)&(c[:,2]>15.6)
    model=[(pole,(151,164,165),'shaft'),(foot,(191,185,169),'block')]
    context=[(alltri[selected],(209,208,197),'frontage context'),*model]
    sheet=Image.new('RGB',(1450,980),'#f4f1ea');d=ImageDraw.Draw(sheet)
    def txt(x,y,s,n,fg='#273b3d',bold=False):d.text((x,y),s,font=font(n,bold),fill=fg)
    txt(42,14,'原交通银行仓库的屋顶旗杆',42,bold=True)
    txt(44,85,'光复路195号南露台   ·   修缮后实物   ·   中央门洞中线向楼内约1米',22)
    d.line((42,138,1406,138),fill='#8ca29a',width=2)
    view=panel(context,[0,.58,22.23],[1,2,.12],712,640,56)
    sheet.paste(view,(42,154))
    txt(62,169,'临河中央山墙及其后的旗杆',21)
    d.line((128,215,128,506),fill='#3e6d69',width=2);d.line((120,215,139,215),fill='#3e6d69',width=2);d.line((120,506,139,506),fill='#3e6d69',width=2)
    txt(145,210,'杆顶约27.0米',18)
    txt(145,479,'正面山墙顶约21.84米',17)
    txt(777,157,'杆脚局部',26,bold=True)
    inset=panel(model,[-.06,1.07,18.50],[1,-1.7,.80],604,304,790)
    sheet.paste(inset,(777,207))
    txt(777,522,'图38与39可见杆脚小块的明暗边界。',19)
    txt(777,562,'近景将小块画为0.40 × 0.32米，厚0.20米。',18)
    txt(777,597,'两幅图均有遮挡，宽深和厚度为示意尺寸。',18)
    d.line((777,660,1390,660),fill='#b2beb9')
    txt(777,675,'两处独立机位的杆顶测量',22,bold=True)
    txt(777,723,'临河斜照（图34）　27.08米',21)
    txt(777,763,'屋面侧照（图39）　26.83米',21)
    txt(42,806,'照片约束',24,bold=True)
    txt(43,853,'正照图16显示杆身与中央山墙对中。由图34、39读得杆顶约26.5—27.5米；模型取27.00米。',20)
    txt(43,896,'图38原相机在细杆顶处有21像素的纵向残差。两处金属断面和杆脚尺寸均为外观近似。',18)
    sheet.save(out,quality=93,optimize=True,subsampling=0)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['project','mesh','house','output']:p.add_argument(key,type=Path)
    a=p.parse_args();render(a.project,a.mesh,a.house,a.output)
