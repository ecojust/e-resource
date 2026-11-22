"""Plot the decoded garden-planter geometry and the measured plan beside the stair."""
from pathlib import Path
import argparse
import sys
import json
import numpy as np
from PIL import Image,ImageDraw
from balustrade_board import font
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import load_triangles
from garden_planters import PANEL,EARTH,PLASTER,STONE_EDGE,STONE,sections,plan_band


def project(p,facing):
    right,up,depth=facing
    return np.column_stack((p@right,-p@up,p@depth))


def view(image,tri,materials,rect,direction,filter_fn):
    direction=np.asarray(direction,dtype=float);direction/=np.linalg.norm(direction)
    right=np.cross([0,0,1.],direction);right/=np.linalg.norm(right)
    up=np.cross(direction,right)
    keep=filter_fn(tri.mean(axis=1))
    tris=tri[keep];mats=materials[keep]
    pts=project(tris.reshape(-1,3),(right,up,direction)).reshape(-1,3,3)
    w,h=rect[2]-rect[0],rect[3]-rect[1]
    lo=pts[:,:,:2].min(axis=(0,1));hi=pts[:,:,:2].max(axis=(0,1))
    scale=min((w-22)/(hi[0]-lo[0]),(h-18)/(hi[1]-lo[1]))
    uv=(pts[:,:,:2]-lo)*scale+((np.array([w,h])-(hi-lo)*scale)/2)
    normal=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
    normal/=np.maximum(np.linalg.norm(normal,axis=1),1.e-8)[:,None]
    light=.83+.21*np.clip(normal@[-.3,-.6,.72],-.5,1.)
    colors={PANEL:[91,96,102],EARTH:[109,88,62],PLASTER:[213,201,171],STONE:[199,190,172],
            STONE_EDGE:[114,117,119],'Zhu residence | rose and grey terrazzo':[164,142,137]}
    pixels=np.empty((h,w,3),dtype=np.uint8)
    pixels[:]=(77,88,89)
    depthbuffer=np.full((h,w),-np.inf)
    for i,coords in enumerate(uv):
        ix0,iy0=np.maximum(np.floor(coords.min(axis=0)).astype(int),0)
        ix1,iy1=np.minimum(np.ceil(coords.max(axis=0)).astype(int),[w-1,h-1])
        if ix1<ix0 or iy1<iy0:continue
        e1,e2=coords[1]-coords[0],coords[2]-coords[0]
        det=e1[0]*e2[1]-e1[1]*e2[0]
        if abs(det)<1e-8:continue
        yy,xx=np.ogrid[iy0:iy1+1,ix0:ix1+1]
        dx=xx+.5-coords[0,0];dy=yy+.5-coords[0,1]
        a=(dx*e2[1]-dy*e2[0])/det;b=(e1[0]*dy-e1[1]*dx)/det
        z=pts[i,:,2];interp=z[0]+a*(z[1]-z[0])+b*(z[2]-z[0])
        prior=depthbuffer[iy0:iy1+1,ix0:ix1+1]
        visible=(a>=0)&(b>=0)&(a+b<=1)&(interp>prior)
        prior[visible]=interp[visible]
        pixels[iy0:iy1+1,ix0:ix1+1][visible]=np.clip(light[i]*np.array(colors[mats[i]]),0,255)
    image.paste(Image.fromarray(pixels),rect[:2])


def draw(mesh,path):
    tri,ids,names,_=load_triangles(mesh)
    mats=np.array(names,dtype=object)[ids];centers=tri.mean(axis=1)
    valid=(centers[:,1]<-.29)&(centers[:,2]<.711)&np.isin(mats,
           [PANEL,EARTH,PLASTER,STONE,STONE_EDGE,'Zhu residence | rose and grey terrazzo'])
    tri=tri[valid];mats=mats[valid]
    im=Image.new('RGB',(1160,680),'#f5f1e9');d=ImageDraw.Draw(im)
    d.text((34,19),'南园弧阶两侧的花池',font=font(32,True),fill='#2f423f')
    d.text((36,72),'愚园路684号　两张2013年9月庭园照片可辨西、东两段浅色压顶及截角灰嵌板。',font=font(16),fill='#39504c')
    view(im,tri,mats,(34,111,1126,385),(-.14,-1.,.60),lambda p:np.ones(len(p),bool))
    d.text((38,393),'据解码模型绘制。西侧三面依次可数8、3、1格，东侧回角1格，长边7格，末格外缘有车遮挡。',font=font(17),fill='#354b46')
    view(im,tri,mats,(34,441,590,636),(-.30,-1.,.33),lambda p:(p[:,0]>4.34)&(p[:,0]<7.12)&(p[:,1]<-1.75))
    d.text((38,642),'灰嵌板、浅凹边及双层压顶',font=font(16),fill='#354b46')
    s=json.loads((HERE/'garden-planter-corners.json').read_bytes())
    rect=(616,441,1126,636);d.rectangle(rect,fill='#e4dfd1')
    def plan(xy):return [(int(622+x*28.0),int(521-y*28.0))for x,y in xy]
    for side in s['walls']:
        points,joins,lengths=sections(s,side)
        for a,b,c in ((.178,.498,'#92775b'),(-.031,.199,'#96948b')):
            band=plan_band(points,joins,a,b)
            d.polygon(plan(band.exterior.coords),fill=c)
        for x,y in plan(points):d.ellipse((x-3,y-3,x+3,y+3),fill='#485d58')
    d.text((626,454),'可见墙段平面',font=font(18,True),fill='#354b46')
    d.text((626,642),'两处收口取图08庭前地坪，压顶高约0.43米。',font=font(15),fill='#354b46')
    im.save(path,quality=88,optimize=True,subsampling=0)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path)
    ap.add_argument('image',type=Path);a=ap.parse_args();draw(a.mesh,a.image)
