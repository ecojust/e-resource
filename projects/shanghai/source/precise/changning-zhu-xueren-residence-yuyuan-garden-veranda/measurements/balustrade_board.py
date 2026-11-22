"""Draw the actual decoded railing meshes together with the 2013 profile measurements."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import load_triangles
COLORS={
 'Veranda | pale turned stone':(221,217,202),
 'Veranda | weathered stone coping':(185,181,163),
 'Veranda | warm dressed stone':(215,201,174),
 'Veranda | blue-grey plinth':(137,142,142),
}
def font(n,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSerifCJK-'+('Bold'if bold else'Regular')+'.ttc',n,index=2)

def picture(canvas,tri,mi,names,rect,keep,facing,window):
    mean=tri.mean(axis=1)
    good=np.array([name in COLORS for name in names],bool)[mi]&keep(mean)
    selected=tri[good];indices=mi[good]
    right=np.asarray(facing[0]);up=np.asarray(facing[1]);view=np.cross(right,up)
    projected=np.stack((selected@right,-selected@up),axis=2)
    xmin,ymin,xmax,ymax=window
    width,height=rect[2]-rect[0],rect[3]-rect[1];s=min(width/(xmax-xmin),height/(ymax-ymin))
    px=(projected-[xmin,ymin])*s+[(width-(xmax-xmin)*s)/2,(height-(ymax-ymin)*s)/2]
    normals=np.cross(selected[:,1]-selected[:,0],selected[:,2]-selected[:,0])
    length=np.linalg.norm(normals,axis=1);normals/=np.maximum(length,1e-8)[:,None]
    sun=np.array([-.34,-.65,.72]);sun/=np.linalg.norm(sun)
    light=np.clip(normals@sun,-.2,1)*.30+.76
    layer=Image.new('RGB',(width,height),'#485657');draw=ImageDraw.Draw(layer)
    for i in np.argsort(selected.mean(axis=1)@view):
        xy=[tuple(j) for j in px[i].round().astype(int)]
        rgb=np.clip(np.array(COLORS[names[indices[i]]])*light[i],0,255).astype(int)
        draw.polygon(xy,fill=tuple(rgb))
    canvas.paste(layer,(rect[0],rect[1]))


def draw(mesh,output):
    tri,mi,names,_=load_triangles(mesh)
    source=json.loads((HERE/'south-balustrade-photo-readings.json').read_bytes())
    img=Image.new('RGB',(1152,702),'#f5f1e8');d=ImageDraw.Draw(img)
    d.text((34,18),'朱学仁住宅南园栏杆',font=font(32,True),fill='#273736')
    d.text((35,69),'愚园路684号  ·  2013年9月南廊测绘',font=font(18),fill='#40544f')
    picture(img,tri,mi,names,(35,111,1117,400),lambda m:(m[:,2]>4.9)&(m[:,0]<18.3),([1,0,0],[0,0,1]),(-.1,-8.56,18.91,-4.96))
    d.text((42,405),'西段 7＋7',font=font(17,True),fill='#314540')
    d.text((487,405),'中央 3＋8＋3',font=font(17,True),fill='#314540')
    d.text((980,405),'东段 7＋7',font=font(17,True),fill='#314540')
    picture(img,tri,mi,names,(35,454,443,648),lambda m:(m[:,0]>13.3)&(m[:,0]<16.60)&(m[:,2]<2),([1,0,0],[0,0,1]),(13.45,-1.55,16.63,-.63))
    d.text((42,652),'东侧地层十瓶，中央通向弧阶。',font=font(16),fill='#314540')
    picture(img,tri,mi,names,(457,454,698,648),lambda m:(m[:,0]>18.5)&(m[:,2]<2),([0,1,0],[0,0,1]),(1.32,-1.5,2.32,-.67))
    d.text((460,652),'东端横栏四瓶',font=font(16),fill='#314540')
    pr=source['profile_11'];xc=779
    d.rectangle((711,454,1117,648),fill='#e8e2d3')
    xy=[(xc+r*.86,463+(y-699)*.91)for y,r in zip(pr['heights_y_px'],pr['visible_half_width_px'])]
    d.polygon(xy+[(2*xc-x,y)for x,y in xy[::-1]],fill='#546761')
    d.text((825,463),'图11原像轮廓',font=font(19,True),fill='#30423e')
    d.text((825,507),'双层鼓圈与收细的颈部',font=font(16),fill='#30423e')
    d.text((825,546),'方领、方脚与压顶石',font=font(16),fill='#30423e')
    d.text((825,590),'高参88摄影，据图量取',font=font(15),fill='#465850')
    img.save(output,quality=89,subsampling=0,optimize=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('image',type=Path)
    args=ap.parse_args();draw(args.mesh,args.image)
