"""Create the window identification plate from the photographed building's own mesh."""
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from check_postal_windows import read_mesh, FIXED,BAR,GREY,SHADE,SKY,HERE

TEXT=(31,42,44);MUTED=(73,88,88);TEAL=(30,86,86);PAPER=(250,249,245);BORDER=(203,204,195)
def font(size,bold=False):
    family='Bold' if bold else 'Regular'
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+family+'.ttc',size,index=2)


def panel(tri,idx,names,op,side,scale):
    l,r,b,t=[op[k]for k in ('x0','x1','z0','z1')];width,height=r-l,t-b
    pad=12;nx=round(width*scale)+2*pad;ny=round(height*scale)+2*pad
    vals=np.full((ny,nx,3),[236,233,224],np.uint8);depth=np.full((ny,nx),np.inf)
    colors={FIXED:(54,62,58),BAR:(60,72,67),GREY:(124,141,139),SHADE:(89,99,94),SKY:(128,158,164)}
    for mat,color in colors.items():
        tt=tri[idx==names.index(mat)]
        lower,upper=tt.min(axis=1),tt.max(axis=1)
        keep=(lower[:,0]>=l-.003)&(upper[:,0]<=r+.003)&(lower[:,2]>=b-.003)&(upper[:,2]<=t+.003)&(lower[:,1]>.0)&(upper[:,1]<1)
        for xyz in tt[keep]:
            px=pad+(xyz[:,0]-l)*scale;py=pad+(t-xyz[:,2])*scale
            x0=max(0,int(np.floor(px.min())));x1=min(nx,int(np.ceil(px.max()))+1)
            y0=max(0,int(np.floor(py.min())));y1=min(ny,int(np.ceil(py.max()))+1)
            x,y=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
            det=(px[1]-px[0])*(py[2]-py[0])-(py[1]-py[0])*(px[2]-px[0])
            if abs(det)<1e-12:continue
            u=((x-px[0])*(py[2]-py[0])-(y-py[0])*(px[2]-px[0]))/det
            v=((y-py[0])*(px[1]-px[0])-(x-px[0])*(py[1]-py[0]))/det
            z=xyz[0,1]+u*(xyz[1,1]-xyz[0,1])+v*(xyz[2,1]-xyz[0,1])
            local=depth[y0:y1,x0:x1];valid=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(z<local)
            local[valid]=z[valid]
            vals[y0:y1,x0:x1][valid]=color
    assert np.isfinite(depth).sum()>scale*scale*.5,op['id']
    return Image.fromarray(vals)


def main():
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    tri,idx,names,_,digest=read_mesh(args.model)
    wall=json.loads((HERE/'west-front-masonry.json').read_bytes())
    opwest=json.loads((HERE/'west-front-openings.json').read_bytes())['openings']
    ops={r['id']:r for r in opwest+wall['south_windows']}
    end=tri[:,:,[1,0,2]].copy();end[:,:,1]=wall['south_return_x_m']-end[:,:,1]
    entries=[('central-2','二层门上窗','三光，两根内竖梃'),('central-3','三层门上窗','四光，三根内竖梃'),
             ('end-A-3','A 窗 · 三层','双光，设一道内竖梃'),('end-B-3','B 窗 · 三层','单光，上下各一整片'),('end-C-3','C 窗 · 三层','双光，设一道内竖梃')]
    im=Image.new('RGB',(1600,747),PAPER);d=ImageDraw.Draw(im)
    d.text((47,26),'交通部邮政总局驻沪办事处',font=font(40,True),fill=TEXT)
    d.text((49,90),'胶州路322号　｜　西立面门上宽窗与南端院墙三列窗',font=font(24),fill=MUTED)
    d.line((48,147,1552,147),fill=BORDER,width=2)
    for x0,x1,label in [(48,636,'临街西立面'),(670,1551,'南端院墙')]:
        d.text((x0,162),label,font=font(23,True),fill=TEAL);d.line((x0,210,x1,210),fill=TEAL,width=2)
    boxes=[(48,330),(353,636),(670,949),(970,1248),(1271,1551)]
    scale=134
    for i,(k,title,note) in enumerate(entries):
        op=ops[k];l,r=boxes[i];pic=panel(tri if i<2 else end,idx,names,op,i>=2,scale)
        d.rectangle((l,230,r,558),fill=(236,233,224));im.paste(pic,((l+r-pic.width)//2,541-pic.height))
        d.text((l,573),title,font=font(23,True),fill=TEXT)
        d.text((l,614),note,font=font(19),fill=MUTED)
        d.text((l,648),f"{op['x1']-op['x0']:.2f} × {op['z1']-op['z0']:.2f} m",font=font(17),fill=MUTED)
    d.line((48,695,1552,695),fill=BORDER)
    d.text((48,705),'实模正投影，五扇同一比例。洞净宽 × 净高，单位米。框梃取自三维实体，玻璃以统一色块区分。',font=font(16),fill=MUTED)
    args.output.parent.mkdir(parents=True,exist_ok=True);im.save(args.output,quality=93,subsampling=0)
    print(args.model.name,digest,args.output.name)

if __name__=='__main__':main()
