"""Swept flat ironwork on the shallow bowed balcony, including the photographed centre scrolls."""
from pathlib import Path
import json
import numpy as np
from scipy.interpolate import PchipInterpolator
from geometry_reference import surface,frontage

IRON='Black painted railing'
WORN='Weathered iron edge'
TIP='Worn dark finial'
X,SHAPE=frontage()
def at(x,z,setback=.09):
    a=np.atleast_1d(np.array(x,float))
    return np.column_stack([a,SHAPE(a)+setback,np.broadcast_to(z,a.shape)])
def ribbon(b,points,width,depth,mat,label):
    pts=np.array(points,float)
    pts=pts[np.r_[True,np.linalg.norm(np.diff(pts,axis=0),axis=1)>1e-7]]
    tang=np.gradient(pts,axis=0);tang/=np.linalg.norm(tang,axis=1)[:,None]
    across=np.cross(tang,np.array([0.,-1.,0.]));across/=np.linalg.norm(across,axis=1)[:,None]
    normal=np.cross(across,tang)
    verts=np.stack([pts+sw*width*.5*across+sd*depth*.5*normal for sw,sd in [(1,1),(-1,1),(-1,-1),(1,-1)]],axis=1).reshape(-1,3)
    faces=[(3,2,1,0)]
    for j in range(len(pts)-1):
        k=4*j
        for i in range(4):
            n=(i+1)%4;faces.append((k+i,k+n,k+n+4,k+i+4))
    j=4*(len(pts)-1);faces.append((j,j+1,j+2,j+3))
    b.add(verts,faces,mat,label)
def cropped(points):return np.asarray(points)/2+[395,165]
top=np.array([[138,273],[181,251],[232,226],[279,207],[305,192],[345,177],[406,152],[451,135],[509,114],[559,96],[593,86]])
low=np.array([[94,404],[151,382],[210,363],[267,341],[287,333],[351,304],[403,290],[456,277],[517,264],[578,245],[622,232]])
def guide(points):
    a=surface(cropped(points));return PchipInterpolator(a[:,0],a[:,2])
TOP,BOTTOM=guide(top),guide(low)
def limits(x):
    t=np.clip(x,-1.64,2.00);l=np.clip(x,-2.10,2.03)
    return float(BOTTOM(l)),float(TOP(t))
def observed(points,offset=.09):
    return surface(np.array([525,246])+np.asarray(points)/5.002,offset)
def bezier(points,n):
    a,b,c,d=np.asarray(points,float);t=np.linspace(0,1,n)[:,None]
    return (1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d
def draw_guard(b,lod):
    # The insert interrupts both rails. Their ends meet its side stiles.
    for span,(begin,end)in enumerate([(-2.61,.018),(.295,2.91)]):
        xs=np.linspace(begin,end,17 if lod else 47)
        floor=np.array([limits(x)[0]for x in xs]);cap=np.array([limits(x)[1]for x in xs])
        ribbon(b,at(xs,cap),.029,.029,IRON,'Bow guard/top rail span '+str(span+1))
        ribbon(b,at(xs,floor),.029,.027,IRON,'Bow guard/bottom rail span '+str(span+1))
    # Uprights and low foot blocks are placed individually from the reference.
    measured=cropped([[94,401],[127,392],[158,381],[181,374],[211,363],[232,355],[264,342],
                      [280,336],[307,326],[348,309],[368,300],[447,281],[515,265],[568,249],[622,231],[675,214]])
    upr=surface(measured)[:,0].tolist()+[-2.55,2.70,2.88]
    for i,x in enumerate(upr):
        if -.085<x<.34:continue
        lo,hi=limits(x)
        ribbon(b,at([x,x],[lo-.008,hi+.009]),.018 if i%4 else .025,.019,IRON,'Bow guard/individual upright %02d'%(i+1))
        if i%3==0:ribbon(b,at([x,x],[-.129,lo]),.031,.032,IRON,'Bow guard/paving foot %02d'%(i+1))
    # Each zigzag is on a fine outer vertical with four angular bends and a small pointed foot.
    for i,(u,v)in enumerate([(158,375),(231,351),(447,277),(578,245)]):
        x=surface(cropped([[u,v]]))[0,0];lo,hi=limits(x);h=hi-lo
        seq=[(x,hi-.012)]
        for j,t in enumerate([.86,.72,.58,.45,.31,.17]):seq.append((x+(.042 if j%2 else -.037),lo+h*t))
        seq.append((x,lo+.016));ribbon(b,at(*np.array(seq).T),.014,.013,IRON,'Bow guard/zigzag %02d'%(i+1))
        z=lo+.009
        poly=[(x,z-.041),(x-.026,z),(x,z+.044),(x+.026,z)]
        q=at(*np.array(poly).T);verts=np.vstack([q+[0,-.009,0],q+[0,.009,0]])
        b.add(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],TIP,'Bow guard/zigzag foot')
    def trace(points,w,label,setback=.072):ribbon(b,observed(points,setback),w,.011,IRON,'Central grille/'+label)
    # The rectangular panel is visibly wider across its foot than across its crown in the perspective image.
    trace([[107,50],[190,18],[227,364],[128,400],[107,50]],.024,'rectangular frame')
    for i,path in enumerate([[[110,104],[151,71],[175,39]],[[120,242],[162,206],[177,161]],[[130,367],[166,327],[183,282]]]):
        trace(path,.014,'diagonal sprig %d'%(i+1))
        p=np.asarray(path);j=p[1];trace([j,j+[9,-11],j+[12,-25]],.009,'small sprig leaf %d'%(i+1))
    for i,path in enumerate([[[112,117],[204,142]],[[120,258],[220,280]]]):trace(path,.011,'transverse tie %d'%(i+1))
    # The left and right scrolls are traced from the crop in the supplied measurements.
    left_top=[[[49,138],[40,99],[70,71],[91,83]],[[91,83],[117,98],[103,138],[86,145]],[[86,145],[68,149],[72,123],[82,117]]]
    left_bottom=[[[89,329],[101,307],[126,326],[122,347]],[[122,347],[116,372],[85,373],[79,357]],[[79,357],[75,344],[89,338],[93,347]]]
    right_top=[[[226,79],[214,57],[228,30],[246,30]],[[246,30],[267,30],[270,49],[262,66]],[[262,66],[248,87],[238,71],[246,58]]]
    right_bottom=[[[240,315],[243,290],[257,270],[274,271]],[[274,271],[298,270],[299,303],[287,318]],[[287,318],[275,332],[260,314],[269,304]]]
    for i,paths in enumerate([left_top,left_bottom,right_top,right_bottom]):
        chain=np.vstack([bezier(a,6 if lod else 15)[:-1] for a in paths]+[np.array(paths[-1][-1])[None,:]])
        trace(chain,.015,'curled end %d'%(i+1),.066)
    trace([[48,136],[50,196],[55,265],[65,330],[77,356]],.013,'left scroll spine',.066)

    trace([[194,28],[219,23],[239,34]],.013,'upper right welded return',.066)
    trace([[246,32],[262,78],[268,149],[273,217],[278,272]],.012,'right scroll spine',.066)
    trace([[224,348],[239,338],[247,305]],.013,'lower right welded return',.066)
    trace([[77,356],[77,342],[89,329]],.012,'lower left curled return',.066)
