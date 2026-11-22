"""Draw the released mesh, surveyed southern roof levels, and difference from the background footprint."""
from pathlib import Path
from argparse import ArgumentParser
from hashlib import sha256
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
M=Path(__file__).resolve().parent
sys.path.insert(0,str(M.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene, material_appearance

def print_board(path,output):
    scene=SerialScene(path);layout=json.loads((M/'west-front-masonry.json').read_text())
    openings=json.loads((M/'west-front-openings.json').read_text())['openings'];cal=json.loads((M/'west-courtyard-camera-registration.json').read_text())
    im=Image.new('RGB',(1270,850),'#f6f3eb');d=ImageDraw.Draw(im)
    regular='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
    fonts={}
    def tx(xy,t,size=18,b=False,color='#293c39'):
        p=(size,b)
        if p not in fonts:fonts[p]=ImageFont.truetype(bold if b else regular,size,index=2)
        d.text(xy,t,font=fonts[p],fill=color)
    tx((40,19),'胶州路邮政供应处',38,True);tx((42,75),'西立面与南端墙的影像测读',22);tx((875,32),'胶州路 320 号 / 现院门 322 号',21,True)
    tx((876,65),'第五批优秀历史建筑  5B057',17)
    d.line((40,112,1230,112),fill='#8b9b92',width=2)
    appearance=material_appearance(path)['materials']
    def sr(c):return 12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055
    def mesh(box,kind):
        left,top,right,bot=box;tile=Image.new('RGB',(right-left,bot-top),'#e8ece5');q=ImageDraw.Draw(tile);tri=scene.tri
        if kind=='west':axis=np.array([1.,0,0]);up=np.array([0,0,1.]);depth=np.array([0.,1,0]);mask=tri[:,:,1].mean(axis=1)<2.
        else:axis=np.array([0,1.,0]);up=np.array([0,0,1.]);depth=np.array([-1.,0,0]);mask=(tri[:,:,0].mean(axis=1)>1.1)&(tri[:,:,1].mean(axis=1)>-.4)
        idx=np.flatnonzero(mask);proj=tri[idx]@np.stack([axis,up]).T
        mn,mx=proj.min(axis=(0,1)),proj.max(axis=(0,1));scale=min((tile.width-30)/(mx[0]-mn[0]),(tile.height-16)/(mx[1]-mn[1]));e=(tile.width-scale*(mx[0]-mn[0]))/2
        pt=np.empty_like(proj);pt[:,:,0]=e+(proj[:,:,0]-mn[0])*scale;pt[:,:,1]=tile.height-8-(proj[:,:,1]-mn[1])*scale
        normals=np.cross(tri[idx,1]-tri[idx,0],tri[idx,2]-tri[idx,0]);normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-9)
        light=np.array([-.3,-.58,.76]);shade=.74+.25*np.maximum(0,normals@light)
        colors={}
        for mi,name in enumerate(scene.materials):
            if name=='Postal courtyard | pale lime render':rgb=[216,214,204]
            elif name=='Postal courtyard | sand-faced stone':rgb=[163,158,145]
            else:rgb=[round(255*sr(float(v))) for v in appearance.get(name,{}).get('baseColorFactor',[.52,.52,.48])[:3]]
            colors[mi]=np.array(rgb)
        for n in np.argsort((tri[idx]@depth).mean(axis=1))[::-1]:
            p=pt[n].round().astype(int);q.polygon([tuple(v)for v in p],fill=tuple(np.clip(colors[int(scene.mi[idx[n]])]*shade[n],0,255).astype(int)))
        im.paste(tile,(left,top));d.rectangle((left,top,right,bot),outline='#9fac9d')
    tx((42,128),'西立面',23,True);tx((790,128),'南端墙',23,True)
    mesh((40,171,775,488),'west');mesh((788,171,1230,488),'south')
    tx((41,495),'北侧上层按各期可辨视野截取。下层窗台局部被绿篱遮挡。',16)
    tx((789,495),'低层止于首个窗轴，上部可见三列窗。',16)
    d.line((40,549,1230,549),fill='#a9b4a8');tx((41,568),'照片定位与底图轮廓',23,True)
    tx((41,610),'图中街面与底图沿街方向的偏差',16)
    x=lambda v:55+(v+30)*14.5;y=lambda v:762-v*7.3
    pts=[(-24.54,-1.48),(6.85,-1.48),(6.65,14.35),(-24.26,14.17)]
    d.polygon([(x(u),y(v))for u,v in pts],fill='#dce1d5',outline='#7f8a78')
    d.line([(x(-27.72),y(0)),(x(2.65),y(0)),(x(2.65),y(13.2))],fill='#a95642',width=5)
    for u in [-.703,.703]:d.ellipse((x(u)-3,y(0)-3,x(u)+3,y(0)+3),fill='#174f49')
    tx((59,785),'灰  原 2429 底图轮廓       砖红  照片定位的立面与回墙',15)
    tx((645,568),'南角屋顶',23,True)
    for i,(n,z)in enumerate([('转角方台顶','19.05 m'),('常规女儿墙上缘','18.26–18.52 m'),('通常挑檐外鼻','约 17.78 m')]):
        yy=619+42*i;d.line((650,yy+17,693,yy+17),fill=['#935c46','#6c7f72','#909c91'][i],width=4);tx((706,yy),n,17);tx((949,yy-2),z,19,True)
    s=cal['summary'];tx((645,776),f"西面 {s['stations']} 个机位 / {s['landmarks']} 个同名点 / {s['observations']} 次观测",16)
    tx((42,821),'自制模型投影与位置示意。高度以街面为基准，单位为米。',13,color='#5e706a')
    output.parent.mkdir(parents=True,exist_ok=True);im.save(output,quality=89,subsampling=0)
    return dict(mesh_sha256=sha256(path.read_bytes()).hexdigest(),output_sha256=sha256(output.read_bytes()).hexdigest(),western_apertures=len(openings),southern_apertures=len(layout['south_windows']),photographs_embedded=False)
if __name__=='__main__':
    ap=ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();print(json.dumps(print_board(a.mesh,a.output)))
