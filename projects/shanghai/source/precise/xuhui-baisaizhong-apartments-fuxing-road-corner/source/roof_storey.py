"""The projecting terrace, set-back sixth storey and the shallow pitched roof above it."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box
from materials import STUCCO,PALE,BAND,IRON,FRAME,GLASS,ROOF,RIDGE,ZINC
from plan import wall,segment
HERE=Path(__file__).resolve().parent
Q=json.loads((HERE.parent/'measurements/corner-camera-and-levels.json').read_bytes())
M=np.linalg.inv(np.asarray(Q['cameras']['commons2015']['P'])[:,:3])
EYE=-M@np.asarray(Q['cameras']['commons2015']['P'])[:,3]
# The eave and terrace front are reconstructed from the two frontal photographs.
# The rear outline follows the surveyed site. It has a lower return at the stair.
TERRACE=[(-4.75,-.50),(4.80,-.50),(9.28,5.96),(3.47,13.64),(-2.75,11.00),(-8.99,7.12)]
UPSTAIRS=[(-4.02,.73),(4.05,.73),(7.24,5.48),(3.05,11.79),(-2.58,9.87),(-7.48,6.74)]
EAVES=[(-4.50,.035),(4.63,.035),(7.87,5.60),(3.22,12.32),(-2.57,10.46),(-8.01,6.79)]
DECK=16.55
def front_uv(u,v,depth):
    r=M@np.array([u,v,1.])
    return EYE+r*((depth-EYE[1])/r[1])
def shell_panel(b,points,mat,name):
    pts=np.asarray(points,float)
    if np.cross(pts[1]-pts[0],pts[2]-pts[0])[2]<0:pts=pts[::-1]
    n=len(pts)
    vertices=np.vstack([pts,pts-[0,0,.105]])
    faces=[]
    for i in range(1,n-1):faces+=[(0,i,i+1),(n,n+i+1,n+i)]
    for i in range(n):
        j=(i+1)%n;faces.append((i,i+n,j+n,j))
    b.add(vertices,faces,mat,name)
def add_terrace(b,lod):
    poly=Polygon(TERRACE)
    # Leave the structural floor hole at the stair head open.
    from plan import STAIR
    b.plan_prism(poly.difference(STAIR.buffer(.03,join_style=2)),16.40,16.55,PALE,'large overhanging terrace slab')
    for i,(p,q) in enumerate(zip(TERRACE,TERRACE[1:]+TERRACE[:1])):
        p,q=np.asarray(p),np.asarray(q);ds=q-p
        if i not in [0,1,5]:continue
        length=np.linalg.norm(ds);u=ds/length
        n=np.array([u[1],-u[0]])
        segment(b,p,q,DECK,17.24,-.175,-.018,STUCCO,'terrace solid parapet')
        # The flat iron rails above the parapet are particularly clear in 2015.
        foot=-.09*n
        for height in [17.28,17.39,17.52,17.66,17.84]:
            b.tube([(*list(p+foot),height),(*list(q+foot),height)],.014,IRON,6 if lod else 9,'terrace horizontal steel rail')
        count=max(1,round(length/1.05))
        for k in range(count+1):
            pos=p+ds*k/count+foot
            b.tube([(*pos,17.22),(*pos,17.85)],.018,IRON,6 if lod else 8,'terrace steel post')

def front_sash(b,a,c,u0,z0,u1,z1,cols,rows,label):
    def rect(x,y,r,t,inside,outer,mat,suffix):
        wall(b,a,c,box(x,y,r,t),inside,outer,mat,label+' '+suffix)
    rim=.047
    for x in np.linspace(u0,u1,cols+1):
        rect(x-rim/2,z0,x+rim/2,z1,-.104,-.034,FRAME,'steel upright')
    for z in np.linspace(z0,z1,rows+1):
        rect(u0,z-rim/2,u1,z+rim/2,-.104,-.033,FRAME,'steel crossbar')
    for i in range(cols):
        x=u0+(u1-u0)*i/cols;nx=u0+(u1-u0)*(i+1)/cols
        for j in range(rows):
            z=z0+(z1-z0)*j/rows;nz=z0+(z1-z0)*(j+1)/rows
            rect(x+rim/2,z+rim/2,nx-rim/2,nz-rim/2,-.123,-.112,GLASS,'pane')

def add_penthouse(b,lod):
    a,c=map(np.asarray,UPSTAIRS[:2]);depth=a[1]
    face=box(0,DECK,np.linalg.norm(c-a),19.70)
    lights=[('left terrace light',(439,463,473,532),1,2),('centre upper sash',(577,493,814,547),7,3),('right terrace light',(932,470,958,534),1,2)]
    for name,(u,v,uu,vv),cols,rows in lights:
        p=front_uv(u,v,depth);q=front_uv(uu,vv,depth)
        x0,x1=p[0]-a[0],q[0]-a[0];z0,z1=q[2],p[2]
        face=face.difference(box(x0,z0,x1,z1))
        front_sash(b,a,c,x0,z0,x1,z1,cols,rows,name)
        if cols==1:
            surround=box(x0-.11,z0-.16,x1+.11,z1+.18).difference(box(x0,z0,x1,z1))
            wall(b,a,c,surround,.01,.118,PALE,name+' rectangular head and surround')
    wall(b,a,c,face,-.21,0,STUCCO,'sixth-storey front with three actual apertures')
    # Three narrow flutes rise in each of the piers which frame the upper lights.
    for x in [.23,.29,.35,7.71,7.77,7.83]:
        wall(b,a,c,box(x,17.36,x+.021,19.64),.002,.027,BAND,'sixth-storey vertical fluting')
    for i in range(1,len(UPSTAIRS)):
        a,c=np.asarray(UPSTAIRS[i]),np.asarray(UPSTAIRS[(i+1)%len(UPSTAIRS)])
        L=np.linalg.norm(c-a)
        shell=box(0,DECK,L,19.70)
        if i in (1,5):
            fractions=[(.25,.51),(.65,.86)] if i==1 else [(.14,.37),(.51,.76)]
            for lo,hi in fractions:
                x0,x1=lo*L,hi*L;z0,z1=17.63,19.15
                shell=shell.difference(box(x0,z0,x1,z1))
                front_sash(b,a,c,x0,z0,x1,z1,2,2,'top-floor street side')
        wall(b,a,c,shell,-.17,0,STUCCO,'sixth-storey side and rear')
    # The low eaves screen the pitch from the foot of the street corner.
    # The staggered rear and central ridge follow the dark roof field in the dated aerials.
    soffit=Polygon(EAVES).buffer(-.018,join_style=2).difference(Polygon(UPSTAIRS).buffer(-.015,join_style=2))
    b.plan_prism(soffit,19.679,19.701,PALE,'continuous underside of top eaves')
    z_foot=19.70;z_tile=19.89
    for p,q in zip(EAVES,EAVES[1:]+EAVES[:1]):
        segment(b,np.array(p),np.array(q),z_foot,z_tile-.105,-.35,-.008,PALE,'top eave fascia')
    v=[list(pt)+[z_tile] for pt in EAVES]
    near=[.05,2.94,20.91];rear=[.64,8.57,21.12]
    for i,chosen in enumerate([[v[0],v[1],near],[v[1],v[2],rear,near],[v[2],v[3],rear],
                              [v[3],v[4],rear],[v[4],v[5],near,rear],[v[5],v[0],near]]):
        shell_panel(b,chosen,ROOF,'pressed tile roof pitch '+str(i+1))
    for tag,line in [('main ridge',[near,rear]),('front northwest hip',[near,v[0]]),('front southeast hip',[near,v[1]]),
                     ('rear east hip',[rear,v[3]]),('west roof fold',[rear,v[4]])]:
        b.tube(line,.052,RIDGE,7 if lod else 11,'roof '+tag)
def add_roof(b,lod):
    add_terrace(b,lod);add_penthouse(b,lod)
