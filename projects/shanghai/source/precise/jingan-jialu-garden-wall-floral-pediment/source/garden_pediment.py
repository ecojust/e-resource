"""Garden-wall acanthus and fruit urn, Beijing West Road, from Antigng's CC BY-SA photograph."""
from pathlib import Path
import base64,json,zlib
import numpy as np

def paint(rgb):
    def lin(v):return v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4
    return dict(color=[lin(v)for v in rgb],roughness=.87)

PALETTE={'stone ground':paint((152,146,138)),'weathered granite ledge':paint((128,123,119)),
         'light stone lip':paint((156,151,144)),'recessed gutter line':paint((109,105,101))}
for i in range(14):
    v=102+4*i
    PALETTE[f'cast-stone fleck tone {i:02}']=paint((v+5,v+2,v))
LEFT=29
RIGHT=698
OUTLINE=[(29,122),(68,122),(323,-35),(661,153),(695,153)]
INNER=[(30,155),(72,155),(323,23),(647,201),(692,202)]
def position(u,v,depth):
    return ((u-364)*.0045,depth,(410+(u-364)*.024-v)*.0045)
def sill(x):return 399+(x-30)*.026
def verge(u):
    for (x,y),(xx,yy) in zip(INNER,INNER[1:]):
        if u<=xx:return y+max(0,min(1,(u-x)/(xx-x)))*(yy-y)
    return INNER[-1][1]
def face(b,points,front,back,mat,label):
    n=len(points);v=[position(u,z,y)for y in (front,back)for u,z in points]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    for i in range(n):
        j=(i+1)%n;faces.append((i,n+i,n+j,j))
    b.add(v,faces,mat,label)
def ribbon(b,path,a,c,front,back,material,label):
    for i,(s,t) in enumerate(zip(path,path[1:])):
        p=[(s[0],s[1]+a),(s[0],s[1]+c),(t[0],t[1]+c),(t[0],t[1]+a)]
        face(b,p,front,back,material,f'{label} {i+1}')
def sample_data(lod):
    d=json.loads(Path(__file__).with_name('acanthus-surface.json').read_bytes())['samples']['far' if lod else 'near']
    dep=np.frombuffer(zlib.decompress(base64.b64decode(d['height_u16_le_01mm'])),dtype='<u2').reshape(d['shape'])*.0001
    tone=np.frombuffer(zlib.decompress(base64.b64decode(d['tone_u8'])),dtype='uint8').reshape(d['shape'])
    return dep,tone
def add_building(b,lod=False):
    # The non-convex verge is split at each return so both faces follow the photographed profile.
    for i,(a,c) in enumerate(zip(OUTLINE,OUTLINE[1:])):
        face(b,[a,(a[0],sill(a[0])+13),(c[0],sill(c[0])+13),c],.004,.226,'stone ground',f'stone panel backing {i+1}')
    for k,(s,t,front,back,mat) in enumerate([(0,5,-.119,.23,'light stone lip'),(5,13,-.104,.20,'weathered granite ledge'),(13,19,-.076,.16,'recessed gutter line'),(19,29,-.066,.15,'weathered granite ledge'),(29,34,-.043,.15,'light stone lip')]):
        ribbon(b,OUTLINE,s,t,front,back,mat,f'pediment upper return course {k+1}')
    for k,(s,t,front,back,mat) in enumerate([(0,6,-.045,.22,'light stone lip'),(6,13,-.073,.22,'weathered granite ledge'),(13,18,-.058,.22,'recessed gutter line'),(18,24,-.071,.22,'light stone lip'),(24,48,-.022,.21,'stone ground')]):
        ribbon(b,[(LEFT,sill(LEFT)),(RIGHT,sill(RIGHT))],s,t,front,back,mat,f'horizontal lower moulding {k+1}')
    depth,tone=sample_data(lod);nz,nx=depth.shape
    u=np.linspace(30,701,nx);vs=np.linspace(19,418,nz)
    for block in range(3):
        start=block*(nx-1)//3;end=(block+1)*(nx-1)//3
        groups={}
        for j in range(nz-1):
            for i in range(start,end):
                x=(u[i]+u[i+1])/2;v=(vs[j]+vs[j+1])/2
                if not 33<=x<=693 or not verge(x)<=v<=sill(x)+1:continue
                color=min(13,max(0,int((float(np.mean(tone[j:j+2,i:i+2]))-45)/5.7)))
                verts,faces,idx=groups.setdefault(color,([],[],{}));face_id=[]
                for r,c in [(j,i),(j+1,i),(j+1,i+1),(j,i+1)]:
                    key=(r,c)
                    if key not in idx:
                        idx[key]=len(verts);verts.append(position(u[c],vs[r],-.001-depth[r,c]))
                    face_id.append(idx[key])
                faces.append(tuple(face_id))
        for color,(verts,faces,_) in groups.items():
            b.add(verts,faces,f'cast-stone fleck tone {color:02}',f'acanthus and fruit urn zone {block+1} tone {color:02}')
