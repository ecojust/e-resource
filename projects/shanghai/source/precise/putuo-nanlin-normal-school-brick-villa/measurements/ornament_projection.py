"""Compare attributed photo crops with geometry read from an exported GLB."""
import argparse
from pathlib import Path
import sys
import runpy
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageOps

def unchart(points,f):
    x,z=points[:,0],points[:,2]
    ref=f.PITCH_AT_ZERO+f.PITCH_SLOPE*f.ORIGIN_U
    pitch=ref*np.exp(x*f.PITCH_SLOPE/(f.MID_COURSE_M*f.OBLIQUE_FACTOR))
    ub=(pitch-f.PITCH_AT_ZERO)/f.PITCH_SLOPE
    v=np.polyval(f.BELT,ub)-(z-f.REFERENCE_BELT_Z)*pitch/f.MID_COURSE_M
    u=ub.copy()
    for _ in range(6):
        u=ub+(u-1072.)*(v-np.polyval(f.BELT,u))/33000.
    return np.stack([u,v],axis=1)

def projection(scene,f,o):
    image=Image.new('RGB',(2144,1424),(228,225,217));drawing=ImageDraw.Draw(image)
    zbuffer=Image.new('F',(2144,1424),1000.);zpen=ImageDraw.Draw(zbuffer)
    vertex=scene.tri.reshape((-1,3))
    eye=o.balcony_eye(f.metric);flat=vertex.copy();
    balcony_points=(vertex[:,1]<-.32);q=vertex[balcony_points]; flat[balcony_points]=eye+(q-eye)*(-eye[1]/(q[:,1]-eye[1]))[:,None]
    coords=unchart(flat,f).reshape((-1,3,2)); depth=scene.tri[:,:,1].mean(axis=1)
    normals=scene.cross/np.maximum(np.linalg.norm(scene.cross,axis=1)[:,None],1e-12)
    light=np.array([-.32,-.78,.53]); light/=np.linalg.norm(light)
    tone=np.clip(.59+.41*np.maximum(normals@light,0),0,1)
    palette={**f.PALETTE,**o.PALETTE}
    colors=[]
    for name in scene.materials:
        if name==f.GRAY:c=(93,93,93)
        elif name==f.RED:c=(151,84,61)
        else:
            mat=palette.get(name,{'color':[.40,.366,.32]})
            c=np.clip(np.power(mat.get('color',[.40,.366,.32])[:3],1/2.2)*255,0,255)
        colors.append(c)
    colors=np.array(colors)
    for i in np.argsort(-depth,kind='stable'):
        if normals[i,1]>=-.00005:continue
        c=tuple((colors[scene.mi[i]]*tone[i]).astype('uint8'))
        poly=[tuple(p)for p in coords[i]]
        drawing.polygon(poly,fill=c);zpen.polygon(poly,fill=float(depth[i]))
    # Project short shadows of actual foreground edges onto the subsequent
    # measured face. Arched caps, pierced piers and raised carving cast shadows
    # at different lengths according to their separation from the next face.
    zd=np.array(zbuffer);weight=np.zeros_like(zd);valid=zd<900.
    for d in (1,2,3,4,6,8,10,13):
        prev=np.roll(zd,(d,d),axis=(0,1));occluded=valid&(prev<zd-.0039*d)
        weight=np.maximum(weight,occluded*(.36-.015*d))
    rgb=np.asarray(image,dtype=float)*(1-weight[:,:,None])
    return Image.fromarray(np.uint8(rgb))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path);parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--project',type=Path,default=Path.cwd());args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).absolute().parent.parent/'source'));import fabric as f;import nanlin_ornaments as o
    sc=runpy.run_path(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py')['SerialScene'](args.glb)
    photo=Image.open(args.photo);assert photo.size==(2144,1424)
    rendering=projection(sc,f,o);board=Image.new('RGB',(1380,1115),(248,246,240));d=ImageDraw.Draw(board)
    ff='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    font=lambda s: ImageFont.truetype(ff,s)
    d.text((34,19),'南林师范学校旧址 · 山花、瓶栏与木檐阳台',font=font(36),fill='#262722')
    d.text((34,78),'2016年4月10日原片局部',font=font(22),fill='#585548')
    d.text((703,78),'由交付网格投影到同一立面',font=font(22),fill='#585548')
    rows=[('左山花的玻璃窗与两端石托',(229,278,947,478),113,190),
          ('右山花的卷草石板和下横饰带',(1654,342,2077,542),348,173),
          ('两段石瓶栏与中间砖墩',(940,371,1458,495),566,137),
          ('铁柱、木弓、卷纹和竖向隔条',(436,495,894,772),746,239)]
    for txt,box,y,h in rows:
        for x,source in ((34,photo),(703,rendering)):
            part=source.crop(box);part.thumbnail((637,h),Image.Resampling.LANCZOS)
            board.paste(part,(x,y))
        d.text((34,y+h+3),txt,font=font(18),fill='#3f3d35')
    d.line((34,1027,1345,1027),fill='#979284',width=1)
    d.text((34,1041),'摄影 Fayhoo · Wikimedia Commons · CC BY-SA 3.0 · 原图经裁切与缩放。图板依同许可分享。',font=font(17),fill='#46463f')
    d.text((34,1072),'网格采用明暗着色以显示形状；右列隐去原片树叶。被遮挡的栏脚和左山花顶线按可见部分衔接。',font=font(16),fill='#58584f')
    args.output.parent.mkdir(parents=True,exist_ok=True);temp=args.output.with_suffix('.tmp');board.save(temp,'JPEG',quality=90,optimize=True);temp.replace(args.output)
if __name__=='__main__':main()
