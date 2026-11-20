"""Glazed auditorium roof, nine southern dormers and the two square pavilion roofs."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from photo_architecture import Facade

TILE='ochre glazed tile'
ROLL='gold ridge tiles'
PIGMENT='vermilion lacquer'
BLUE='blue green painted wood'
DARK='dark bronze sash'
GLASS='blue grey glazing'
STONE='cream limestone'
TIMBER='brown roof timbers'


def roof_patch(b,fn,label,lod,edge_tiles=True):
    cols,rows=(8,5) if lod else (18,9)
    vv=[fn(s,t) for t in np.linspace(0,1,rows+1)for s in np.linspace(-1,1,cols+1)]
    quads=[]
    for j in range(rows):
        for i in range(cols):
            a=j*(cols+1)+i
            q=[a,a+1,a+cols+2,a+cols+1]
            v0,v1,v2=np.array(vv)[q[:3]]
            if np.cross(v1-v0,v2-v0)[2]<0:q.reverse()
            quads.append(q)
    b.add(vv,quads,TILE,label+'/roof planes')
    if not lod:
        span=np.linalg.norm(np.subtract(fn(-1,1),fn(1,1)))
        n=max(2,round(span/.38))
        for i,s in enumerate(np.linspace(-1,1,n+1)):
            if not edge_tiles and i in (0,n):continue
            path=[np.asarray(fn(s,t))+[0,0,.035]for t in np.linspace(.015,1,8)]
            b.tube(path,.041,ROLL,5,label+'/rolled tiles')
    edge=[np.asarray(fn(s,1))+[0,0,.025] for s in np.linspace(-1,1,15)]
    b.tube(edge,.094,ROLL,8,label+'/eave tiles')


def main_z(t,s):
    return 15.92+3.86*(1-t)**1.55+.73*abs(s)**10*t**3


def main_roof(b,lod):
    center=-.95
    cy=-3.12
    outer=22.80; ridge=16.08; deep=10.39; br=.51
    for face in (-1,1):
        def surface(s,t):
            xmid=ridge+(outer-ridge)*max(0.,(t-br)/(1-br))
            return (center+s*xmid,cy+face*deep*t,main_z(t,s))
        roof_patch(b,surface,'Auditorium/long north pitch' if face>0 else 'Auditorium/south dormer pitch',lod)
    for end in (-1,1):
        def hip(s,t):
            d=br+(1-br)*t
            return(center+end*(ridge+(outer-ridge)*t),cy+s*deep*d,main_z(d,1.)-.73*(1-abs(s)**10)*d**3)
        roof_patch(b,hip,'Auditorium/end hip',lod,False)
        # End-gable lower edge lies at the hip's inner edge; upper edge follows the main curved slopes.
        f=Facade(b,(center+end*ridge,cy-end*deep*br),(center+end*ridge,cy+end*deep*br),'Auditorium/gable')
        lower=[(s*deep*br,hip(s,0)[2]) for s in np.linspace(-1,1,17)]
        top=[(s*deep*br,main_z(abs(s)*br,1.)) for s in np.linspace(1,-1,17)]
        f.prism(Polygon(lower+top).buffer(0),-.15,.0,PIGMENT,'gable panel')
        for z in (17.55,18.01):
            inside=Polygon(lower+top).buffer(0).intersection(box(-5.2,z-.05,5.2,z+.05))
            if inside.area>.001:f.prism(inside,0,.045,BLUE,'end gable beams')
        for face in (-1,1):
            b.tube([np.array(hip(face,t))+[0,0,.10]for t in np.linspace(0,1,11)],.10,ROLL,7,'Roof/sloping ridge')
        # Upturned ridge ends and lower ridge ornaments are interpreted only in silhouette.
        p=[(center+end*(ridge+t),cy,19.83+z) for t,z in [(-.7,0),(-.13,.10),(.18,.35),(.27,.62),(.13,.70)]]
        b.tube(p,.16,ROLL,7,'Roof/ridge end ornaments')
    b.tube([(center-ridge,cy,19.83),(center+ridge,cy,19.83)],.145,ROLL,9,'Roof/main ridge')
    for x in np.linspace(center-13.9,center+13.9,9):
        front=cy-6.62;back=cy-3.28
        # The photographed dormer's broad base meets the yellow roof; each forward opening has a deep reveal.
        zz=17.02; h=.90;w=1.61
        f=Facade(b,(x-w/2,front),(x+w/2,front),'Roof/south dormer')
        outline=Polygon([(-w/2,zz), (w/2,zz), (w/2,zz+h*.66),(0,zz+h+.27),(-w/2,zz+h*.66)])
        light=box(-.39,zz+.08,.39,zz+.70)
        f.prism(outline.difference(light),-.18,0,STONE,'dormer face')
        f.prism(light,-.15,-.11,GLASS,'dormer light')
        f.box(0,zz+.40,.04,.59,.055,-.074,DARK,'dormer mullion')
        for side in (-1,1):
            v=[(x,front-.15,zz+h+.33),(x+side*(w/2+.14),front-.15,zz+h*.68),(x+side*.28,back,18.39),(x,back,18.60)]
            if np.cross(np.subtract(v[1],v[0]),np.subtract(v[2],v[0]))[2]<0:v.reverse()
            b.add(v,[(0,1,2),(0,2,3)],TILE,'Roof/dormer hips')
            b.tube([v1 for v1 in [(x,front-.15,zz+h+.35),(x+side*(w/2+.14),front-.15,zz+h*.70)]],.048,ROLL,6,'Roof/dormer eaves')
            v=[(x+side*w/2,front,zz),(x+side*w/2,front,zz+h*.66),(x+side*.28,back,18.39),(x+side*.28,back,18.03)]
            if side<0:v.reverse()
            b.add(v,[(0,1,2),(0,2,3)],TIMBER,'Roof/dormer cheeks')


def pyramid(b,cx,cy,half,z,h,lod):
    for k in range(4):
        along=np.array([(1,0),(0,1),(-1,0),(0,-1)][k]);out=np.array([along[1],-along[0]])
        def facet(s,t):
            xy=np.array([cx,cy])+half*(out+s*along)*t
            return (*xy,z+h*(1-t)**1.35+.54*abs(s)**8*t**4)
        # At the apex a tiny square collar under the finial avoids degenerate faces.
        def top(s,t):return facet(s,.025+.975*t)
        roof_patch(b,top,'End pavilion/pyramidal roof',lod,False)
        b.tube([np.asarray(facet(1,t))+[0,0,.07]for t in np.linspace(.025,1,10)],.085,ROLL,7,'End pavilion/hip roll')
    b.lathe((cx,cy),[(z+h-.12,.22),(z+h,.29),(z+h+.18,.19),(z+h+.32,.13),(z+h+.54,.043)],ROLL,12,'End pavilion/apex finial')
