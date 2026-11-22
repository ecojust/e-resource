"""A cutaway of a single three-flight circuit of the Liangyou Apartments stair."""
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from PIL import Image
ID='xuhui-liangyou-angular-three-flight-stair'
MOSAIC='Grey green square mosaic';STONE='Pale terrazzo nosing';BASE='Ivory concrete fascia';STEEL='Black painted metal';WOOD='Red polished handrail'
PALETTE={k:dict(color=c,roughness=r)for k,c,r in [(MOSAIC,[1.,1.,1.],.85),(STONE,[.45,.45,.41],.84),(BASE,[.76,.74,.67],.93),(STEEL,[.12,.13,.12],.62),(WOOD,[.49,.16,.13],.47)]}
INNER=np.array([[-.68,-1.02],[.50,-1.02],[.73,-.57],[.18,1.02],[-.22,1.12],[-.71,.58],[-.91,-.54],[-.68,-1.02]])
def offset_polygon():
    line=Polygon(INNER[:-1]);expanded=np.array(line.buffer(.91,join_style=2).exterior.coords[:-1])
    points=[]
    for i,p in enumerate(INNER[:-1]):
        a=p-INNER[(i-1)%(len(INNER)-1)];c=INNER[i+1]-p
        n=sum(np.array([v[1],-v[0]])/np.linalg.norm(v)for v in [a,c])
        points.append(min(expanded,key=lambda v:np.linalg.norm(v-(p+.91*n/np.linalg.norm(n)))))
    return np.array(points+[points[0]])
OUTER=offset_polygon()
def course():
    z=.25
    for i,risers in enumerate([0,2,7,0,3,6,2]):
        n=max(1,risers);a,b=INNER[i:i+2];c,d=OUTER[i:i+2]
        for j in range(n):
            lo=z+.156*risers*j/n;hi=z+.156*risers*(j+1)/n
            yield a+(b-a)*j/n,c+(d-c)*j/n,a+(b-a)*(j+1)/n,c+(d-c)*(j+1)/n,lo,hi
        z+=risers*.156
def texture():
    f=Path(__file__).with_name('green-grey-mosaic.png')
    if not f.exists():
        y,x=np.indices((384,384));rnd=np.random.default_rng(743)
        val=np.array([111,120,110])+rnd.normal(0,6,(25,25))[y//16,x//16,None]+rnd.normal(0,2,x.shape)[:,:,None]
        val[(x%16==0)|(y%16==0)]=[108,104,94]
        Image.fromarray(np.clip(val,0,255).astype('uint8')).quantize(116).save(f)
    PALETTE[MOSAIC]['texture']=str(f)
def add_building(b,far=False):
    texture()
    def rail(a,c,r,material,round_,label):
        a=np.array(a);c=np.array(c);axis=c-a;axis/=np.linalg.norm(axis)
        ref=[0,0,1]if abs(axis[2])<.9 else[1,0,0]
        u=np.cross(axis,ref);u/=np.linalg.norm(u);v=np.cross(axis,u)
        n=(6 if far else 16)if round_ else 4
        circ=np.array([r*(u*np.cos(t)+v*np.sin(t)*(.78 if round_ else 1.))for t in np.arange(n)*2*np.pi/n])
        verts=np.concatenate([a+circ,c+circ]);faces=[]
        for i in range(n):
            j=(i+1)%n;faces.extend([(i,j,n+j),(i,n+j,n+i)])
        faces.extend((0,i+1,i)for i in range(1,n-1));faces.extend((n,n+i,n+i+1)for i in range(1,n-1));b.add(verts,faces,material,label)
    for a,c,b1,d,z0,z1 in course():
        corners=[a,c,d,b1]
        bottom=np.array([[*v,h-.185]for v,h in zip(corners,[z0,z0,z1,z1])]);top=np.array([[*v,z0]for v in corners])
        faces=[(0,2,1),(0,3,2),(4,5,6),(4,6,7)]
        for i,j in [(0,1),(1,2),(2,3),(3,0)]:faces.extend([(i,j+4,i+4),(i,j,j+4)])
        b.add(np.concatenate([bottom,top]),faces,BASE,'Sloping concrete stair waist')
        b.plan_prism(Polygon(corners),z0-.012,z0+.012,MOSAIC,'Square mosaic stair tread and landing')
        b.plan_prism(Polygon([a,c,c+.073*(d-c),a+.073*(b1-a)]),z0+.012,z0+.02,STONE,'Pale nosing strip')
        rail([*a,z0+.89],[*b1,z1+.89],.038,WOOD,True,'Continuous polished wood handrail')
        for k in [.15,.71]:rail([*a,z0+k],[*b1,z1+k],.013,STEEL,False,'Horizontal steel balustrade member')
        n=max(1,int(np.ceil(np.linalg.norm(b1-a)/.16)))
        for t in (np.arange(n)+.08)/n:
            v=a+t*(b1-a);rise=z0+t*(z1-z0);rail([*v,z0+.02],[*v,rise+.875],.012,STEEL,False,'Upright steel baluster')
    for part in b.parts:
        if part['material']==MOSAIC:part['texcoords']=[[(x+2.3)/.88,(y+2.2)/.88]for x,y,z in part['vertices']]
