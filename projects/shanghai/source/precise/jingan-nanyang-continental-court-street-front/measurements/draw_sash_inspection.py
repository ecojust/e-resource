"""Render four sets of editable glazing and fitted frames in the measured openings."""
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont

project=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
outdir=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else project.parents[2]/'data/audit/nanyang-continental-court-street-front-v1/sashes'
sys.path.insert(0,str(project/'source'))
from continental_window_sashes import add_sash, PALETTE
schedule=json.loads((project/'measurements/street-window-schedule.json').read_bytes())

class Collector:
    def __init__(self):self.parts=[]
    def add(self,vertices,faces,material,label):
        xyz=np.array(vertices)
        tris=np.array([(p[0],p[i],p[i+1]) for p in faces for i in range(1,len(p)-1)])
        self.parts.append(dict(tris=xyz[tris],material=material))

def tint(name):
    lin=np.array(PALETTE[name]['color'])
    return np.where(lin<=.0031308,12.92*lin,1.055*lin**(1/2.4)-.055)*255.

def normalize(v):return v/np.linalg.norm(v)

def image(bay,floor,view,width=490,height=232):
    sl=next(f for f in schedule['bays'][bay]['floors'] if f['floor']==floor)
    m=Collector()
    for i,(l,r) in enumerate(sl['openings_u_m']):
        kwargs={'strip_index':i} if sl['configuration']=='three-light' else {}
        add_sash(m,False,lambda u,d,z:(u,d,z),bay,floor,i,l,r,sl['sill_z'],sl['head_z'],sl['face_depth_m']+sl['sash_recess_m'],**kwargs)
    sight=normalize(np.array(view));right=normalize(np.cross(sight,(0,0,1)));up=np.cross(right,sight)
    basis=np.column_stack((right,-up,sight))
    projected=[p['tris']@basis for p in m.parts]
    bounds=np.concatenate([q.reshape(-1,3) for q in projected])
    lo=bounds.min(axis=0);hi=bounds.max(axis=0)
    scale=min((width-32)/(hi-lo)[0],(height-18)/(hi-lo)[1])
    color=np.full((height,width,3),(237,235,228),dtype=np.uint8);depth=np.full((height,width),np.inf)
    shift=np.array((width,height))*.5-scale*(lo+hi)[:2]*.5
    light=normalize(np.array((-.37,-.70,.61)))
    for src,points in zip(m.parts,projected):
        rgb=tint(src['material'])
        for p,physical in zip(points,src['tris']):
            norm=normalize(np.cross(physical[1]-physical[0],physical[2]-physical[0]))
            if np.dot(norm,sight)>0:continue
            xy=p[:,:2]*scale+shift
            (x0,y0),(x1,y1)=np.maximum(xy.min(axis=0).astype(int),0),np.minimum(np.ceil(xy.max(axis=0)).astype(int),(width-1,height-1))
            if x1<x0 or y1<y0:continue
            a,b,c=xy
            den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if abs(den)<1e-8:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];dx=xx+.5-a[0];dy=yy+.5-a[1]
            u=(dx*(c[1]-a[1])-dy*(c[0]-a[0]))/den
            v=((b[0]-a[0])*dy-(b[1]-a[1])*dx)/den
            zz=p[0,2]+u*(p[1,2]-p[0,2])+v*(p[2,2]-p[0,2])
            zd=depth[y0:y1+1,x0:x1+1]
            mask=(u>=0)&(v>=0)&(u+v<=1)&(zz<zd)
            zd[mask]=zz[mask]
            color[y0:y1+1,x0:x1+1][mask]=np.clip(rgb*(.73+.34*max(0,np.dot(norm,light))),0,255)
    return Image.fromarray(color)

def font(size,bold=False):
    name='DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'
    return ImageFont.truetype(name,size)
out=Image.new('RGB',(1008,590),(249,248,244));draw=ImageDraw.Draw(out)
samples=[(5,2,(0,1,-.015),'Central bay · second floor','Three sashes divided by two masonry mullions'),
         (7,3,(0,1,-.015),'Bay 7 · third floor','Four-by-four and two-by-four lower glazing'),
         (7,4,(-.34,1,-.08),'Bay 7 · fourth floor','Outward-opening lower leaves and top light'),
         (8,3,(-.50,1,-.14),'Bay 8 · third floor','Two top-hinged lights viewed from the street')]
for i,(bay,level,angle,title,caption) in enumerate(samples):
    x=8+500*(i%2);y=5+293*(i//2)
    draw.text((x+4,y+1),title,font=font(18,True),fill=(42,43,40))
    out.paste(image(bay,level,angle), (x,y+30))
    draw.text((x+4,y+265),caption,font=font(13),fill=(64,64,60))
outdir.mkdir(parents=True,exist_ok=True)
out.save(outdir/'four-street-window-types.jpg',quality=92,subsampling=0)
