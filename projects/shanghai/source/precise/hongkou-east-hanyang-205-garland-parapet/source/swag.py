"""Model the floral swag of the right rooftop panel at 205 East Hanyang Road."""
from math import sin,cos,pi,sqrt
from pathlib import Path
from PIL import Image
from shapely.geometry import box
import numpy as np
ID='hongkou-east-hanyang-205-garland-parapet'
GROUND='Limestone-toned plaster';MOULD='Coping and string moulds';PANEL='Shallow frame strips';FOL='Foliage on the garland';FRUIT='Rounded blooms';TAPE='Twisted ribbon relief'
PALETTE={n:dict(color=c,roughness=.90)for n,c in [(GROUND,[1,1,1]),(MOULD,[.736,.63,.443]),(PANEL,[.64,.58,.432]),(FOL,[.725,.646,.455]),(FRUIT,[.779,.679,.472]),(TAPE,[.779,.704,.542])]}
def texture():
    p=Path(__file__).with_name('buff-plaster.png')
    if not p.exists():
        r=np.random.default_rng(647);v=r.normal(0,3.1,(120,240,1))
        Image.fromarray(np.clip(np.array([191,175,133])+v,0,255).astype('uint8')).save(p)
    PALETTE[GROUND]['texture']=str(p)
def base(x):return .365+.445*(x/.77)**2
def add_building(b,far=False):
    texture()
    def face(x0,x1,z0,z1,back,front,mat,label):
        b.prism(box(x0,z0,x1,z1),back,front,lambda x,z,d:(x,-d,z),mat,label)
    face(-1.32,1.32,.03,1.13,-.25,0,GROUND,'Flat field of the parapet cartouche')
    for x,z,h,d in [(1.37,.012,.071,.047),(1.36,.087,.035,.026),(1.357,1.078,.038,.035),(1.40,1.12,.065,.073)]:
        face(-x,x,z,z+h,-.20,d,MOULD,'Projecting mould at foot or coping')
    for sign in (-1,1):
        x=sign*1.14
        face(x-.11,x+.11,.19,1.06,0,.019,PANEL,'Upright at the side of the ornament')
        face(x-.065,x+.065,.21,.65,.019,.039,MOULD,'Long rectangular tongue on the flanking upright')
        for step in(-.038,.038):
            face(x+step-.009,x+step+.009,.713,.899,.018,.039,MOULD,'Paired short vertical strokes')
    def curved(pts,r,mat,label):
        b.tube([(x,-d,z)for x,z,d in pts],r,mat,sides=5 if far else 11,label=label)
    a=np.linspace(-.77,.77,23 if far else 59)
    curved([(x,base(x),.051)for x in a],.064,FOL,'Main curved support of the swag')
    def relief(cx,cz,rx,rz,depth,angle,mat,name):
        # A closed oval in low relief, tapered at the ends with a raised central ridge.
        angles=[2*pi*k/16 for k in (list(range(9))+[10,12,14] if far else range(16))]
        seg=len(angles);ring=8;verts=[];faces=[]
        for i in range(ring+1):
            t=pi*i/ring
            for j in range(seg):
                v=angles[j];u=rx*cos(t);vv=rz*sin(t)*cos(v)
                x=cx+u*cos(angle)-vv*sin(angle);z=cz+u*sin(angle)+vv*cos(angle)
                verts.append((x,-(.061+depth*sin(t)*sin(v)),z))
        for i in range(ring):
            for j in range(seg):
                p=i*seg+j;q=i*seg+(j+1)%seg
                faces.extend([(p,q+seg,q),(p,p+seg,q+seg)])
        b.add(verts,faces,mat,name)
    for i,x in enumerate(np.linspace(-.72,.72,20)):
        for side in (-1,1):
            dx=side*.019
            relief(x+dx,base(x)+side*.046,.063,.034,.051,(.47 if side>0 else -.36)+(x/.77)*.685,FOL,'Leaf pointing along the catenary')
        if i%2==0:relief(x,base(x)+.023,.044,.041,.072,.12,FRUIT,'Alternate rounded floral bosses')
    # Small bosses sit in pockets between the larger leaves, with denser foliage in the belly.
    for j,x in enumerate(np.linspace(-.61,.59,15)):
        z=base(x)+.049+.010*cos(j*2.4)
        relief(x+.018*sin(j*2.1),z,.034,.031,.085,.35,FRUIT,'Cluster of small raised buds along the upper edge')
        if j%2:
            relief(x+.022,base(x)-.029,.053,.028,.084,.93+1.3*x,FOL,'Overlapping diagonal leaf on the garland face')
    for side in (-1,1):
        cx=side*.77
        relief(cx,.848,.059,.046,.065,.48,FRUIT,'Ribbon knot')
        curves=[[(0,.84),(.029,.934),(.146,.96),(.162,.911),(.116,.870),(.063,.897)],[(0,.831),(.107,.764),(.217,.777),(.251,.826)],[(.05,.797),(.158,.714),(.188,.656),(.149,.609),(.131,.559),(.153,.506),(.202,.492)]]
        for c in curves:
            # A smooth returning ribbon is flattened across its width at the front.
            path=np.array(c);smooth=[]
            for j in range(len(path)-1):
                a=path[max(0,j-1)];bb=path[j];cc=path[j+1];d=path[min(len(path)-1,j+2)]
                for t in np.linspace(0,1,4 if far else 8,endpoint=False):
                    smooth.append(.5*((2*bb)+(-a+cc)*t+(2*a-5*bb+4*cc-d)*t*t+(-a+3*bb-3*cc+d)*t*t*t))
            smooth.append(path[-1]);verts=[];indices=[]
            for j,(x,z) in enumerate(smooth):
                tangent=smooth[min(j+1,len(smooth)-1)]-smooth[max(0,j-1)]
                normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
                width=.018+.010*sin(pi*j/(len(smooth)-1));lift=.073+.021*sin(2*pi*j/(len(smooth)-1))
                for offset,depth in [(-width,lift),(0,lift+.012),(width,lift),(.8*width,lift-.010),(-.80*width,lift-.010)]:
                    verts.append((cx+side*(x+normal[0]*offset),-depth,z+normal[1]*offset))
                if j:
                    for c0 in range(5):
                        a0=(j-1)*5+c0;b0=(j-1)*5+(c0+1)%5
                        indices.extend([(a0,b0,b0+5),(a0,b0+5,a0+5)])
            if side>0:indices=[(a,c,b)for a,b,c in indices]
            b.add(verts,indices,TAPE,'Folded ribbon with a curved returning end')
    # The original left ribbon has a second small leafy drop.
    for j in range(4):
        x=-.765-.023*j;z=.722-.088*j
        relief(x,z,.059,.035,.053,-1.25,FOL,'Short foliage drop beside left knot')
    for p in b.parts:
        if p['material']==GROUND:p['texcoords']=[[(x+1.32)/2.64,(z-.03)/1.10]for x,y,z in p['vertices']]
